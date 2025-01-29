# VLifeシステムの実装
from dotenv import load_dotenv
import scripts.utils.helpers as helpers
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.adapters.twitter_adapter import TwitterAdapter
from scripts.world_simulation.world_time import WorldTime
from scripts.world_simulation.daily_planner import DailyPlanner
from scripts.world_simulation.school import School
from scripts.commands.queries import Queries
from scripts.commands.action_manager import ActionManager
from scripts.memory.sensory_memory import SensoryMemory
from scripts.adapters.hatena_entry_adapter import HatenaEntryAdapter
from scripts.adapters.discord_adapter import DiscordBot
from scripts.adapters.yahoo_news_adapter import YahooNews
from scripts.memory.memo import Memo

import asyncio
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
        self.action_manager = ActionManager(adapter=self.openai_adapter, vlife=self)
        self.sensory_memory = SensoryMemory()
        self.twitter_adapter = TwitterAdapter()
        self.hatena_entry_adapter = HatenaEntryAdapter()
        self.discord_adapter = DiscordBot()
        self.yahoo_news = YahooNews()
        self.memo = Memo()

    async def start(self):
        # 年間スケジュールを作成する。4月1日になったら自動的に新しいスケジュールを作成する
        self.school.make_year_schedule(year=self.world_time.current_time.year)
        # 一日の計画を立てる。一日の計画の更新は自動的ではなく、コマンド：起きるところから始める
        self.daily_planner.make_daily_plan(day=self.world_time.current_time.day)
        # システムを開始
        while True:
            await self.action_manager.take_action()
            await asyncio.sleep(1)  # Add a small delay to avoid busy-waiting

if __name__ == '__main__':
    load_dotenv()
    vlife = VLife()
    asyncio.run(vlife.start())