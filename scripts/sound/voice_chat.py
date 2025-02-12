import sys
import subprocess
import asyncio
from scripts.sound.VoiceMaker import VoiceMaker
from scripts.sound.play_sound import PlaySound
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.adapters.vtube_studio_adapter import VTSAdapter
from scripts.adapters.obs_adapter import OBSAdapter
from scripts.utils.helpers import split_japanese_text
from scripts.utils.parser import Parser
from scripts.sound.VoiceMaker import StyleBertVits2Adapter
from scripts.file_manager import FileManager, FilePath
from scripts.commands.action_manager import ActionManager, ActLeaveDiscordVoiceChat
from scripts.commands.queries import Queries
from scripts.memory.memory import ShortTermMemory
import re
import os
import logging

class VoiceChat:
    def __init__(self, adapter: OpenAIAdapter, vits2: StyleBertVits2Adapter, play_sound: PlaySound, 
                 action_manager: ActionManager, memory: ShortTermMemory, queries: Queries, 
                 obs: OBSAdapter, vts: VTSAdapter | None = None, nickname: str = "シン"):
        self.adapter = adapter
        # self.voice_maker = voice_maker
        self.vits2 = vits2 # 高速化のためにモデルを先にロードする（voice_makerの代わりに）
        self.play_sound = play_sound
        self.process = None
        self.terminated = False  # Flag to track termination
        self.vts = vts
        self.action_manager = action_manager
        self.memory = memory
        self.queries = queries
        self.voice_chat_prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_VOICE_CHAT)
        self.obs = obs
        self.nickname = nickname # TODO: 二人以上の会話を対応させる

    def __run_asr(self):
        return subprocess.Popen(
            [sys.executable, 'scripts/sound/asr.py', '--use_api', 'True'],
            # [sys.executable, 'scripts/sound/asr.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line-buffered output
            universal_newlines=True,  # Handle newlines cross-platform
            env=os.environ
        )

    async def __chat(self, transcription: str):
        await self.memory.add(transcription, 'user', narrate=False)
        # Reload prompt to get latest info
        self.voice_chat_prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_VOICE_CHAT)
        talk_history = self.memory.get_short_term_memory(20)
        message = [self.adapter.create_message("system", self.voice_chat_prompt),
                   *talk_history]
        response = self.adapter.chat_completions(message)
        await self.memory.add(response, role='assistant', narrate=False)
        return response

    async def end(self):
        if  self.process and not self.terminated:
            self.terminated = True  # Mark as terminated to avoid multiple calls
            self.process.terminate()  # Try to terminate the process
            await asyncio.to_thread(self.process.wait)  # Wait for the process to exit
            print("ボイスチャットのセッションが終了した。")

    async def __read_stdout(self):
        while True:
            line = await asyncio.to_thread(self.process.stdout.readline)  # Read one line asynchronously
            if line:  # If there's a line read
                line = line.strip()  # Clean up the line
                if line:  # Only yield non-empty lines
                    yield line  # Yield each line as it's read
            elif self.process.poll() is not None:  # End of process
                break


    async def start(self):
        if self.vts:
            await self.vts.connect_auth()
        self.process = self.__run_asr()
        logging.info("ボイスチャットのセッションが開始した。")

        # Debugging: Read stderr
        asyncio.create_task(self._log_stderr())

        try:
            async for output in self.__read_stdout():
                if 'ready' in output:
                    print("[ASRが準備完了した]")
                elif output:
                    output = f"[{self.nickname}]{output}" 
                    # 音声合成して会話をする
                    response = await self.__chat(output)
                    if 'none' in response:
                        await self.memory.add(f"(アイリが{self.nickname}を無視した)", role='assistant', narrate=False)
                    elif response is not None:
                        token, text_raw = self.parse_expression(response)
                        text_list = split_japanese_text(text_raw)
                        response_voice = self.vits2.get_voice(text_list.pop(0))
                        # response_voice = self.voice_maker.make_voice_fish_audio(text_list.pop(0))
                        if token and self.vts is not None:
                            for _, expression in self.vts.hotkeys.items():
                                if expression == token:
                                    await self.vts.trigger_hotkeys(expression)
                        self.play_sound.play_sound(response_voice)
                        for text in text_list:
                            response_voice = self.vits2.get_voice(text)
                            self.play_sound.play_sound(response_voice)
                        else:
                            text = response
                        if "!LEAVE_DISCORD" in text:
                            text = str(text).replace("!LEAVE_DISCORD", "").replace(" ", "")
                            leave = ActLeaveDiscordVoiceChat(self.action_manager.vlife)
                            if text != "":
                                await self.memory.add(text, role='assistant', narrate=False)
                            await leave.execute()
                            await leave.end()
                            break
                        await self.memory.add(text, role='assistant', narrate=False)
                        
        # except Exception as e:
        #     print("予期せぬエラーが発生した：", e)
        finally:
            if self.process:
                logging.debug(f"Subprocess exited with code: {self.process.returncode}")
            await self.end()

    async def _log_stderr(self):
        while True:
            if self.process.stderr:
                line = await asyncio.to_thread(self.process.stderr.readline)
                if line:
                    logging.error(f"[Subprocess Error]: {line.strip()}")
                elif self.process.poll() is not None:
                    break
    
    def parse_expression(self, input_text):
        input_text = Parser.remove_brackets(input_text)
        # Match the first occurrence of {token} anywhere in the text
        match = re.search(r"\{(\w+)\}", input_text)
        if match:
            token = match.group(1)  # Extract the token inside {}
            # Remove the token and the surrounding {} from the input text
            text = re.sub(r"\{\w+\}", "", input_text).strip()
            return token, text
        return None, input_text