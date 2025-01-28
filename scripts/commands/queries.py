from scripts.adapters.openai_adapter import OpenAIAdapter
# クエリはシステム権限のみアクセスできる
PREDEFINED_QUERIES = [
    "PROFILE",
    "SCHOOL_EVENTS",
    "TIMETABLE",
    "LONG_TERM_MEMORY",
    "SHORT_TERM_MEMORY",
    "MEMO_APP",
    "DATE",
    "TIME",
    "THOUGHTS"
]

class Queries:
    def __init__(self, adapter: OpenAIAdapter):
        self.adapter = adapter
        self.available_queries = PREDEFINED_QUERIES.append(self.__load_saved_queries())

    def get_available_queries():
        raise NotImplementedError

    def parse(text: str):
        raise NotImplementedError
    
    def load_prompt_from_file(self, prompt_path: str):
        with open(prompt_path) as file:
            prompt_template = file.read()
            prompt = self.parse(prompt_template)
            return prompt