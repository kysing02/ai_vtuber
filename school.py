from pydantic import BaseModel
from world_time import WorldTime, CallbackSchedule
from openai_adapter import OpenAIAdapter
from datetime import datetime

class TimeTable(BaseModel):
    monday: list[str]
    tuesday: list[str]
    wednesday: list[str]
    thursday: list[str]
    friday: list[str]

class SchoolEvent(BaseModel):
    month: int
    day: int
    description: str

class SchoolEventList(BaseModel):
    event: list[SchoolEvent]

class School:
    def __init__(self, world_time: WorldTime, adapter: OpenAIAdapter):
        self.world_time = world_time
        self.adapter = adapter
        self.__make_year_schedule(world_time.current_time.year)

    def __make_year_schedule(self, year):
        print(f"{year}年のスケジュールを生成する")

        # プロンプトチェイン１：高校の行事を生成
        assistant_message = """
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
        user_message = f"{year}年の行事："
        year_schedule_draft = self.adapter.chat_completions([self.adapter.create_message("assistant", assistant_message),
                                                       self.adapter.create_message("user", user_message)])
        # プロンプトチェイン２：休みも入れた高校行事を生成
        system_message = """
        与えられた日本の高校の行事表に、日本の祝日を入れてください。
        4月1日から3月31日までの順番で並べてください。。
        """
        year_schedule = self.adapter.create_structured_output([self.adapter.create_message("assistant", system_message),
                                                               self.adapter.create_message("user", f"{year}年の行事：\n" + year_schedule_draft)],
                                                               SchoolEventList)
        with open(f"storage/year_schedule/school_events_{year}.json", "w", encoding="utf-8") as f:
            f.write(year_schedule.model_dump_json(indent=4))
        next_year_schedule = CallbackSchedule(datetime=datetime(self.world_time.current_time.year + 1, 4, 1, 0, 0), 
                                              callback=lambda : self.__make_year_schedule(self.world_time.current_time.year + 1))
        self.world_time.callback_schedules.append(next_year_schedule)
    
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
                    self.adapter.create_message("user", f"{year}年の時間割\n")]
        timetable: TimeTable = self.adapter.create_structured_output(messages, TimeTable)
        with open(f"storage/year_schedule/school_timetable_{year}.json", "w", encoding="utf-8") as f:
            f.write(timetable.model_dump_json(indent=4))
    
    @staticmethod
    def get_timetable_str(year):
        with open(f"")
        
if __name__ == "__main__":
    adapter = OpenAIAdapter()
    school = School(adapter=adapter, world_time=WorldTime(adapter))
