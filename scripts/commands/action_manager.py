from abc import ABC, abstractmethod
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.VLife import VLife
from scripts.memory.sensory_memory import SensoryMemory
from scripts.commands.action_manager import ActionManager
from typing_extensions import TypedDict
from enum import Enum

# アクションはAIVTuber向けインターフェース

class Action(ABC):
    def __init__(self, name: str, description: str, vlife: VLife, realtime=False):
        self.name = name
        self.description = description
        self.realtime = realtime
        self.sensory_memory = vlife.sensory_memory
        self.action_manager = vlife.action_manager
        self.vlife = vlife

    @abstractmethod
    async def execute(self):
        """Define what happens when this action is executed."""
        pass

    async def end(self):
        raise NotImplementedError

class PostTwitterAction(Action):
    async def execute(self):
        self.sensory_memory.add("アイリがTwitterを開いた。")
        content = self.action_manager.ask("Twitterを開いた。投稿する内容を書いてください：")
        twitter = self.vlife.twitter_adapter
        twitter.post_tweet(content)
        self.sensory_memory.add(f"アイリがTwitterをポストした。内容は「{content}」")

class WriteDiaryAction(Action):
    async def execute(self):
        self.sensory_memory.add("アイリが日記を書き始めた。")
        title = self.action_manager.ask("日記を開いた。まずタイトルを書いてください：")
        content = self.action_manager.ask("日記のタイトルを書いた。次はその内容を書いてください：")
        diary = self.vlife.hatena_entry_adapter
        diary.post(title, content)
        self.sensory_memory.add(f"アイリが日記を書いた。タイトルは「{title}」内容は「{content}」")

class EnterDiscordAction(Action):
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.set_online()
        self.sensory_memory.add("アイリがDiscordに入った。")

class LeaveDiscordAction(Action):
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.set_invisible()
        self.sensory_memory.add("アイリがDiscordから出た。")

class EnterDiscordVoiceChatAction(Action):
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.join_voice_chat()
        self.sensory_memory.add("アイリがDiscordのボイスチャットに入った。")
    
class LeaveDiscordVoiceChatAction(Action):
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.leave_voice_chat()
        self.sensory_memory.add("アイリがDiscordのボイスチャットから出た。")
    
class ReadNewsAction(Action):
    async def execute(self):
        self.sensory_memory.add("アイリがYahooニュースを読み始めた。")
        yahoo_news = self.vlife.yahoo_news
        trendings = yahoo_news.trendings(10)
        article_list_str = ""
        for idx, article in enumerate(trendings, 1):
            article_list_str += f"{idx}. {article.title}\n{article.link}\n"
            print(article_list_str)
        interested_article_id = int(self.action_manager.ask("Yahooニュースを開いた。興味のあるタイトルを数字で一つ選んでください：(1-10)"))
        

PREDEFINED_ACTIONS = [
    {
        "name": "STREAMING",
        "description": "パソコンを使って、ライブ配信を開始する。",
        "realtime": True
    },
    {
        "name": "POST_TWITTER",
        "description": "Twitterに新しい投稿をする。",
        "action": PostTwitterAction
    },
    {
        "name": "DIARY_WRITING",
        "description": "ブログを開いて、日記を書く。"
    },
    {
        "name": "ENTER_DISCORD",
        "description": "Discordに入る。",
        "realtime": True
    },
    {
        "name": "LEAVE_DISCORD",
        "description": "Discordから出る",
        "realtime": True
    },
    {
        "name": "ENTER_DISCORD_VOICE_CHAT",
        "description": "Discordのボイスチャットに入る。先にDiscordに入る必要がある。",
        "realtime": True
    },
    {
        "name": "EXIT_DISCORD_VOICE_CHAT",
        "description": "Discordのボイスチャットから出る。先にDiscordのボイスチャットに入っている必要がある。"
    },
    {
        "name": "READ_NEWS",
        "description": "Yahoo新聞を開いて、今トップランキングの新聞を読む。"
    },
    {
        "name": "SEARCH_NEWS",
        "descriptions": "Yahoo新聞を開いて、キーワードから新聞を検索する。"
    },
    {
        "name": "MAKE_MEMO",
        "description": "大事なことを忘れないように、スマホアプリで記録する"
    },
    {
        "name": "READ_MEMO",
        "description": "大事なことを忘れないように書いたメモを、スマホアプリから開く"
    },
    {
        "name": "CHECK_SCHOOL_EVENTS",
        "description": "学校の行事表を見る"
    },
    {
        "name": "CHECK_TIMETABLE",
        "description": "学校の時間割を開く"
    },
    {
        "name": "CHANGE_TODAY_PLAN",
        "description": "今日の予定を変更する"
    },
    {
        "name": "CHECK_DATETIME",
        "description": "今の時間と日付を確認する"
    },
    {
        "name": "SLEEP_TILL_TOMORROW",
        "description": "明日まで寝る"
    },
    # {
    #     "name": "LINE_CHAT_DEVELOPER",
    #     "description": "アイリの開発者にLINEを送信する"
    # },
    # {
    #     "name": "LINE_CHECK_DEVELOPER_CHAT",
    #     "description": "開発者とのLINEチャット記録を見る"
    # }
]

EXAMPLE_ACTIONS = [
    {
        "name": "GO_CAFE",
        "description": "喫茶店に行く"
    },
    {
        "name": "READ_BOOKS",
        "description": "本を読む"
    },
    {
        "name": "FOOD_HUNT",
        "description": "料理店巡りをする"
    },
]

class ActionManager:
    def __init__(self, vlife: VLife):
        self.vlife = vlife
        self.queries = vlife.queries
        self.adapter = vlife.openai_adapter
        self.all_actions = PREDEFINED_ACTIONS.append(self.__load_saved_actions())
    
    def get_available_actions():
        raise NotImplementedError
    
    def parse(text: str):
        raise NotImplementedError

    def execute_actions(self, action_name: str):
        raise NotImplementedError
    
    def create_new_action():
        raise NotImplementedError
    
    async def take_action(self):
        # 今、一番したいことは？
        prompt = self.queries.load_prompt_from_file("storage/commands/actions.txt")
        decision = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', "一番したいこと:")])
        # 今の考えを整理しよう

        
        # 対応するコマンドを実行してください
        prompt = self.queries.load_prompt_from_file("storage/commands/commands.txt")
        command_list = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', decision)])
        
        # 対応するコマンドに応じて行動を取る
        action_list = self.parse(command_list)