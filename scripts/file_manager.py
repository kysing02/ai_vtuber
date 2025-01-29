import os
import json
from pydantic import BaseModel

class FilePath:
    PROMPT_CHANGE_PLAN = "storage/system/prompt_change_plan.txt"

class FileManager:
    @staticmethod
    def open_file(file_path: str):
        with open(file_path) as file:
            text = file.read()
            return text
    
    @staticmethod
    def write_json_file(file_path: str, json_file):
        with open(file_path, "w", encoding="utf-8") as file:
            if isinstance(json_file, BaseModel):
                file.write(json_file.model_dump_json(indent=2))
            else:
                file.write(json.dumps(json_file, indent=2))

    @staticmethod
    def exist(file_path: str):
        return os.path.exists(file_path)
    