# VLifeシステムの実装
from dotenv import load_dotenv
import scripts.utils.helpers as helpers
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.world_simulation.world_time import WorldTime
from scripts.world_simulation.daily_planner import DailyPlanner
from scripts.commands.queries import Queries
from scripts.commands.actions import Actions
from scripts.world_simulation.school import School

class VLife:
    def __init__(self):
        self.config = helpers.load_config("config.yaml")
        self.openai_adapter = OpenAIAdapter()
        self.world_time = WorldTime(adapter=self.openai_adapter,
                                   start_time=self.config["world_simulations"]["start_time"],
                                   time_step=self.config["world_simulations"]["time_step"])
        self.school = School(world_time=self.world_time, adapter=self.openai_adapter)
        self.queries = Queries(adapter=self.openai_adapter, vlife=self)
        self.daily_planner = DailyPlanner(adapter=self.openai_adapter, queries=self.queries)
        self.actions = Actions(adapter=self.openai_adapter, vlife=self)

    def __start(self):
        # 年間スケジュールを作成する。4月1日になったら自動的に新しいスケジュールを作成する
        self.school.make_year_schedule(year=self.world_time.current_time.year)
        # 一日の計画を立てる。一日の計画の更新は自動的ではなく、コマンド：起きるところから始める
        self.daily_planner.make_daily_plan(day=self.world_time.current_time.day)
        # システムを開始
        while True:
            self.actions.take_action()

if __name__ == '__main__':
    load_dotenv()
    vlife = VLife()
    vlife.__start()