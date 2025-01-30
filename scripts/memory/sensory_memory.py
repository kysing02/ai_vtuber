from scripts.memory.reflection import Emotion

class SensoryMemory:
    def __init__(self):
        self.memory_list: list[str] = []

    def add(self, message):
        self.memory_list.append(message)
        