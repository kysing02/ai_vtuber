import logging
import scripts.utils.helpers as utils
from datetime import datetime
from pydantic import BaseModel
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.file_manager import FileManager, FilePath
from scripts.world_simulation.world_time import WorldTime

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

    def make_year_schedule(self):
        """
        年間学校行事表と時間割を生成する。既存するものがあれば処理がスキップされる。
        来年度からのスケジュールも自動的に作成されるようになる。
        """
        annual_year = self.__get_annual_year()
        # 来年のスケジュールも4月1日になったらまた自動的に作成する
        self.world_time.add_timer(datetime=datetime(self.world_time.current_time.year + 1, 4, 1, 0, 0),
                                  callback=self.make_year_schedule)

        events_file_path = FilePath.JSON_SCHOOL_EVENTS.format(year=annual_year)
        timetable_file_path = FilePath.JSON_TIMETABLE.format(year=annual_year)

        if FileManager.exist(events_file_path) and FileManager.exist(timetable_file_path):
            logging.info("年間スケジュールと時間割が既に存在しているため再生成しない。")
            return

        # プロンプトチェイン１：高校の行事を生成
        school_event_prompt = FileManager.read(FilePath.PROMPT_SCHOOL_EVENT_1)
        messages = [self.adapter.create_message("system", school_event_prompt),
                    self.adapter.create_message("user", f"{annual_year}年度の行事：")]
        school_event_draft = self.adapter.chat_completions(messages)

        # プロンプトチェイン２：休みも入れた高校行事を生成
        school_event_prompt = FileManager.read(FilePath.PROMPT_SCHOOL_EVENT_2)
        messages = [self.adapter.create_message("system", school_event_prompt),
                    self.adapter.create_message("user", f"{annual_year}年度の行事：\n" + school_event_draft)]
        school_events = self.adapter.create_structured_output(messages, SchoolEvents)
        FileManager.write_json(events_file_path, school_events)

        logging.info(f"{annual_year}年度のスケジュールが生成された。")

        # 学校の時間割を生成
        timetable_prompt = FileManager.read(FilePath.PROMPT_SCHOOL_TIMETABLE)
        messages = [self.adapter.create_message("system", timetable_prompt), 
                    self.adapter.create_message("user", f"{annual_year}年度の時間割:\n")]
        timetable = self.adapter.create_structured_output(messages, TimeTable)
        FileManager.write_json(timetable_file_path, timetable)

        logging.info(f"{annual_year}年度の学校の時間割が生成された。")
    
    def __get_timetable(self):
        """学校の時間割をJSONフォーマットとして取得する。

        Returns:
            any: 学校の時間割(JSON)
        """
        annual_year = self.__get_annual_year()
        timetable_json = FileManager.read_json(FilePath.JSON_TIMETABLE.format(year=annual_year))
        return timetable_json

    def get_timetable_str(self):
        """学校の時間割を取得する。

        Returns:
            str: 学校の時間割（文字列）
        """
        annual_year = self.__get_annual_year()
        weekday = self.world_time.current_time.weekday()
        if weekday == 5 or weekday == 6:
            return "今日は土日なので学校がありません。"
        
        timetable_json = self.__get_timetable()
        timetable_template = FileManager.read(FilePath.TEXT_TIMETABLE_TEMPLATE)
        weekday_name = utils.decapitalize(utils.get_weekday_name(weekday))
        weekday_name_ja = utils.get_weekday_japanese(weekday)
        replacements = {
            "{0}": weekday_name_ja,
            "{1}": timetable_json[weekday_name][0],
            "{2}": timetable_json[weekday_name][1],
            "{3}": timetable_json[weekday_name][2],
            "{4}": timetable_json[weekday_name][3]
        }
        timetable = utils.replace(replacements, timetable_template)
        return timetable
    
    def __get_school_events(self):
        """学校の行事表を`SchoolEvents`フォーマットとして取得する。JSONではないことに注意。

        Returns:
            SchoolEvents: 学校の行事表
        """
        annual_year = self.__get_annual_year()
        school_events_data = FileManager.read_json(FilePath.JSON_SCHOOL_EVENTS.format(year=annual_year))
        events = school_events_data.get("events", [])
        return SchoolEvents(events=[SchoolEvent(**event) for event in events])
    
    def get_school_events_str(self):
        """学校の行事表を取得する。

        Returns:
            str: 学校の行事表（文字列）
        """
        annual_year = self.__get_annual_year()
        school_events = self.__get_school_events()
        school_events_str = f"{annual_year}年の学校行事："
        
        for event in school_events.events:
            event_str = f"{event.month}月{event.day}日 {event.description}"
            school_events_str = "\n".join([school_events_str, event_str])
        
        return school_events_str

    def __get_school_event_today(self):
        """学校の今日の行事一つを`SchoolEvent`フォーマットとして取得する。JSONではないことに注意。

        Returns:
            SchoolEvent: 学校の今日の事
        """
        datetime = self.world_time.current_time
        school_events = self.__get_school_events()
        for event in school_events.events:
            if event.day == datetime.day and event.month == datetime.month:
                return event
        return None
    
    def get_school_event_today_str(self):
        """学校の今日の行事を取得する。

        Returns:
            str: 学校の今日の行事
        """
        datetime = self.world_time.current_time
        event_today = self.__get_school_event_today()
        if event_today is None:
            return f"{datetime.month}月{datetime.day}日の学校行事：特別行事がありません。"
        else:
            return f"{event_today.month}月{event_today.day}日の学校行事： {event_today.description}"
    
    def __get_annual_year(self):
        """
        今年度を取得する。
        4月以降の年度は今年、3月以前の年度は去年になる。
        
        例. 2024.4 -> 2024, 2025.3 -> 2024

        Returns:
            int: 今年度
        """
        datetime = self.world_time.current_time
        return datetime.year if datetime.month >= 4 else datetime.year - 1
    
if __name__ == "__main__":
    adapter = OpenAIAdapter()
    school = School(adapter=adapter, 
                    world_time=WorldTime(adapter=adapter, loop=None))
    
    print(school.get_timetable_str())
    print(school.get_school_events_str())
    print(school.get_school_event_today_str())