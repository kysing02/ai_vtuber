import asyncio
from scripts.world_simulation.world_time import WorldTime
from datetime import datetime
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.file_manager import FileManager, FilePath
import numpy as np
from scripts.world_simulation.narrator import Narrator

class MemoryRecord:
    def __init__(self, memory_time: datetime, role: str, message: str, adapter: OpenAIAdapter, skip_embedding=False):
        self.memory_time = memory_time
        self.role = role
        self.message = message
        # TODO メモリに入った瞬間は、高速化を図るために、まだEmbeddingの処理をしないこともある（リアルタイム性重視の場合）
        self.embedding: list[float] = []
        if not skip_embedding:
            self.embedding = adapter.create_embedding(self.message)

    def to_dict(self):
        """Convert the object to a JSON-serializable dictionary."""
        return {
            "memory_time": self.memory_time.isoformat(),  # Convert datetime to string
            "role": self.role,
            "message": self.message,
            "embedding": self.embedding
        }

class LongTermMemory:
    def __init__(self, adapter: OpenAIAdapter):
        # self.__load_memory_from_file()
        self.memory_list: list[MemoryRecord] = []
        self.adapter = adapter

    def __load_memory_from_file():
        raise NotImplementedError
    
    import numpy as np

    def cosine_similarity(self, arr1, arr2):
        # Convert arrays to numpy arrays if they aren't already
        arr1 = np.array(arr1)
        arr2 = np.array(arr2)
        
        # Compute the dot product of the two arrays
        dot_product = np.dot(arr1, arr2)
        
        # Compute the norm (magnitude) of each array
        norm_arr1 = np.linalg.norm(arr1)
        norm_arr2 = np.linalg.norm(arr2)
        
        # Compute the cosine similarity score
        if norm_arr1 == 0 or norm_arr2 == 0:
            return 0.0  # Avoid division by zero if either array is a zero vector
        
        similarity = dot_product / (norm_arr1 * norm_arr2)
        return similarity
    
    def get_top_similar_memories(self, num: int, text: str):
        text_embedding = self.adapter.create_embedding(text)
        similarity_scores = []

        for memory in self.memory_list:
            if memory.embedding:  # Ensure embedding exists
                similarity = self.cosine_similarity(text_embedding, memory.embedding)
                similarity_scores.append((memory, similarity))

        # Sort by similarity score (highest to lowest) and extract only MemoryRecord objects
        top_memories: list[MemoryRecord] = [mem[0] for mem in sorted(similarity_scores, key=lambda x: x[1], reverse=True)]
        return top_memories[:num]  # Return only MemoryRecord objects

    def get_top_similar_memories_str(self, num: int, text: str):
        top_n_memories = self.get_top_similar_memories(num, text)
        top_n_memories_str = "今のアイリの行動と関係がある昔の記憶：\n"
        for memory in top_n_memories:
            top_n_memories_str += f"{memory.memory_time.strftime('[%Y年%m月%d日 %H時%M分]')}{memory.message}"
        print("[DEBUG]:", top_n_memories_str)
        return top_n_memories_str

    async def process_batch(self, memory_to_process: list[MemoryRecord]):
        # Hint: This might be a process comsuming task. Consider running this in background.
        for memory in memory_to_process:
            if not memory.embedding:
                memory.embedding = self.adapter.create_embedding(memory.message)
        
        # Save embeddings into own memory_list and save to file
        self.memory_list.extend(memory_to_process)
        FileManager.write_json(FilePath.JSON_LONG_TERM_MEMORY, [item.to_dict() for item in self.memory_list])

class ShortTermMemory:
    LTM_UPDATE_FREQUENCY = 5   # 何件の新しいことが起きたときに、短期記憶を長期記憶に保存するか
    
    def __init__(self, worldtime: WorldTime, long_term_memory: LongTermMemory, adapter: OpenAIAdapter, narrator: Narrator):
        self.memory_list: list[MemoryRecord] = []
        self.memory_list_gpt = []
        self.worldtime = worldtime
        self.long_term_memory = long_term_memory
        self.adapter = adapter
        self.narrator = narrator
        # self.__load_memory_from_file()
        self.notification = None # Temporary solution for message ignored bug

    def __load_memory_from_file(self):
        raise NotImplementedError

    async def add(self, message: str, role: str='info', skip_embedding=True, narrate=True):
        memory_time = self.worldtime.current_time
        self.memory_list.append(MemoryRecord(memory_time, role, message, self.adapter, skip_embedding))
        # GPTが認識できるフォーマットにする
        if role == 'info':
            role_msg = 'INFO'
        elif role == 'assistant':
            role_msg = 'アイリ'
        else:
            role_msg = 'システム'
        print(f"[メモリ更新：{memory_time}][{role_msg}]{message}")
        if narrate:
            await self.narrator.narrate(message, role)
        if role == 'info':
            role = 'user'
            message = "[INFO]" + message
        self.memory_list_gpt.append(self.adapter.create_message(role, f"{message}")) # TODO Temporarily removed time
        # if len(self.memory_list) % ShortTermMemory.LTM_UPDATE_FREQUENCY == 0 and len(self.memory_list) > 0:
        #     asyncio.create_task(self.long_term_memory.process_batch(self.memory_list[-10:]))

    def create_notification(self, message:str):
        memory_time = self.worldtime.current_time
        self.notification = MemoryRecord(memory_time=memory_time, role='info', message=message, adapter=self.adapter, skip_embedding=True)

    def clear_notification(self):
        self.notification = None

    def get_short_term_memory(self, num: int):
        memory_list_gpt = self.memory_list_gpt[-num: ]
        if isinstance(self.notification, MemoryRecord):
            memory_list_gpt.append(self.adapter.create_message(role='user', content=self.notification.message))
        return memory_list_gpt

    def get_short_term_memory_str(self, num: int):
        retrieved_memory = self.memory_list[-num:]
        retrieved_memory_str = "アイリが直近にあったことの詳細："
        for record in retrieved_memory:
            retrieved_memory_str += f"\n[{record.memory_time}] {record.message}"
        if isinstance(self.notification, MemoryRecord):
            retrieved_memory_str += f"\n[{self.notification.memory_time}] {self.notification.message}"
        return retrieved_memory_str