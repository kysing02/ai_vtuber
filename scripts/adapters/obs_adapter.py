import obsws_python as obs
import os
from dotenv import load_dotenv
import logging

class OBSAdapter:
    def __init__(self) -> None:
        load_dotenv()
        password = os.environ.get('OBS_WS_PASSWORD')
        host = os.environ.get('OBS_WS_HOST')
        port = os.environ.get('OBS_WS_PORT')
        # 設定されていない場合はエラー
        if (password == None or host == None or port == None):
            raise Exception("OBSの設定がされていません")
        self.ws = obs.ReqClient(host=host,
                                port=port,
                                password=password)

    def set_question(self, text: str):
        self.ws.set_input_settings(name="Question", settings={"text": text}, overlay=True)
    
    def set_answer(self, text: str):
        self.ws.set_input_settings(name="Answer", settings={"text": text}, overlay=True)

    def set_scene(self, scene_name: str="Storytelling-Scene"):
        self.ws.set_current_scene_collection(scene_name)
        logging.info(f"Scene changed to {scene_name}")

    def start_streaming(self):
        self.ws.set_stream_service_settings()

if __name__ == "__main__":
    obsAdapter = OBSAdapter()
    import random
    question_text = "Questionの番号は" + str(random.randint(0, 100)) + "になりました"
    obsAdapter.set_question(question_text)
    answer_text = "Answerの番号は" + str(random.randint(0, 100)) + "になりました"
    obsAdapter.set_answer(answer_text)
    obsAdapter.set_scene()