import re
from abc import ABC, abstractmethod
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.vlife import VLife
from scripts.memory.memory import ShortTermMemory
from scripts.commands.action_manager import ActionManager
from typing_extensions import TypedDict
from enum import Enum
from file_manager import FilePath
from datetime import datetime, timedelta
# アクションはAIVTuber向けインターフェース

class Action(ABC):
    name = None
    description = None
    realtime = False

    def __init__(self, vlife: VLife):
        self.short_term_memory = vlife.short_term_memory
        self.action_manager = vlife.action_manager
        self.vlife = vlife
        self.adapter = vlife.openai_adapter
        self.time_start = datetime.now()
        if Action.realtime:
            self.vlife.world_time.pause()

    @abstractmethod
    async def execute(self):
        """Define what happens when this action is executed."""
        pass

    async def end(self):
        # リアルタイムの行動（例.ボイスチャットなど）は、現実世界の時間を使用する
        if self.realtime:
            time_diff = datetime.now() - self.time_start
            # バーチャル世界の時間に整定するために、秒とマイクロ秒は省略
            time_diff.seconds = 0
            time_diff.microseconds = 0 
            self.vlife.world_time.proceed_time(timedelta)
            self.vlife.world_time.resume()
        

class ActStreaming(Action):
    name = "!STREAMING"
    description = "パソコンを使って、ライブ配信を開始する。"
    realtime = True
    async def execute(self):
        pass

class ActPostTwitter(Action):
    name = "!POST_TWITTER"
    description = "Twitterに新しい投稿をする。"
    async def execute(self):
        self.short_term_memory.add("アイリがTwitterを開いた。")
        content = self.action_manager.ask("Twitterを開いた。投稿する内容を書いてください：")
        twitter = self.vlife.twitter_adapter
        twitter.post_tweet(content)
        self.short_term_memory.add(f"アイリがTwitterをポストした。内容は「{content}」")
        await self.end()

class ActWriteDiary(Action):
    name = "!WRITE_DIARY"
    description = "ブログを開いて、日記を書く。"
    async def execute(self):
        self.short_term_memory.add("アイリが日記を書き始めた。")
        title = self.action_manager.ask("日記を開いた。まずタイトルを書いてください：")
        content = self.action_manager.ask("日記のタイトルを書いた。次はその内容を書いてください：")
        diary = self.vlife.hatena_entry_adapter
        diary.post(title, content)
        self.short_term_memory.add(f"アイリが日記を書いた。タイトルは「{title}」内容は「{content}」")
        await self.end()

class ActEnterDiscord(Action):
    name = "!ENTER_DISCORD"
    description = "Discordに入る。"
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.set_online()
        self.short_term_memory.add("アイリがDiscordに入った。")
        await self.end()

class ActLeaveDiscord(Action):
    name = "!LEAVE_DISCORD"
    description = "Discordから出る"
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.set_invisible()
        self.short_term_memory.add("アイリがDiscordから出た。")
        await self.end()

class ActEnterDiscordVoiceChat(Action):
    name = "!ENTER_DISCORD_VOICE_CHAT"
    description = "Discordのボイスチャットに入る。先にDiscordに入る必要がある。"
    realtime = True
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.join_voice_chat()
        self.short_term_memory.add("アイリがDiscordのボイスチャットに入った。")
        await self.end()

class ActLeaveDiscordVoiceChat(Action):
    name = "!LEAVE_DISCORD_VOICE_CHAT"
    description = "Discordのボイスチャットから出る。先にDiscordのボイスチャットに入っている必要がある。"
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.leave_voice_chat()
        self.short_term_memory.add("アイリがDiscordのボイスチャットから出た。")
        await self.end()

class ActReadNews(Action):
    name = "!READ_NEWS"
    description = "Yahoo新聞を開いて、今トップランキングの新聞を読む。"
    async def execute(self):
        self.short_term_memory.add("アイリがYahooニュースを読み始めた。")
        yahoo_news = self.vlife.yahoo_news
        trendings = yahoo_news.trendings(10)
        if not trendings:
            self.short_term_memory.add("新しいニュースがありませんでした。")
        article_list_str = ""
        for idx, article in enumerate(trendings, 1):
            article_list_str += f"{idx}. {article.title}\n{article.link}\n"
            print(article_list_str)
        selected_id = int(self.action_manager.ask("Yahooニュースを開いた。興味のあるタイトルを数字で一つ選んでください：(1-10)"))
        content = yahoo_news.get_article_content(trendings[selected_id-1])
        if not content:
            self.short_term_memory.add("ニュースのリンクを開けませんでした。")
        self.short_term_memory.add(f"アイリがニュースを読んだ：\nタイトル：{trendings[selected_id-1].title}\n内容：{content}")
        await self.end()

class ActSearchNews(Action):
    name = "!SEARCH_NEWS"
    description = "Yahoo新聞を開いて、キーワードから新聞を検索する。"
    async def execute(self):
        self.short_term_memory.add("アイリがYahooニュースの検索機能を使った。")
        yahoo_news = self.vlife.yahoo_news
        selected_topic = self.action_manager.ask("Yahooニュースを開いた。検索キーワードを入力してください：")
        if not selected_topic:
            self.short_term_memory.add("検索結果がありませんでした。")
        await self.end()

class ActMakeMemo(Action):
    name = "!MAKE_MEMO"
    description = "大事なことを忘れないように、スマホアプリで記録する"
    async def execute(self):
        self.short_term_memory.add("アイリがスマホアプリにメモを書いた。")
        memo = self.vlife.memo
        content = self.action_manager.ask("メモアプリを開いた。なにを記録しますか？")
        memo.write_memo(content)
        self.short_term_memory.add("アイリがスマホアプリでメモをした：", content)
        await self.end()

class ActReadMemo(Action):
    name = "!READ_MEMO"
    description = "大事なことを忘れないように書いたメモを、スマホアプリから開く"
    async def execute(self):
        memo = self.vlife.memo
        memo_list_str = "\n".join(memo.read_memo(10))
        self.short_term_memory.add("アイリがスマホアプリでメモを開いた：\n", memo_list_str)
        await self.end()

class ActCheckSchoolEvents(Action):
    name = "!CHECK_SCHOOL_EVENTS"
    description = "学校の行事表を見る"
    async def execute(self):
        school = self.vlife.school
        school_events = school.get_school_events_str()
        self.short_term_memory.add("アイリが学校の行事表を調べた：\n", school_events)
        await self.end()

class ActCheckTimeTable(Action):
    name = "!CHECK_TIMETABLE"
    description = "学校の時間割を開く"
    async def execute(self):
        school = self.vlife.school
        timetable = school.get_timetable_str()
        self.short_term_memory.add("アイリが時間割を調べた：\n", timetable)
        await self.end()

class ActChangeTodayPlan(Action):
    name = "!CHANGE_TODAY_PLAN"
    description =  "今日の予定を変更する"
    async def execute(self):
        plan_change = self.action_manager.ask("今日はどのように予定を変更しようか？具体的に何時何分から何時何分まで？")
        new_plan = self.vlife.daily_planner.change_daily_plan(self.vlife.world_time.current_time, plan_change)
        self.short_term_memory.add("アイリが今日の予定を変更した：\n", new_plan)
        await self.end()

class ActCheckDateTime(Action):
    name = "!CHECK_DATETIME"
    description = "今の時間と日付を確認する"
    async def execute(self):
        self.short_term_memory.add("アイリが今の時間と日付を調べた：\n", self.vlife.world_time.get_time_str())
        await self.end()

class ActSleepTillTomorrow(Action):
    name = "!SLEEP_TILL_TOMORROW"
    description = "明日まで寝る"
    async def execute(self):
        self.short_term_memory.add("アイリが明日まで寝た。おやすみなさい。")
        await self.end()

class ActChatDeveloper(Action):
    name = "!CHAT_DEVELOPER"
    description = "アイリの開発者、シンにチャットを送信する"
    async def execute(self):
        await self.end()
    
class ActCheckDeveloperChat(Action):
    name = "!CHECK_CHAT_DEVELOPER"
    description = "アイリの開発者、シンからもらったチャットメッセージを見る"
    async def execute(self):
        await self.end()
    
class ActNew(Action):
    name = "!NEW_ACTION"
    description = "新しいコマンドを作成する。コマンドの後ろに説明が必要"
    
    async def execute(self, info):
        await self.end()

class ActionManager:
    PREDEFINED_ACTIONS: list[Action] = [
        # ActStreaming,
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
        # ActChatDeveloper,
        # ActCheckDeveloperChat,
        ActNew
    ]
    
    def __init__(self, vlife: VLife):
        self.vlife = vlife
        self.queries = vlife.queries
        self.adapter = vlife.openai_adapter
        self.all_actions = ActionManager.PREDEFINED_ACTIONS.append(self.__load_saved_actions())

    def get_available_actions_str():
        available_actions = "今実行できるコマンドのリスト：\n"
        for action in ActionManager.PREDEFINED_ACTIONS:
            available_actions = available_actions + f"{action.name} : {action.description}\n"
        return available_actions
    
    def parse(text: str):
        # Regular expression to match commands
        command_pattern = re.compile(r'\{!(.*?)\}')
        
        # Find all commands in the input string
        commands = command_pattern.findall(text)
        
        # List to store the final result as (command, description)
        result = []
        
        for command in commands:
            # Split the command into name and description (if any)
            if " " in command:
                # Split into command name and description
                command_name, description = command.split(maxsplit=1)
                result.append((f"!{command_name}", description))
            else:
                # If no description, set description to empty string
                result.append((f"!{command}", ""))
        
        return result

    def execute_actions(self, action_name: str):
        raise NotImplementedError
    
    def create_new_action():
        raise NotImplementedError
    
    async def take_action(self):
        # 今の考えを整理しよう
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_THOUGHT)
        thought = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                                 self.adapter.create_message('user', "今考えていること:")])
        print("[SYSTEM]アイリが今考えていること：", thought)

        # 今、一番したいことは？
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_ACT)
        decision = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', "一番したいこと:")])
        print("[SYSTEM]アイリが今一番したいこと：", decision)
        # 対応するコマンドを実行してください
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_ACT_PROCESS)
        command_list = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', decision)])
        print("[SYSTEM]検出されたコマンド：", command_list)

        # 対応するコマンドに応じて行動を取る
        action_list = self.parse(command_list)
        for action, desc in action_list:
            if action == ActNew.name:
                # 一番目のアクションだけ実行する
                perform = ActNew(self.vlife)
                await perform.execute(desc)
            else:
                # すべてのコマンドを実行する
                for predefined_act in ActionManager.PREDEFINED_ACTIONS:
                    if action == predefined_act.name:
                        perform: Action = predefined_act(self.vlife)
                        await perform.execute()

    def ask(self):
        raise NotImplementedError