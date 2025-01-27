import subprocess
from scripts.adapters.openai_adapter import OpenAIAdapter
from time import sleep
import signal
from scripts.sound.VoiceMaker import VoiceMaker
from scripts.sound.play_sound import PlaySound

class VoiceChat:
    def __init__(self, adapter: OpenAIAdapter, voice_maker: VoiceMaker, play_sound: PlaySound):
        self.adapter = adapter
        self.voice_maker = voice_maker
        self.play_sound = play_sound
        self.process = None
        self.talk_history: list[dict[str, str]] = []
        with open("storage/airi/voice_chat.txt", "r", encoding="utf-8") as f:
            voice_chat_prompt = f.read()
        self.voice_chat_prompt = voice_chat_prompt
    
    def __run_asr(self):
        return subprocess.Popen(
            ['python', 'scripts/sound/asr.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def __chat(self, transcription: str):
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
    
    def end(self):
        self.process.terminate()
        self.process.wait()
        print("ボイスチャットのセッションが終了した。")

    def start(self):
        self.process = self.__run_asr()
        print("ボイスチャットのセッションが開始した。")
        signal.signal(signal.SIGINT, lambda signum, frame: self.end)  # Handle interrupt signal (Ctrl+C)
        signal.signal(signal.SIGTERM, lambda signum, frame: self.end)  # Handle terminate signal

        try:
            while True:
                # ASRのトランスクリプションを取得する
                output = self.process.stdout.readline()
                output = output.replace("\n", "").replace(" ", "")
                if 'ready' in output:
                    print("[ASRが準備完了した]")
                    continue
                if 'none' in output:
                    print("[アイリがあなたのメッセージを無視した]")
                    continue
                if output == '' and self.process.poll() is not None:
                    self.end()
                    break
                if output:
                    transcription = output.strip()
                    print("[音声入力]:", transcription)
                
                    # 音声合成して会話をする
                    response = self.__chat(transcription)
                    if response is not None:
                        response_voice = self.voice_maker.make_voice_style_bert_vits2(response)
                        self.play_sound.play_sound(response_voice)
                        print("[アイリ]:", response)
                sleep(0.5)
        except Exception as e:
            print("予期せぬエラーが発生した：", e)
        finally:
            self.end()

if __name__ == "__main__":
    adapter = OpenAIAdapter()
    voice_maker = VoiceMaker()
    play_sound = PlaySound()
    voice_realtime = VoiceChat(adapter, voice_maker, play_sound)
    voice_realtime.start()