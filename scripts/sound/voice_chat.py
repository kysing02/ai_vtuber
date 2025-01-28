import sys
import re
import subprocess
from time import sleep
import signal
import asyncio
from scripts.sound.VoiceMaker import VoiceMaker
from scripts.sound.play_sound import PlaySound
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.adapters.vtube_studio_adapter import VTSAdapter
from scripts.reflection import Emotion
import os
class VoiceChat:
    def __init__(self, adapter: OpenAIAdapter, voice_maker: VoiceMaker, play_sound: PlaySound, vts: VTSAdapter | None = None):
        self.adapter = adapter
        self.voice_maker = voice_maker
        self.play_sound = play_sound
        self.process = None
        self.talk_history: list[dict[str, str]] = []
        with open("storage/airi/voice_chat.txt", "r", encoding="utf-8") as f:
            voice_chat_prompt = f.read()
        self.voice_chat_prompt = voice_chat_prompt
        self.terminated = False  # Flag to track termination
        self.vts = vts
    
    def __run_asr(self):
        return subprocess.Popen(
            [sys.executable, 'scripts/sound/asr.py', '--use_api', 'True'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line-buffered output
            universal_newlines=True,  # Handle newlines cross-platform
            env=os.environ
        )

    async def __chat(self, transcription: str):
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
         if self.process and not self.terminated:
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
        await self.vts.connect()
        await self.vts.authenticate()
        self.process = self.__run_asr()
        print("ボイスチャットのセッションが開始した。")
        signal.signal(signal.SIGINT, lambda signum, frame: asyncio.create_task(self.end()))
        signal.signal(signal.SIGTERM, lambda signum, frame: asyncio.create_task(self.end()))
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
                        token, text = Emotion.parse_expression(response)
                        response_voice = self.voice_maker.make_voice_style_bert_vits2(text)
                        if token and self.vts is not None:
                            for _, expression in self.vts.hotkeys.items():
                                if expression == token:
                                    print("expression triggered")
                                    await self.vts.trigger_hotkeys(expression)
                        else:
                            text = response
                        self.play_sound.play_sound(response_voice)
                        print("[アイリ]:", response)
                        
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

if __name__ == "__main__":
    adapter = OpenAIAdapter()
    voice_maker = VoiceMaker()
    play_sound = PlaySound()
    vts_adapter = VTSAdapter()
    voice_realtime = VoiceChat(adapter, voice_maker, play_sound, vts_adapter)
    asyncio.run(voice_realtime.start())