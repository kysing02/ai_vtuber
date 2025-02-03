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
            top_n_memories_str += f"{memory.memory_time.strftime('[%d年%m月%Y日 %H時%M分]')}{memory.message}"

    async def process_batch(self, memory_to_process: list[MemoryRecord]):
        # Hint: This might be a process comsuming task. Consider running this in background.
        for memory in memory_to_process:
            if not memory.embedding:
                memory.embedding = self.adapter.create_embedding(memory.message)
        
        # Save embeddings into own memory_list and save to file
        self.memory_list.extend(memory_to_process)
        FileManager.write_json(FilePath.JSON_LONG_TERM_MEMORY, self.memory_list)

class ShortTermMemory:
    LTM_UPDATE_FREQUENCY = 1000   # 何件の新しいことが起きたときに、短期記憶を長期記憶に保存するか
    
    def __init__(self, worldtime: WorldTime, long_term_memory: LongTermMemory, adapter: OpenAIAdapter, narrator: Narrator):
        self.memory_list: list[MemoryRecord] = []
        self.memory_list_gpt = []
        self.worldtime = worldtime
        self.long_term_memory = long_term_memory
        self.adapter = adapter
        self.narrator = narrator
        # self.__load_memory_from_file()

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
        self.memory_list_gpt.append(self.adapter.create_message(role, f"[{self.worldtime.get_time_str_short()}] {message}"))
        # if len(self.memory_list) % 40 == 0 and len(self.memory_list) > 0:
        #     loop = asyncio.get_running_loop()
        #     loop.run_until_complete(asyncio.to_thread(self.long_term_memory.process_batch, self.memory_list[-40:]))

    def get_short_term_memory(self, num: int):
        return self.memory_list_gpt[-num: ]

    def get_short_term_memory_str(self, num: int):
        retrieved_memory = self.memory_list[-num:]
        retrieved_memory_str = "アイリが直近にあったことの詳細："
        for record in retrieved_memory:
            retrieved_memory_str += f"\n[{record.memory_time}] {record.message}"
        return retrieved_memory_str