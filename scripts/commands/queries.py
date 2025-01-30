from scripts.file_manager import FileManager
from scripts.vlife import VLife

# クエリはシステム権限のみアクセスできる
class Queries:
    PREDEFINED_QUERIES = [
        "PROFILE",
        "SCHOOL_EVENTS",
        "TIMETABLE"
        "LONG_TERM_MEMORY",
        "SHORT_TERM_MEMORY",
        "MEMO_APP",
        "DATETIME",
        "THOUGHTS"
    ]

    def __init__(self, vlife: VLife):
        self.vlife = vlife

    def parse(self, text: str):
        replacements = {
            "!PROFILE": VLife.get_profile,
            "!SCHOOL_EVENTS": self.vlife.school.get_school_events_str,
            "!TIMETABLE": self.vlife.school.get_timetable_str,
            "!LONG_TERM_MEMORY": "Past Memory",
            "!SHORT_TERM_MEMORY": lambda: self.vlife.short_term_memory.get_short_term_memory_str(10),
            "!MEMO_APP": lambda: self.vlife.memo.read_memos_str(5),
            "!DATETIME": self.vlife.world_time.get_time_str,
            "!THOUGHTS": "Daily Reflections",
            "!AVAILABLE_ACTIONS": self.vlife.action_manager.get_available_actions_str
        }
        # Replace placeholders, calling functions only when needed
        for key, value in replacements.items():
            if f"{{{key}}}" in text:
                text = text.replace(f"{{{key}}}", value() if callable(value) else value)
    
    def load_prompt_from_file(self, prompt_path: str):
        prompt_template = FileManager.read(prompt_path)
        prompt = self.parse(prompt_template)
        return prompt