import os
from scripts.usecases.talker import Talker
from scripts.adapters.obs_adapter import OBSAdapter
from scripts.adapters.youtube_comment_adapter import YoutubeCommentAdapter
from scripts.sound.VoiceMaker import VoiceIO, VoiceMaker
from scripts.sound.play_sound import PlaySound
from dotenv import load_dotenv
import time
load_dotenv(override=True)

# 注：このクラスはVLifeシステムに使用されていない。
# 参考書籍：「AITuberを作ってみたらプロンプトエンジニアリングがよくわかった件 - 阿部由延」
# TODO: ある程度VLifeシステムのストリーミング状況が整ったら、このクラスを`Narrator`クラスに移行する。
class AITuberSystem:
    def __init__(self):
        self.talker = Talker()
        self.obs_adapter = OBSAdapter()
        self.voice_maker = VoiceMaker()
        self.youtube_comment_adapter = YoutubeCommentAdapter(os.environ.get("YOUTUBE_VIDEO_ID"))
        self.play_sound = PlaySound()

    def start(self):
        while True:
            comment = self.youtube_comment_adapter.get_comment()
            if comment is None:
                # おとぎ話を話す
                talk = self.talker.generate_fairy_tale()
                talk_list = self.split_text(talk)
                for talk in talk_list:
                    voice: VoiceIO = self.voice_maker.make_voice_voicevox(talk)
                    self.obs_adapter.set_question("")
                    self.obs_adapter.set_answer(talk)
                    self.play_sound.play_sound(voice)
            else:
                character_speak = self.talker.chat(comment)
                speak_list = self.split_text(character_speak)
                for speak in speak_list:
                    voice: VoiceIO = self.voice_maker.make_voice_voicevox(speak)
                    self.obs_adapter.set_question(comment)
                    self.obs_adapter.set_answer(speak)
                    self.play_sound.play_sound(voice)
                time.sleep(1)
    
    def split_text(self, text: str) -> list[str]:
        # 。を区切りにしてリストにする
        text = text.replace("\n", "")
        return text.split("。")

if __name__ == "__main__":
    aituber_system = AITuberSystem()
    aituber_system.start()