import os
import json
from pydantic import BaseModel

class FilePath:
    TEXT_DAILY_PLAN = "storage/daily_plan/{datestr}.txt"
    TEXT_PROFILE = "storage/airi/profile.txt"
    TEXT_TIMETABLE_TEMPLATE = "storage/year_schedule/school_timetable_template.txt"
    JSON_SCHOOL_EVENTS = "storage/year_schedule/school_events_{year}.json"
    JSON_TIMETABLE = "storage/year_schedule/school_timetable_{year}.json"
    PROMPT_CHANGE_PLAN = "storage/system/prompt_change_plan.txt"
    PROMPT_COMMAND_ACTIONS = "storage/commands/prompt_act.txt"
    PROMPT_ACTION_PROCESS = "storage/commands/prompt_act_process.txt"
    PROMPT_VOICE_CHAT = "storage/airi/voice_chat.txt"
    PROMPT_DIARY_MAKER = "storage/prompt_diary_maker.txt"

class FileManager:
    @staticmethod
    def read(file_path: str):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            return text
    
    @staticmethod
    def write(file_path: str, content: str):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
    @staticmethod
    def read_json(file_path: str):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    @staticmethod
    def write_json(file_path: str, json_file):
        with open(file_path, 'w', encoding='utf-8') as file:
            if isinstance(json_file, BaseModel):
                file.write(json_file.model_dump_json(indent=2))
            else:
                file.write(json.dumps(json_file, indent=2))

    @staticmethod
    def exist(file_path: str):
        return os.path.exists(file_path)
    