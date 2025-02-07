import sys
import subprocess
from time import sleep
import signal
import asyncio
from scripts.sound.VoiceMaker import VoiceMaker
from scripts.sound.play_sound import PlaySound
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.adapters.vtube_studio_adapter import VTSAdapter
from scripts.utils.helpers import split_japanese_text
from scripts.sound.VoiceMaker import StyleBertVits2Adapter
from scripts.file_manager import FileManager, FilePath
from scripts.commands.action_manager import ActionManager, ActLeaveDiscordVoiceChat
from scripts.commands.queries import Queries
from scripts.memory.memory import ShortTermMemory
import re
import os
class VoiceChat:
    def __init__(self, adapter: OpenAIAdapter, vits2: StyleBertVits2Adapter, play_sound: PlaySound, action_manager: ActionManager, memory: ShortTermMemory, queries: Queries, vts: VTSAdapter | None = None):
        self.adapter = adapter
        # self.voice_maker = voice_maker
        self.vits2 = vits2 # 高速化のためにモデルを先にロードする（voice_makerの代わりに）
        self.play_sound = play_sound
        self.process = None
        self.talk_history: list[dict[str, str]] = []
        self.terminated = False  # Flag to track termination
        self.vts = vts
        self.action_manager = action_manager
        self.memory = memory
        self.talk_history.extend(self.memory.get_short_term_memory(20))
        self.queries = queries
        self.voice_chat_prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_VOICE_CHAT)

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
        self.voice_chat_prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_VOICE_CHAT)
        self.talk_history.append({"role": "user",
                                  "content": transcription})
        # 過去100やりとりまで参照する
        if len(self.talk_history) > 100:
            talk_history = self.talk_history[-100:]
        else:
            talk_history = self.talk_history
        message = [self.adapter.create_message("system", self.voice_chat_prompt),
                   *talk_history]
        response = self.adapter.chat_completions(message)
        self.talk_history.append({"role": "assistant",
                                  "content": response})
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
        print("ボイスチャットのセッションが開始した。")

        # Use asyncio's signal handling instead of the signal module
        # loop = asyncio.get_event_loop()
        # loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(self.end()))
        # loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(self.end()))

        # Debugging: Read stderr
        asyncio.create_task(self._log_stderr())

        try:
            async for output in self.__read_stdout():
                if 'ready' in output:
                    print("[ASRが準備完了した]")
                elif output:
                    print("[音声入力]:", output)
                    # 音声合成して会話をする
                    response = await self.__chat(output)
                    if 'none' in response:
                        print("[アイリがあなたのメッセージを無視した]")
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
                                print("[アイリ]:", text)
                            await leave.execute()
                            await leave.end()
                            break
                        print("[アイリ]:", text)
                        
        # except Exception as e:
        #     print("予期せぬエラーが発生した：", e)
        finally:
            if self.process:
                print(f"Subprocess exited with code: {self.process.returncode}")
            await self.end()

    async def _log_stderr(self):
        while True:
            if self.process.stderr:
                line = await asyncio.to_thread(self.process.stderr.readline)
                if line:
                    print(f"[Subprocess Error]: {line.strip()}")
                elif self.process.poll() is not None:
                    break
    
    def parse_expression(self, input_text):
        print("RAW TEXT:", input_text)
        # Match the first occurrence of {token} anywhere in the text
        match = re.search(r"\{(\w+)\}", input_text)
        if match:
            token = match.group(1)  # Extract the token inside {}
            # Remove the token and the surrounding {} from the input text
            text = re.sub(r"\{\w+\}", "", input_text).strip()
            print("TOKEN:", token)
            return token, text
        return None, input_text
    

if __name__ == "__main__":
    adapter = OpenAIAdapter()
    # voice_maker = VoiceMaker()
    play_sound = PlaySound()
    vts_adapter = VTSAdapter()
    # voice_realtime = VoiceChat(adapter, voice_maker, play_sound, vts_adapter)
    # asyncio.run(voice_realtime.start())