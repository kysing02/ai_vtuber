from scripts.adapters.obs_adapter import OBSAdapter
from scripts.adapters.vtube_studio_adapter import VTSAdapter
from scripts.sound.play_sound import PlaySound
from scripts.sound.VoiceMaker import StyleBertVits2Adapter, VoicevoxAdapter
from scripts.utils.helpers import split_japanese_text
from scripts.utils.parser import Parser

class Narrator:
    """ストリーミング画面に出力する音声、文字列を管理するモジュール。"""
    
    def __init__(self, vits2: StyleBertVits2Adapter, voicevox: VoicevoxAdapter, 
                 vts: VTSAdapter, play_sound_narrator: PlaySound, play_sound_airi: PlaySound, obs: OBSAdapter):
        self.vits2 = vits2
        self.voicevox = voicevox
        self.vts = vts
        self.play_sound_narrator = play_sound_narrator
        self.play_sound_airi = play_sound_airi
        self.obs = obs
    
    async def narrate(self, message: str, role: str='info'):
        token, text_raw = Parser.parse_expression(message)
        text_list = split_japanese_text(text_raw)
        text_first = text_list.pop(0)
        self.obs.set_answer(text_first)
        if role in ['info', 'user']:
            response_voice = self.voicevox.get_voice(text_first)
            self.play_sound_narrator.play_sound(response_voice)
        else:
            response_voice = self.vits2.get_voice(text_first)
            self.play_sound_airi.play_sound(response_voice)
        if token and self.vts is not None:
            for _, expression in self.vts.hotkeys.items():
                if expression == token:
                    await self.vts.trigger_hotkeys(expression)
        
        for text in text_list:
            self.obs.set_answer(text)
            if role in ['info', 'user']:
                response_voice = self.voicevox.get_voice(text)
                self.play_sound_narrator.play_sound(response_voice)
            else:
                response_voice = self.vits2.get_voice(text)
                self.play_sound_airi.play_sound(response_voice)
        