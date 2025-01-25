import json
from typing import TypedDict
import numpy as np
from scripts.adapters.openai_adapter import OpenAIAdapter
import requests
import soundfile
import io
from pathlib import Path
from style_bert_vits2.nlp import bert_models
from style_bert_vits2.constants import Languages
from style_bert_vits2.tts_model import TTSModel

class VoiceIO(TypedDict):
    data:np.ndarray
    sample_rate:int

class VoiceMaker:
    @staticmethod
    def make_voice_openai(text: str) -> VoiceIO:
        adapter = OpenAIAdapter()
        response_bytes = adapter.create_voice(text)
        data,sample_rate = soundfile.read(io.BytesIO(response_bytes))
        return VoiceIO(data=data, sample_rate=sample_rate)
    
    @staticmethod
    def make_voice_voicevox(text: str) -> VoiceIO:
        adapter = VoicevoxAdapter()
        return adapter.get_voice(text)

    @staticmethod
    def make_voice_style_bert_vits2(text: str) -> VoiceIO:
        adapter = StyleBertVits2Adapter()
        return adapter.get_voice(text)
    
    @staticmethod
    def make_voice_fish_audio(text: str) -> VoiceIO:
        adapter = FishAudioAdapter()
        return adapter.get_voice(text)

class VoicevoxAdapter:
    URL = 'http://127.0.0.1:50021/'
    # 二回postする。一回目で変換、二回目で音声合成
    def __init__(self) -> None:
        pass
    def __create_audio_query(self, text: str, speaker_id: int) -> json:
        item_data={'text': text,
                   'speaker': speaker_id}
        response = requests.post(self.URL+'audio_query', params=item_data)
        return response.json()
    def __create_request_audio(self, query_data, speaker_id: int) -> bytes:
        a_params = {
            'speaker': speaker_id
        }
        headers = {"accept": "audio/wav", "Content-Type":"application/json"}
        res = requests.post(self.URL+'synthesis', params=a_params, data=json.dumps(query_data), headers=headers)
        print(res.status_code)
        return res.content
    def get_voice(self, text: str) -> VoiceIO:
        speaker_id = 59 # 「猫使ビィ」のspeaker_id
        query_data:json = self.__create_audio_query(text, speaker_id=speaker_id)
        query_data["speedScale"] = 1.0          # VOICEVOXでは 0.50 ~ 2.00の範囲で指定できる
        query_data["pitchScale"] = -0.05        # VOICEVOXでは-0.15 ~ 0.15の範囲で指定できる
        query_data["intonationScale"] = 0.90    # VOICEVOXでは 0.00 ~ 2.00の範囲で指定できる
        query_data["volumeScale"] = 1.0         # VOICEVOXでは 0.00 ~ 2.00の範囲で指定できる
        audio_bytes = self.__create_request_audio(query_data,speaker_id=speaker_id)
        audio_stream = io.BytesIO(audio_bytes)
        data, sample_rate = soundfile.read(audio_stream)
        return VoiceIO(data=data, sample_rate=sample_rate)

class StyleBertVits2Adapter:
    def __init__(self):
        # ダウンロードされたデフォルトモデルのディレクトリ
        model_file = "amitaro/amitaro.safetensors"
        config_file = "amitaro/config.json"
        style_file = "amitaro/style_vectors.npy"

        # BERTモデルをロード（ローカルに手動でダウンロードする必要はありません）
        bert_models.load_model(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
        bert_models.load_tokenizer(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")

        # モデルを設定
        assets_root = Path("model_assets")
        self.model = TTSModel(
            model_path=assets_root / model_file,
            config_path=assets_root / config_file,
            style_vec_path=assets_root / style_file,
            device="cuda"
        )

    def get_voice(self, text: str) -> VoiceIO:
        sr, audio = self.model.infer(text=text)
        return VoiceIO(data=audio, sample_rate=sr)

class FishAudioAdapter:
    URL = 'http://127.0.0.1:7000/'
    def __init__(self) -> None:
        pass
    def __create_tts(self, query_data) -> bytes:
        headers = {"accept": "audio/wav", "Content-Type":"application/json"}
        res = requests.post(self.URL+'v1/tts', json=query_data, headers=headers)
        print(res.status_code)
        return res.content
    def get_voice(self, text: str) -> VoiceIO:
        query_data = {
            "text": text,
            "chunk_length": 200,
            "format": "wav",
            "references": [],
            "reference_id": "hina", # 「空崎ヒナ」のreference_id
            "seed": None,
            "use_memory_cache": "off",
            "normalize": True,
            "streaming": False,
            "max_new_tokens": 1024,
            "top_p": 0.7,
            "repetition_penalty": 1.2,
            "temperature": 0.7
        }
        audio_bytes = self.__create_tts(query_data)
        audio_stream = io.BytesIO(audio_bytes)
        data, sample_rate = soundfile.read(audio_stream)
        return VoiceIO(data=data, sample_rate=sample_rate)
        

if __name__ == "__main__":
    voice_io = VoiceMaker.make_voice_style_bert_vits2("人工音声のテストです。")

    with open("test.wav", "wb") as f:
        # バイトデータとrateからwavファイルを作成
        soundfile.write(f, voice_io["data"], voice_io["sample_rate"])