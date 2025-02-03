from scripts.sound.play_sound import PlaySound
from scripts.adapters.vtube_studio_adapter import VTSAdapter
from scripts.utils.helpers import split_japanese_text
from scripts.sound.VoiceMaker import StyleBertVits2Adapter, VoicevoxAdapter
from scripts.file_manager import FileManager, FilePath
from scripts.adapters.obs_adapter import OBSAdapter
from scripts.utils.parser import Parser
from scripts.utils.helpers import split_japanese_text

class Narrator:
    def __init__(self, vits2: StyleBertVits2Adapter, voicevox: VoicevoxAdapter, 
                 vts: VTSAdapter, playsound: PlaySound,obs: OBSAdapter):
        self.vits2 = vits2
        self.voicevox = voicevox
        self.vts = vts
        # self.playsound = playsound
        self.playsound2 = PlaySound(output_device_name="Speakers") # Use default output for this
        self.playsound1 = PlaySound(output_device_name="CABLE Input")
        self.obs = obs
    
    async def narrate(self, message: str, role: str='info'):
        token, text_raw = Parser.parse_expression(message)
        text_list = split_japanese_text(text_raw)
        text_first = text_list.pop(0)
        self.obs.set_answer(text_first)
        if role in ['info', 'user']:
            response_voice = self.voicevox.get_voice(text_first)
            self.playsound2.play_sound(response_voice)
        else:
            response_voice = self.vits2.get_voice(text_first)
            self.playsound1.play_sound(response_voice)
        if token and self.vts is not None:
            for _, expression in self.vts.hotkeys.items():
                if expression == token:
                    await self.vts.trigger_hotkeys(expression)
        
        for text in text_list:
            self.obs.set_answer(text)
            if role in ['info', 'user']:
                response_voice = self.voicevox.get_voice(text)
                self.playsound2.play_sound(response_voice)
            else:
                response_voice = self.vits2.get_voice(text)
                self.playsound1.play_sound(response_voice)
        