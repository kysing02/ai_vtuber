from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.world_simulation.world_time import WorldTime
from scripts.commands.queries import Queries
from datetime import datetime
import os

class DailyPlanner:
    def __init__(self, adapter: OpenAIAdapter, queries: Queries):
        self.adapter = adapter
        self.queries = queries

    def make_daily_plan(self, datetime: datetime):
        datestr = datetime.strftime("%Y%m%d")
        daily_plan_file_path = f"storage/daily_plan/{datestr}.txt"
        if os.path.exists(daily_plan_file_path):
            print("一日の予定表が既に存在しているため再生成しない。")
            return
        prompt_template_path = "storage/airi/daily_planner.txt"
        with open(prompt_template_path) as file:
            prompt_template = file.read()
        prompt = self.queries.parse(prompt_template)
        message = [self.adapter.create_message('system', prompt),
                   self.adapter.create_message('user', "情報に基づいて、今日の予定を作ろう。")]
        daily_plan = self.adapter.chat_completions(message)
        with open(daily_plan_file_path) as file:
            file.write(daily_plan)