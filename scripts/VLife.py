# VLifeシステムの実装
import asyncio
from dotenv import load_dotenv
import scripts.utils.helpers as helpers
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.adapters.twitter_adapter import TwitterAdapter
from scripts.world_simulation.world_time import WorldTime
from scripts.world_simulation.school import School
from scripts.memory.memo import Memo
from scripts.adapters.hatena_entry_adapter import HatenaEntryAdapter
from scripts.adapters.yahoo_news_adapter import YahooNews
from scripts.file_manager import FileManager, FilePath
from scripts.sound.voice_chat import VoiceChat
from scripts.memory.memory import ShortTermMemory, LongTermMemory
from scripts.adapters.discord_adapter import DiscordBot
from scripts.memory.reflection import Reflection
from scripts.commands.queries import Queries
from scripts.world_simulation.daily_planner import DailyPlanner
from scripts.commands.action_manager import ActionManager
from scripts.sound.VoiceMaker import VoiceMaker, StyleBertVits2Adapter, VoicevoxAdapter
from scripts.sound.play_sound import PlaySound
from scripts.adapters.vtube_studio_adapter import VTSAdapter
from scripts.adapters.obs_adapter import OBSAdapter
from scripts.world_simulation.narrator import Narrator

class VLife:
    def __init__(self):
        # self.config = helpers.load_config("config.yaml")
        self.openai_adapter = OpenAIAdapter()
        self.world_time = WorldTime(adapter=self.openai_adapter)
        self.school = School(world_time=self.world_time, adapter=self.openai_adapter)
        self.obs = OBSAdapter()
        self.vits2 = StyleBertVits2Adapter()
        self.voicevox = VoicevoxAdapter()
        self.play_sound = PlaySound("CABLE Input")
        self.vts = VTSAdapter()
        self.long_term_memory = LongTermMemory(self.openai_adapter)
        self.narrator = Narrator(self.vits2, self.voicevox, self.vts, self.play_sound, self.obs)
        self.short_term_memory = ShortTermMemory(self.world_time, self.long_term_memory, self.openai_adapter, self.narrator)
        self.twitter_adapter = TwitterAdapter()
        self.hatena_entry_adapter = HatenaEntryAdapter()
        self.voice_maker = VoiceMaker()
        self.yahoo_news = YahooNews()
        self.memo = Memo()
        self.queries = Queries(vlife=self)
        self.daily_planner = DailyPlanner(adapter=self.openai_adapter, queries=self.queries)
        self.reflection = Reflection(self.openai_adapter, self.queries)
        self.action_manager = ActionManager(vlife=self)
        self.voice_chat = VoiceChat(
            adapter=self.openai_adapter,
            vits2=self.vits2,
            play_sound=self.play_sound,
            vts=self.vts,
            action_manager=self.action_manager,
            memory=self.short_term_memory,
            queries=self.queries
        )
        self.discord = DiscordBot(self.voice_chat, self.openai_adapter, self.short_term_memory, self.action_manager)
        self.discord.run_bot_in_thread()

    async def start(self):
        await self.vts.connect_auth()
        # 年間スケジュールを作成する。4月1日になったら自動的に新しいスケジュールを作成する
        self.school.make_year_schedule(year=self.world_time.current_time.year)
        # 一日の計画を立てる。一日の計画の更新は自動的ではなく、コマンド：起きるところから始める
        self.daily_planner.make_daily_plan(datetime=self.world_time.current_time)
        await self.short_term_memory.add("アイリが今日の予定を立てた。")
        # システムを開始
        while True:
            await self.action_manager.take_action()
            await asyncio.sleep(1)  # Add a small delay to avoid busy-waiting

    @staticmethod
    def get_profile():
        profile = FileManager.read(FilePath.TEXT_PROFILE)
        return profile

async def main():
    load_dotenv()
    vlife = VLife()
    await vlife.start()

if __name__ == "__main__":
    asyncio.run(main())  # Use

# if __name__ == '__main__':
#     load_dotenv()
#     loop = asyncio.get_event_loop()
#     vlife = VLife()
#     loop.run_until_complete(vlife.start())