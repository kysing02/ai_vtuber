from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.world_simulation.world_time import WorldTime
from scripts.commands.queries import Queries
from datetime import datetime
from scripts.file_manager import FileManager, FilePath
import logging

class DailyPlanner:
    def __init__(self, adapter: OpenAIAdapter, queries: Queries):
        self.adapter = adapter
        self.queries = queries

    def make_daily_plan(self, datetime: datetime):
        datestr = datetime.strftime("%Y%m%d")
        daily_plan_file_path = FilePath.TEXT_DAILY_PLAN.format(datestr=datestr)
        if FileManager.exist(daily_plan_file_path):
            logging.info("一日の予定表が既に存在しているため再生成しない。")
            return
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_DAILY_PLANNER)
        message = [self.adapter.create_message('system', prompt),
                   self.adapter.create_message('user', "情報に基づいて、今日の予定を作ろう。")]
        daily_plan = self.adapter.chat_completions(message)
        with open(daily_plan_file_path, "w", encoding="utf-8") as file:
            file.write(daily_plan)

    def update_daily_plan(self, datetime: datetime, new_plan: str):
        datestr = datetime.strftime("%Y%m%d")
        daily_plan_file_path = FilePath.TEXT_DAILY_PLAN.format(datestr=datestr)
        if not FileManager.exist(daily_plan_file_path):
            return
        FileManager.write(daily_plan_file_path, new_plan)

    def get_daily_plan(self, datetime: datetime):
        datestr = datetime.strftime("%Y%m%d")
        daily_plan_file_path = FilePath.TEXT_DAILY_PLAN.format(datestr=datestr)
        with open(daily_plan_file_path, "r", encoding="utf-8") as file:
            daily_plan = file.read()
        return daily_plan
    
    def change_daily_plan(self, datetime: datetime, plan_change: str):
        prompt = FileManager.read(FilePath.PROMPT_CHANGE_PLAN)
        today_schedule = self.get_daily_plan(datetime)
        input_str = "\n\n".join([f"今日の予定：\n{today_schedule}", 
                                 f"以下の予定表を今日の予定に基づいて、変更してください：\n {plan_change}"])
        new_plan = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                    self.adapter.create_message('user', input_str)])
        self.update_daily_plan(datetime, new_plan)
        return new_plan