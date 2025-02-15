import os
import json
from pydantic import BaseModel

class FilePath:
    """
    ファイルに簡単にアクセスするために、ここでファイルのパスを登録する。
    今、`FilePath`に含まれている種類の分類は、`TEXT`, `JSON`, `PROMPT`がある。

    TODO: ある程度プログラムが膨大になったら、サブクラスを作成する。
    """

    TEXT_DAILY_PLAN = "storage/airi/daily_plan/{datestr}.txt"
    TEXT_MEMO = "storage/airi/memo.txt"
    TEXT_PROFILE = "storage/airi/profile.txt"
    TEXT_TIMETABLE_TEMPLATE = "storage/year_schedule/school_timetable_template.txt"
    JSON_LONG_TERM_MEMORY = "storage/airi/memory/long_term_memory.txt"
    JSON_SCHOOL_EVENTS = "storage/year_schedule/school_events_{year}.json"
    JSON_TIMETABLE = "storage/year_schedule/school_timetable_{year}.json"
    PROMPT_ACT = "storage/prompt/act.txt"
    PROMPT_ACT_PROCESS = "storage/prompt/act_process.txt"
    PROMPT_ACT_PROCESS_NEW = "storage/prompt/act_process_new.txt"
    PROMPT_ASK = "storage/prompt/ask.txt"
    PROMPT_CHANGE_PLAN = "storage/prompt/change_plan.txt"
    PROMPT_DAILY_PLANNER = "storage/prompt/daily_planner.txt"
    PROMPT_DIARY = "storage/prompt/diary.txt"
    PROMPT_EVENT_SIMULATOR = "storage/prompt/event_simulator.txt"
    PROMPT_SCHOOL_EVENT_1 = "storage/prompt/school_event_1.txt"
    PROMPT_SCHOOL_EVENT_2 = "storage/prompt/school_event_2.txt"
    PROMPT_SCHOOL_TIMETABLE = "storage/prompt/school_timetable.txt"
    PROMPT_THOUGHT = "storage/prompt/thought.txt"
    PROMPT_TWEET = "storage/prompt/tweet.txt"
    PROMPT_VOICE_CHAT = "storage/prompt/voice_chat.txt"

class FileManager:
    """
    ファイルのReadとWrite処理を簡単に行うために、`FileManager`を使用する。
    複雑な設定ができないため、詳しい設定がしたい場合はI/O処理を独自に行う必要がある。
    """

    @staticmethod
    def read(file_path: str):
        """テキストファイルを読み込む。

        Args:
            file_path (str): ファイルパス

        Returns:
            str: ファイルのテキスト内容
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            return text
    
    @staticmethod
    def write(file_path: str, content: str):
        """テキストファイルを書き込む。

        Args:
            file_path (str): ファイルパス
            content (str): ファイルに書き込むテキストの内容
        """
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
    @staticmethod
    def read_json(file_path: str):
        """JSONファイルを読み込む。

        Args:
            file_path (str): ファイルパス

        Returns:
            Any: JSONファイル
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    @staticmethod
    def write_json(file_path: str, json_file, indent=2):
        """JSONファイルを書き込む。

        Args:
            file_path (str): ファイルパス
            json_file (Any): JSONファイル(`BaseModel`と`obj`形式をサポートしている)
            indent (int): JSONファイルの空白スペース
        """
        with open(file_path, 'w', encoding='utf-8') as file:
            if isinstance(json_file, BaseModel):
                file.write(json_file.model_dump_json(indent=indent))
            else:
                file.write(json.dumps(json_file, indent=indent))

    @staticmethod
    def exist(file_path: str):
        """指定されたパスが存在しているかを調べる。

        Args:
            file_path (str): ファイルパス

        Returns:
            bool: パスが存在しているか
        """
        return os.path.exists(file_path)