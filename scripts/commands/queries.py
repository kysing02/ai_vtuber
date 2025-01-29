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