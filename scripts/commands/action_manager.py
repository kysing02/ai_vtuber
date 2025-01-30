from abc import ABC, abstractmethod
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.vlife import VLife
from scripts.memory.sensory_memory import SensoryMemory
from scripts.commands.action_manager import ActionManager
from typing_extensions import TypedDict
from enum import Enum
from file_manager import FilePath
# アクションはAIVTuber向けインターフェース

class Action(ABC):
    name = None
    description = None
    realtime = False

    def __init__(self, vlife: VLife):
        self.sensory_memory = vlife.sensory_memory
        self.action_manager = vlife.action_manager
        self.vlife = vlife
        self.adapter = vlife.openai_adapter

    @abstractmethod
    async def execute(self):
        """Define what happens when this action is executed."""
        pass

    async def end(self):
        raise NotImplementedError

class ActStreaming(Action):
    name = "!STREAMING"
    description = "パソコンを使って、ライブ配信を開始する。"
    realtime = True

class ActPostTwitter(Action):
    name = "!POST_TWITTER"
    description = "Twitterに新しい投稿をする。"

    async def execute(self):
        self.sensory_memory.add("アイリがTwitterを開いた。")
        content = self.action_manager.ask("Twitterを開いた。投稿する内容を書いてください：")
        twitter = self.vlife.twitter_adapter
        twitter.post_tweet(content)
        self.sensory_memory.add(f"アイリがTwitterをポストした。内容は「{content}」")

class ActWriteDiary(Action):
    name = "!WRITE_DIARY"
    description = "ブログを開いて、日記を書く。"
    
    async def execute(self):
        self.sensory_memory.add("アイリが日記を書き始めた。")
        title = self.action_manager.ask("日記を開いた。まずタイトルを書いてください：")
        content = self.action_manager.ask("日記のタイトルを書いた。次はその内容を書いてください：")
        diary = self.vlife.hatena_entry_adapter
        diary.post(title, content)
        self.sensory_memory.add(f"アイリが日記を書いた。タイトルは「{title}」内容は「{content}」")

class ActEnterDiscord(Action):
    name = "!ENTER_DISCORD"
    description = "Discordに入る。"

    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.set_online()
        self.sensory_memory.add("アイリがDiscordに入った。")

class ActLeaveDiscord(Action):
    name = "!LEAVE_DISCORD"
    description = "Discordから出る"

    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.set_invisible()
        self.sensory_memory.add("アイリがDiscordから出た。")

class ActEnterDiscordVoiceChat(Action):
    name = "!ENTER_DISCORD_VOICE_CHAT"
    description = "Discordのボイスチャットに入る。先にDiscordに入る必要がある。"

    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.join_voice_chat()
        self.sensory_memory.add("アイリがDiscordのボイスチャットに入った。")
    
class ActLeaveDiscordVoiceChat(Action):
    name = "!LEAVE_DISCORD_VOICE_CHAT"
    description = "Discordのボイスチャットから出る。先にDiscordのボイスチャットに入っている必要がある。"

    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.leave_voice_chat()
        self.sensory_memory.add("アイリがDiscordのボイスチャットから出た。")
    
class ActReadNews(Action):
    name = "!READ_NEWS"
    description = "Yahoo新聞を開いて、今トップランキングの新聞を読む。"

    async def execute(self):
        self.sensory_memory.add("アイリがYahooニュースを読み始めた。")
        yahoo_news = self.vlife.yahoo_news
        trendings = yahoo_news.trendings(10)
        if not trendings:
            self.sensory_memory.add("新しいニュースがありませんでした。")
        article_list_str = ""
        for idx, article in enumerate(trendings, 1):
            article_list_str += f"{idx}. {article.title}\n{article.link}\n"
            print(article_list_str)
        selected_id = int(self.action_manager.ask("Yahooニュースを開いた。興味のあるタイトルを数字で一つ選んでください：(1-10)"))
        content = yahoo_news.get_article_content(trendings[selected_id-1])
        if not content:
            self.sensory_memory.add("ニュースのリンクを開けませんでした。")
        self.sensory_memory.add(f"アイリがニュースを読んだ：\nタイトル：{trendings[selected_id-1].title}\n内容：{content}")   

class ActSearchNews(Action):
    name = "!SEARCH_NEWS"
    description = "Yahoo新聞を開いて、キーワードから新聞を検索する。"

    async def execute(self):
        self.sensory_memory.add("アイリがYahooニュースの検索機能を使った。")
        yahoo_news = self.vlife.yahoo_news
        selected_topic = self.action_manager.ask("Yahooニュースを開いた。検索キーワードを入力してください：")
        if not selected_topic:
            self.sensory_memory.add("検索結果がありませんでした。")

class ActMakeMemo(Action):
    name = "!MAKE_MEMO"
    description = "大事なことを忘れないように、スマホアプリで記録する"

    async def execute(self):
        self.sensory_memory.add("アイリがスマホアプリにメモを書いた。")
        memo = self.vlife.memo
        content = self.action_manager.ask("メモアプリを開いた。なにを記録しますか？")
        memo.write_memo(content)
        self.sensory_memory.add("アイリがスマホアプリでメモをした：", content)

class ActReadMemo(Action):
    name = "!READ_MEMO"
    description = "大事なことを忘れないように書いたメモを、スマホアプリから開く"

    async def execute(self):
        memo = self.vlife.memo
        memo_list_str = "\n".join(memo.read_memo(10))
        self.sensory_memory.add("アイリがスマホアプリでメモを開いた：\n", memo_list_str)
        
class ActCheckSchoolEvents(Action):
    name = "!CHECK_SCHOOL_EVENTS"
    description = "学校の行事表を見る"

    async def execute(self):
        school = self.vlife.school
        school_events = school.get_school_events_str()
        self.sensory_memory.add("アイリが学校の行事表を調べた：\n", school_events)

class ActCheckTimeTable(Action):
    name = "!CHECK_TIMETABLE"
    description = "学校の時間割を開く"

    async def execute(self):
        school = self.vlife.school
        timetable = school.get_timetable_str()
        self.sensory_memory.add("アイリが時間割を調べた：\n", timetable)

class ActChangeTodayPlan(Action):
    name = "!CHANGE_TODAY_PLAN"
    description =  "今日の予定を変更する"

    async def execute(self):
        plan_change = self.action_manager.ask("今日はどのように予定を変更しようか？具体的に何時何分から何時何分まで？")
        new_plan = self.vlife.daily_planner.change_daily_plan(self.vlife.world_time.current_time, plan_change)
        self.sensory_memory.add("アイリが今日の予定を変更した：\n", new_plan)

class ActCheckDateTime(Action):
    name = "!CHECK_DATETIME"
    description = "今の時間と日付を確認する"

    async def execute(self):
        self.sensory_memory.add("アイリが今の時間と日付を調べた：\n", self.vlife.world_time.get_time_str())

class ActSleepTillTomorrow(Action):
    name = "!SLEEP_TILL_TOMORROW"
    description = "明日まで寝る"

    async def execute(self):
        self.sensory_memory.add("アイリが明日まで寝た。おやすみなさい。")

class ActChatDeveloper(Action):
    name = "!ACT_CHAT_DEVELOPER"
    description = "アイリの開発者、シンにチャットを送信する"

    async def execute(self):
        return await super().execute()
    
class ActCheckDeveloperChat(Action):
    name = "!ACT_CHECK_CHAT"
    description = "アイリの開発者、シンからもらったチャットメッセージを見る"

    async def execute(self):
        return await super().execute()
    
class ActNew(Action):
    async def execute(self, info):
        pass

class ActionManager:
    PREDEFINED_ACTIONS: list[Action] = [
        ActStreaming,
        ActPostTwitter,
        ActWriteDiary,
        ActEnterDiscord,
        ActLeaveDiscord,
        ActEnterDiscordVoiceChat,
        ActLeaveDiscordVoiceChat,
        ActReadNews,
        ActSearchNews,
        ActMakeMemo,
        ActReadMemo,
        ActCheckSchoolEvents,
        ActCheckTimeTable,
        ActChangeTodayPlan,
        ActCheckDateTime,
        ActSleepTillTomorrow,
        ActChatDeveloper,
        ActCheckDeveloperChat
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
    
    def __init__(self, vlife: VLife):
        self.vlife = vlife
        self.queries = vlife.queries
        self.adapter = vlife.openai_adapter
        self.all_actions = ActionManager.PREDEFINED_ACTIONS.append(self.__load_saved_actions())

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
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_COMMAND_ACTIONS)
        decision = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', "一番したいこと:")])
        # 今の考えを整理しよう
        
        
        # 対応するコマンドを実行してください
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_ACTION_PROCESS)
        command_list = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', decision)])
        
        # 対応するコマンドに応じて行動を取る
        action_list = self.parse(command_list)

    def ask(self):
        raise NotImplementedError