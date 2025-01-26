from pydantic import BaseModel
from scripts.world_simulation.world_time import WorldTime, CallbackSchedule
from scripts.adapters.openai_adapter import OpenAIAdapter
from datetime import datetime
import os
import json
import scripts.utils.helpers as utils

class TimeTable(BaseModel):
    monday: list[str]
    tuesday: list[str]
    wednesday: list[str]
    thursday: list[str]
    friday: list[str]

class School:
    def __init__(self, world_time: WorldTime, adapter: OpenAIAdapter):
        self.world_time = world_time
        self.adapter = adapter

    def make_year_schedule(self, year: int):
        next_year_schedule = CallbackSchedule(datetime=datetime(self.world_time.current_time.year + 1, 4, 1, 0, 0), 
                                              callback=lambda : self.make_year_schedule(self.world_time.current_time.year + 1))
        self.world_time.callback_schedules.append(next_year_schedule)

        events_file_path = f"storage/year_schedule/school_events_{year}.txt"
        timetable_file_path = f"storage/year_schedule/school_timetable_{year}.txt"
        if os.path.exists(events_file_path) and os.path.exists(timetable_file_path):
            print("年間スケジュールと時間割が既に存在しているため再生成しない。")
            return

        # プロンプトチェイン１：高校の行事を生成
        system_message = """
        一年内、何月何日も含めて、日本での高校の行事を作成してください。 
        面白いイベントも入れてください。ただし、日本高校で行われそうなものに限る。（例：文化祭など）
        行事だけでいいです。他の説明は要らない。
        例：
        4月1日 入学式
        4月25日 クラブ活動紹介
        5月15日 遠足（行き先：近くの公園）
        6月1日 中間試験
        6月15日 体育祭（競技：リレー、玉入れなど）
        7月5日 学校見学会（新入生対象）
        7月20日 夏休み前の集会
        8月25日 夏休み明け集会
        9月10日 文化祭準備開始
        9月30日 文化祭
        10月15日 秋の遠足（行き先：歴史的な名所）
        11月1日 期末試験
        11月15日 学校公開日
        12月5日 音楽発表会
        12月20日 冬休み前の集会
        1月10日 冬休み明け集会
        1月25日 スポーツ大会（各種競技）
        2月5日 卒業式リハーサル
        3月1日 卒業式
        3月15日 新入生オリエンテーション
        3月25日 学年末試験
        """
        messages = [self.adapter.create_message("system", system_message),
                    self.adapter.create_message("user", f"{year}年の行事：")]
        year_schedule_draft = self.adapter.chat_completions(messages)
        # プロンプトチェイン２：休みも入れた高校行事を生成
        system_message = """
        与えられた日本の高校の行事表に、日本の祝日を入れてください。
        4月1日から3月31日までの順番で並べてください。
        行事だけでいいです。他の説明は要らない。
        例：
        2024年の行事：
        4月1日 入学式
        4月25日 クラブ活動紹介
        5月15日 遠足（行き先：近くの公園）
        ...(省略)...
        3月25日 学年末試験
        """
        messages = [self.adapter.create_message("assistant", system_message),
                    self.adapter.create_message("user", f"{year}年の行事：\n" + year_schedule_draft)]
        year_schedule = self.adapter.chat_completions()
        with open(f"storage/year_schedule/school_events_{year}.txt", "w", encoding="utf-8") as f:
            f.write(year_schedule)

        print(f"{year}年のスケジュールが生成された")

        # 学校の時間割を生成
        system_message = """
        あなたは日本のある高校の管理部に所属しています。
        その高校のあるクラスのために、時間割を作成してください。
        ただし、以下のルールに従ってください。
        - 毎日は4コマがある
        - 昼休みは無視してください
        - 曖昧な科目を入れない（選択科目など）
        """
        messages = [self.adapter.create_message("system", system_message), 
                    self.adapter.create_message("user", f"{year}年の時間割:\n")]
        timetable: TimeTable = self.adapter.create_structured_output(messages, TimeTable)
        with open(f"storage/year_schedule/school_timetable_{year}.json", "w", encoding="utf-8") as f:
            f.write(timetable.model_dump_json(indent=4))

        print(f"{year}年の学校の時間割が生成された")
    
    def get_timetable_str(self, year: int, weekday: int) -> str:
        if weekday == 5 or 6:
            return "今日は土日なので学校がありません。"
        with open(f"storage/year_schedule/school_timetable_{year}.json", "r", encoding="utf-8") as f:
            timetable_json = json.load(f)
        with open(f"storage/year_schedule/school_timetable_template.txt", "r", encoding="utf-8") as f:
            timetable_template = f.read()
        weekday_name = utils.decapitalize(utils.get_weekday_name(weekday))
        replacements = {
            "{0}": weekday_name,
            "{1}": timetable_json[weekday_name][0],
            "{2}": timetable_json[weekday_name][1],
            "{3}": timetable_json[weekday_name][2],
            "{4}": timetable_json[weekday_name][3]
        }
        timetable = utils.replace(replacements, timetable_template)
        return timetable
        
if __name__ == "__main__":
    adapter = OpenAIAdapter()
    school = School(adapter=adapter, world_time=WorldTime(adapter))
    print(school.get_timetable_str(2025, 2))