import re
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.file_manager import FileManager, FilePath
from scripts.commands.queries import Queries

class Reflection:
    def __init__(self, adapter: OpenAIAdapter, queries: Queries):
        self.adapter = adapter
        self.queries = queries
        self.thought = ""

    def reflect_thought(self):
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_THOUGHT)
        thought = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                                 self.adapter.create_message('user', "今考えていること:")])
        self.thought = thought
        return thought
    
if __file__ == "__main__":
    vlife = None
    adapter = OpenAIAdapter()
    queries = Queries(vlife)
    reflection = Reflection(adapter, queries)
    print("Test 1")
    print(reflection.reflect_thought())
    