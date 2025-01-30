from scripts.memory.reflection import Emotion

class SensoryMemory:
    def __init__(self):
        self.memory_list: list[str] = []
        self.__load_memory_from_file()

    def __load_memory_from_file(self):
        raise NotImplementedError

    def add(self, message):
        self.memory_list.append(message)
        