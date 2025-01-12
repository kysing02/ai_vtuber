import random
from openai_adapter import OpenAIAdapter

class Talker:
    def __init__(self):
        self.talk_history: list[dict[str, str]] = []
        with open("aituber_system_prompt.txt", "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
        
    def chat(self, message):
        adapter = OpenAIAdapter()
        self.talk_history.append({"role":"user",
                                  "content":"message"})