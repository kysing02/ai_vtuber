import os
from usecases.talker import Talker
from obs_adapter import OBSAdapter
from VoiceMaker import VoiceIO, VoiceMaker
from youtube_comment_adapter import YoutubeCommentAdapter
from play_sound import PlaySound
from dotenv import load_dotenv
import time
load_dotenv(override=True)


class AITuberSystem_v2:
    def __init__(self):
        self.talker = Talker()
        self.obs_adapter = OBSAdapter()
        self.voice_maker = VoiceMaker()
        self.play_sound = PlaySound()

    def start(self):
        while True:
            comment = input()    
            character_speak = self.talker.chat(comment)
            speak_list = self.split_text(character_speak)
            print(speak_list)
            for speak in speak_list:
                voice: VoiceIO = self.voice_maker.make_voice_fish_audio(speak)
                self.obs_adapter.set_question(comment)
                self.obs_adapter.set_answer(speak)
                self.play_sound.play_sound(voice)
            time.sleep(0.1)
    
    def split_text(self, text: str) -> list[str]:
        # 。を区切りにしてリストにする
        text = text.replace("\n", "").split("。")
        if text[-1] == '':
            # 最後が空である場合は削除
            text.pop()
        return text

if __name__ == "__main__":
    aituber_system = AITuberSystem_v2()
    aituber_system.start()