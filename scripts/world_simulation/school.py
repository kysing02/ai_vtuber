from pydantic import BaseModel
from scripts.world_simulation.world_time import WorldTime, CallbackSchedule
from scripts.adapters.openai_adapter import OpenAIAdapter
from datetime import datetime
import scripts.utils.helpers as utils
from file_manager import FileManager, FilePath
import logging

class TimeTable(BaseModel):
    """時間割を記録するためのクラス。月曜日から金曜日までを記録する。"""
    monday: list[str]
    tuesday: list[str]
    wednesday: list[str]
    thursday: list[str]
    friday: list[str]

class SchoolEvent(BaseModel):
    """学校の行事を記録するためのクラス。何月何日、それから行事の名前を記録する。"""
    month: int
    day: int
    description: str

class SchoolEvents(BaseModel):
    """学校の行事表を記録する。"""
    events: list[SchoolEvent]

class School:
    """
    学校に関することを管理するモジュール。
    主に年間スケジュールと時間割の生成、保存、取得を管理する。
    """
    
    def __init__(self, world_time: WorldTime, adapter: OpenAIAdapter):
        self.world_time = world_time
        self.adapter = adapter

    def make_year_schedule(self, year: int):
        """
        年間学校行事表と時間割を生成する。既存するものがあれば処理がスキップされる。
        来年度からのスケジュールも自動的に作成されるようになる。

        Args:
            year (int): 何年度の学校行事表と時間割を生成するか
        """

        # 来年のスケジュールも4月1日になったらまた自動的に作成する
        self.world_time.add_timer(datetime=datetime(self.world_time.current_time.year + 1, 4, 1, 0, 0),
                                  callback=lambda : self.make_year_schedule(self.world_time.current_time.year + 1))

        events_file_path = FilePath.JSON_SCHOOL_EVENTS.format(year=year)
        timetable_file_path = FilePath.JSON_TIMETABLE.format(year=year)

        if FileManager.exist(events_file_path) and FileManager.exist(timetable_file_path):
            logging.info("年間スケジュールと時間割が既に存在しているため再生成しない。")
            return

        # プロンプトチェイン１：高校の行事を生成
        school_event_prompt = FileManager.read(FilePath.PROMPT_SCHOOL_EVENT_1)
        messages = [self.adapter.create_message("system", school_event_prompt),
                    self.adapter.create_message("user", f"{year}年の行事：")]
        school_event_draft = self.adapter.chat_completions(messages)

        # プロンプトチェイン２：休みも入れた高校行事を生成
        school_event_prompt = FileManager.read(FilePath.PROMPT_SCHOOL_EVENT_2)
        messages = [self.adapter.create_message("system", school_event_prompt),
                    self.adapter.create_message("user", f"{year}年の行事：\n" + school_event_draft)]
        school_events = self.adapter.create_structured_output(messages, SchoolEvents)
        FileManager.write_json(events_file_path, school_events)

        logging.info(f"{year}年のスケジュールが生成された。")

        # 学校の時間割を生成
        timetable_prompt = FileManager.read(FilePath.PROMPT_SCHOOL_TIMETABLE)
        messages = [self.adapter.create_message("system", timetable_prompt), 
                    self.adapter.create_message("user", f"{year}年の時間割:\n")]
        timetable = self.adapter.create_structured_output(messages, TimeTable)
        FileManager.write_json(timetable_file_path, timetable)

        logging.info(f"{year}年の学校の時間割が生成された。")
    
    def get_timetable_str(self, year: int=None, weekday: int=None):
        if not year or not weekday:
            year = self.world_time.current_time.year
            weekday = self.world_time.current_time.weekday()
        if weekday == 5 or weekday == 6:
            return "今日は土日なので学校がありません。"
        timetable_json = FileManager.read_json(FilePath.JSON_TIMETABLE.format(year=year))
        timetable_template = FileManager.read(FilePath.TEXT_TIMETABLE_TEMPLATE)
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
    
    def get_school_events_str(self, datetime: datetime=None) -> str:
        school_events = self.get_school_events(datetime)
        year = self.__get_annual_year(datetime)
        school_events_str = f"{year}年の学校行事："
        
        for event in school_events.events:
            event_str = f"{event.month}月{event.day}日 {event.description}"
            school_events_str = "\n".join([school_events_str, event_str])
        
        return school_events_str
    
    def get_school_events(self, datetime: datetime=None):
        if datetime is None:
            datetime = self.world_time.current_time
        year = self.__get_annual_year(datetime)
        school_events_data = FileManager.read_json(FilePath.JSON_SCHOOL_EVENTS.format(year=year))
        events = school_events_data.get("events", [])
        return SchoolEvents(events=[SchoolEvent(**event) for event in events])

    def get_school_event_today(self, datetime: datetime=None):
        school_events = self.get_school_events()
        for event in school_events.events:
            if event.day == datetime.day and event.month == datetime.month:
                return event
        return None
    
    def get_school_event_today_str(self, datetime: datetime=None):
        if datetime is None:
            datetime = self.world_time.current_time
        event_today = self.get_school_event_today(datetime)
        return f"{event_today.month}月{event_today.day}日の学校行事： {event_today.description}"
    
    def __get_annual_year(self, datetime: datetime=None):
        # 4月以降の年度は今年、3月以前の年度は去年
        # 例. 2024.4 -> 2024, 2025.3 -> 2024
        if datetime is None:
            datetime = self.world_time.current_time
        return datetime.year if datetime.month >= 4 else datetime.year - 1
    
if __name__ == "__main__":
    adapter = OpenAIAdapter()
    school = School(adapter=adapter, world_time=WorldTime(adapter))
    print(school.get_timetable_str(2025, 2))