import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scripts.vlife import VLife

class Action(ABC):
    name = None
    description = None
    realtime = False

    def __init__(self, vlife: "VLife"):
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

class ActEnterDiscord(Action):
    name = "!ENTER_DISCORD"
    description = "Discordに入る。"
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.set_online()
        self.short_term_memory.add("アイリがDiscordに入った。")

class ActLeaveDiscord(Action):
    name = "!LEAVE_DISCORD"
    description = "Discordから出る"
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.set_invisible()
        self.short_term_memory.add("アイリがDiscordから出た。")

class ActEnterDiscordVoiceChat(Action):
    name = "!ENTER_DISCORD_VOICE_CHAT"
    description = "Discordのボイスチャットに入る。先にDiscordに入る必要がある。"
    realtime = True
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.join_voice_chat()
        self.short_term_memory.add("アイリがDiscordのボイスチャットに入った。")

class ActLeaveDiscordVoiceChat(Action):
    name = "!LEAVE_DISCORD_VOICE_CHAT"
    description = "Discordのボイスチャットから出る。先にDiscordのボイスチャットに入っている必要がある。"
    async def execute(self):
        discord = self.vlife.discord_adapter
        await discord.leave_voice_chat()
        self.short_term_memory.add("アイリがDiscordのボイスチャットから出た。")

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

class ActSearchNews(Action):
    name = "!SEARCH_NEWS"
    description = "Yahoo新聞を開いて、キーワードから新聞を検索する。"
    async def execute(self):
        self.short_term_memory.add("アイリがYahooニュースの検索機能を使った。")
        yahoo_news = self.vlife.yahoo_news
        selected_topic = self.action_manager.ask("Yahooニュースを開いた。検索キーワードを入力してください：")
        if not selected_topic:
            self.short_term_memory.add("検索結果がありませんでした。")

class ActMakeMemo(Action):
    name = "!MAKE_MEMO"
    description = "大事なことを忘れないように、スマホアプリで記録する"
    async def execute(self):
        self.short_term_memory.add("アイリがスマホアプリにメモを書いた。")
        memo = self.vlife.memo
        content = self.action_manager.ask("メモアプリを開いた。なにを記録しますか？")
        memo.write_memo(content)
        self.short_term_memory.add(f"アイリがスマホアプリでメモをした：\n{content}")

class ActReadMemo(Action):
    name = "!READ_MEMO"
    description = "大事なことを忘れないように書いたメモを、スマホアプリから開く"
    async def execute(self):
        memo = self.vlife.memo
        memo_list_str = "\n".join(memo.read_memo(10))
        self.short_term_memory.add(f"アイリがスマホアプリでメモを開いた：\n{memo_list_str}")

class ActCheckSchoolEvents(Action):
    name = "!CHECK_SCHOOL_EVENTS"
    description = "学校の行事表を見る"
    async def execute(self):
        school = self.vlife.school
        school_events = school.get_school_events_str()
        self.short_term_memory.add(f"アイリが学校の行事表を調べた：\n{school_events}")

class ActCheckTimeTable(Action):
    name = "!CHECK_TIMETABLE"
    description = "学校の時間割を開く"
    async def execute(self):
        school = self.vlife.school
        timetable = school.get_timetable_str()
        self.short_term_memory.add(f"アイリが時間割を調べた：\n{timetable}")

class ActChangeTodayPlan(Action):
    name = "!CHANGE_TODAY_PLAN"
    description =  "今日の予定を変更する"
    async def execute(self):
        plan_change = self.action_manager.ask("今日はどのように予定を変更しようか？具体的に何時何分から何時何分まで？")
        new_plan = self.vlife.daily_planner.change_daily_plan(self.vlife.world_time.current_time, plan_change)
        self.short_term_memory.add("アイリが今日の予定を変更した：\n", new_plan)

class ActCheckDateTime(Action):
    name = "!CHECK_DATETIME"
    description = "今の時間と日付を確認する"
    async def execute(self):
        self.short_term_memory.add("アイリが今の時間と日付を調べた：\n", self.vlife.world_time.get_time_str())

class ActSleepTillTomorrow(Action):
    name = "!SLEEP_TILL_TOMORROW"
    description = "明日まで寝る"
    async def execute(self):
        self.short_term_memory.add("アイリが明日まで寝た。おやすみなさい。")
        # TODO 今は固定8時間寝るが、今後は改善する
        self.vlife.world_time.proceed_time(timedelta(hours=8))
    
class ActChatDeveloper(Action):
    name = "!CHAT_DEVELOPER"
    description = "アイリの開発者、シンにチャットを送信する"
    async def execute(self):
        pass
class ActCheckDeveloperChat(Action):
    name = "!CHECK_CHAT_DEVELOPER"
    description = "アイリの開発者、シンからもらったチャットメッセージを見る"
    async def execute(self):
        pass

class ActNew(Action):
    name = "!NEW_ACTION"
    description = "新しいコマンドを作成する。コマンドの後ろに説明が必要"
    
    async def execute(self, info):
        # TODO Implement real logic
        self.short_term_memory.add("アイリが楽しい時間を過ごした：\n", info)
        await asyncio.sleep(10)

if __name__ == "__main__":
    action_list = [('!NEW_ACTION', '家に行く'), ('!NEW_ACTION', '友達と遊ぶ')]
    for action, desc in action_list:
        if action == ActNew.name:
            # 一番目のアクションだけ実行する
            print("Action detected")
        else:
            # すべてのコマンドを実行する
            print("Not detected")