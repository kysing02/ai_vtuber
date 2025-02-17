import asyncio
import logging
import threading
from dotenv import load_dotenv
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.adapters.twitter_adapter import TwitterAdapter
from scripts.adapters.hatena_entry_adapter import HatenaEntryAdapter
from scripts.adapters.yahoo_news_adapter import YahooNews
from scripts.adapters.vtube_studio_adapter import VTSAdapter
from scripts.adapters.obs_adapter import OBSAdapter
from scripts.adapters.discord_adapter import DiscordBot
from scripts.commands.queries import Queries
from scripts.commands.action_manager import ActionManager
from scripts.file_manager import FileManager, FilePath
from scripts.memory.memo import Memo
from scripts.memory.memory import ShortTermMemory, LongTermMemory
from scripts.memory.reflection import Reflection
from scripts.sound.voice_chat import VoiceChat
from scripts.sound.VoiceMaker import VoiceMaker, StyleBertVits2Adapter, VoicevoxAdapter
from scripts.sound.play_sound import PlaySound
from scripts.world_simulation.world_time import WorldTime
from scripts.world_simulation.school import School
from scripts.world_simulation.daily_planner import DailyPlanner
from scripts.world_simulation.narrator import Narrator

class VLife:
    """VLifeシステムの実装を行う。ここはプログラムのエントリーポイントになっている。
    """
    def __init__(self):
        # TODO Config設定ファイルをロードする
        # self.config = helpers.load_config("config.yaml")

        # 使用するモジュールをすべて初期化する
        self.openai_adapter = OpenAIAdapter()
        self.world_time = WorldTime(adapter=self.openai_adapter, loop=asyncio.get_running_loop())
        self.school = School(world_time=self.world_time, adapter=self.openai_adapter)
        self.obs = OBSAdapter()
        self.vits2 = StyleBertVits2Adapter()
        self.voicevox = VoicevoxAdapter()
        self.play_sound_narrator = PlaySound(output_device_name="Headphones")
        self.play_sound_airi = PlaySound(output_device_name="CABLE Input")
        self.vts = VTSAdapter()
        self.long_term_memory = LongTermMemory(self.openai_adapter)
        self.narrator = Narrator(self.vits2, self.voicevox, self.vts, self.play_sound_narrator, self.play_sound_airi, self.obs)
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
            play_sound=self.play_sound_airi,
            action_manager=self.action_manager,
            memory=self.short_term_memory,
            queries=self.queries,
            obs=self.obs,
            vts=self.vts
        )
        self.discord = DiscordBot(self.voice_chat, self.openai_adapter, self.short_term_memory, self.action_manager)

    async def start(self):
        """
        初期状態を設定し、VLifeシステムを開始する。
        ここではすべてのループとタスクを管理する。
        """
        # Discordの接続と認証を行う
        discord_task = asyncio.create_task(self.discord.connect_auth())
        # Discordが準備完了の状態まで待つ
        await self.discord.wait_until_ready()
        # VTube Studioの接続と認証を行う
        await self.vts.connect_auth()

        # WorldTimeの時間進行スレッドを開始する
        proceed_time_thread = threading.Thread(target=self.world_time.proceed_time_in_background, daemon=True).start()

        # 年間スケジュールを作成する。(4月1日になったら自動的に新しいスケジュールを作成する)
        self.school.make_year_schedule()
        # 一日の計画を立てる。(一日の計画の更新は自動的ではなく、コマンド：!SLEEP_TILL_TOMORROWのところから始める)
        self.daily_planner.make_daily_plan(datetime=self.world_time.current_time)
        await self.short_term_memory.add("(アイリが今日の予定を立てた。)")

        # システムを開始
        while True:
            await self.action_manager.take_action()
            await asyncio.sleep(0.1)  # 無限待機を避けるために少し遅延を設定する

    @staticmethod
    def get_profile():
        """
        AIriに関するプロフィールを取得する。

        Returns:
            str: AIriのプロフィール
        """
        profile = FileManager.read(FilePath.TEXT_PROFILE)
        return profile

async def main():
    # システム環境変数を読み込む
    load_dotenv()

    # ログレベルをINFOにする
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-6s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%m-%d %H:%M:%S"
    )

    # VLifeシステムを開始する
    vlife = VLife()
    await vlife.start()

if __name__ == "__main__":
    asyncio.run(main())