import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from scripts.file_manager import FilePath
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scripts.vlife import VLife
    from scripts.adapters.openai_adapter import Message

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
    description = "Twitterに新しい投稿をする。(Twitterでは投稿しかできない。誰かに話しかけるときは別の機能を使ってください)"
    async def execute(self):
        await self.short_term_memory.add("アイリがTwitterを開いた。")
        content = self.action_manager.ask("Twitterを開いた。投稿する内容を書いてください：")
        twitter = self.vlife.twitter_adapter
        twitter.post_tweet(content)
        await self.short_term_memory.add(f"アイリがTwitterをポストした。内容は「{content}」")

class ActWriteDiary(Action):
    name = "!WRITE_DIARY"
    description = "ブログを開いて、日記を書く。"
    async def execute(self):
        await self.short_term_memory.add("アイリが日記を書き始めた。")
        title = self.action_manager.ask("日記を開いた。まずタイトルを書いてください：")
        content = self.action_manager.ask("日記のタイトルを書いた。次はその内容を書いてください：")
        diary = self.vlife.hatena_entry_adapter
        diary.post(title, content)
        await self.short_term_memory.add(f"アイリが日記を書いた。タイトルは「{title}」内容は「{content}」")

class ActEnterDiscord(Action):
    name = "!ENTER_DISCORD"
    description = "Discordに入る。複数の行動がある時このコマンドをCHATよりも一番優先すること。"
    async def execute(self):
        discord = self.vlife.discord
        await discord.set_online()
        await self.short_term_memory.add("アイリがDiscordに入った。")

class ActLeaveDiscord(Action):
    name = "!LEAVE_DISCORD"
    description = "Discordから出る"
    async def execute(self):
        discord = self.vlife.discord
        await discord.set_invisible()
        await self.short_term_memory.add("アイリがDiscordから出た。")

class ActEnterDiscordVoiceChat(Action):
    name = "!ENTER_DISCORD_VOICE_CHAT"
    description = "Discordのボイスチャットに入る。先にDiscordに入る必要がある。"
    # realtime = True
    async def execute(self):
        discord = self.vlife.discord
        future = discord.schedule_task(discord.messenger.join_voice_chat())
        await asyncio.wrap_future(future)
        await self.short_term_memory.add("アイリがDiscordのボイスチャットに入った。")

class ActLeaveDiscordVoiceChat(Action):
    name = "!LEAVE_DISCORD_VOICE_CHAT"
    description = "Discordのボイスチャットから出る。先にDiscordのボイスチャットに入っている必要がある。"
    async def execute(self):
        discord = self.vlife.discord
        future = discord.schedule_task(discord.messenger.leave_voice_chat())
        await asyncio.wrap_future(future)
        await self.short_term_memory.add("アイリがDiscordのボイスチャットから出た。")

class ActReadNews(Action):
    name = "!READ_NEWS"
    description = "Yahoo新聞を開いて、今トップランキングの新聞を読む。"
    async def execute(self):
        await self.short_term_memory.add("アイリがYahooニュースを読み始めた。")
        yahoo_news = self.vlife.yahoo_news
        trendings = yahoo_news.trendings(10)
        if not trendings:
            await self.short_term_memory.add("新しいニュースがありませんでした。", narrate=False)
        article_list_str = ""
        for idx, article in enumerate(trendings, 1):
            article_list_str += f"{idx}. {article.title}\n{article.link}\n"
            print(article_list_str)
        selected_id = int(self.action_manager.ask("Yahooニュースを開いた。興味のあるタイトルを数字で一つ選んでください：(1-10)"))
        content = yahoo_news.get_article_content(trendings[selected_id-1])
        if not content:
            await self.short_term_memory.add("ニュースのリンクを開けませんでした。", narrate=False)
        await self.short_term_memory.add(f"アイリがニュースを読んだ：\nタイトル：{trendings[selected_id-1].title}")
        await self.short_term_memory.add(f"内容：{content}", narrate=False)

class ActSearchNews(Action):
    name = "!SEARCH_NEWS"
    description = "Yahoo新聞を開いて、キーワードから新聞を検索する。"
    async def execute(self):
        await self.short_term_memory.add("アイリがYahooニュースの検索機能を使った。")
        yahoo_news = self.vlife.yahoo_news
        selected_topic = self.action_manager.ask("Yahooニュースを開いた。検索キーワードを入力してください：")
        if not selected_topic:
            await self.short_term_memory.add("検索結果がありませんでした。", narrate=False)

class ActMakeMemo(Action):
    name = "!MAKE_MEMO"
    description = "大事なことを忘れないように、スマホアプリで記録する"
    async def execute(self):
        await self.short_term_memory.add("アイリがスマホアプリにメモを書いた。")
        memo = self.vlife.memo
        content = self.action_manager.ask("メモアプリを開いた。なにを記録しますか(20文字程度)？")
        memo.write_memo(content)
        await self.short_term_memory.add(f"アイリがスマホアプリでメモをした：\n{content}")

class ActReadMemo(Action):
    name = "!READ_MEMO"
    description = "大事なことを忘れないように書いたメモを、スマホアプリから開く"
    async def execute(self):
        memo = self.vlife.memo
        memo_list_str = "\n".join(memo.read_memo(10))
        await self.short_term_memory.add(f"アイリがスマホアプリでメモを開いた：")
        await self.short_term_memory.add(memo_list_str, narrate=False)

class ActCheckSchoolEvents(Action):
    name = "!CHECK_SCHOOL_EVENTS"
    description = "学校の行事表を見る"
    async def execute(self):
        school = self.vlife.school
        school_events = school.get_school_events_str()
        await self.short_term_memory.add(f"アイリが学校の行事表を調べた：")
        await self.short_term_memory.add(school_events, narrate=False)
class ActCheckTimeTable(Action):
    name = "!CHECK_TIMETABLE"
    description = "学校の時間割を開く"
    async def execute(self):
        school = self.vlife.school
        timetable = school.get_timetable_str()
        await self.short_term_memory.add(f"アイリが時間割を調べた：")
        await self.short_term_memory.add(timetable, narrate=False)

class ActChangeTodayPlan(Action):
    name = "!CHANGE_TODAY_PLAN"
    description =  "今日の予定を変更する"
    async def execute(self):
        plan_change = self.action_manager.ask("今日はどのように予定を変更しようか？具体的に何時何分から何時何分まで？")
        new_plan = self.vlife.daily_planner.change_daily_plan(self.vlife.world_time.current_time, plan_change)
        await self.short_term_memory.add("アイリが今日の予定を変更した：")
        await self.short_term_memory.add(new_plan, narrate=False)

class ActCheckDateTime(Action):
    name = "!CHECK_DATETIME"
    description = "今の時間と日付を確認する"
    async def execute(self):
        await self.short_term_memory.add("アイリが今の時間と日付を調べた：")
        await self.short_term_memory.add(self.vlife.world_time.get_time_str(), narrate=False)

class ActSleepTillTomorrow(Action):
    name = "!SLEEP_TILL_TOMORROW"
    description = "明日まで寝る"
    async def execute(self):
        await self.short_term_memory.add("アイリが明日まで寝た。おやすみなさい。")
        # TODO 今は固定8時間寝るが、今後は改善する
        self.vlife.world_time.proceed_time(timedelta(hours=8))
    
class ActChatDeveloper(Action):
    name = "!CHAT_DEVELOPER"
    description = "アイリの開発者・シンにチャットを送信する。 {!CHAT_DEVELOPER **アイリが話した内容をそのまま送ること。**}  アイリがまだ話の内容が曖昧な場合は「{!CHECK_CHAT_DEVELOPER}」を使用する。" 
    async def execute(self, message):
        future = self.vlife.discord.schedule_task(self.vlife.discord.messenger.send_dm(message))
        await asyncio.wrap_future(future)
        
class ActCheckDeveloperChat(Action):
    name = "!CHECK_CHAT_DEVELOPER"
    description = "[スマホを開く][シンに話しかける]などに使う。アイリの開発者、シンからもらったチャットメッセージを見る"
    async def execute(self):
        future = self.vlife.discord.schedule_task(self.vlife.discord.messenger.read_dm_str())
        messages = await asyncio.wrap_future(future)
        await self.short_term_memory.add(f"アイリがシンとの会話履歴をチェックした。")
        await self.short_term_memory.add(messages, narrate=False)

class ActNew(Action):
    name = "!NEW_ACTION"
    description = "新しいコマンドを作成する。コマンドの後ろに説明が必要。シン以外の誰かに話しかけるときはこれを使う"
    
    async def execute(self, info):
        # コマンドを没収する
        self.action_manager.predefined_actions.remove(ActNew)
        self.action_manager.predefined_actions.remove(ActSleepTillTomorrow)
        # self.action_manager.PREDEFINED_ACTIONS.remove(ActStreaming)
        # TODO Implement real logic
        prompt_sim = self.vlife.queries.load_prompt_from_file(FilePath.PROMPT_EVENT_SIMULATOR)
        prompt_act = self.vlife.queries.load_prompt_from_file(FilePath.PROMPT_ACT)
        should_end = False
        loop_trial = 1
        while should_end == False:
            # シミュレータの番
            history = self.short_term_memory.get_short_term_memory(50)
            history_simulator = self.change_role(history)
            history_simulator.insert(0, self.adapter.create_message('system', prompt_sim))

            # 10回の会話ループごとに、{!END}を提唱する
            if loop_trial % 10 == 0:
                end_hint = self.adapter.create_message("assistant", "もう凄い時間立っているのにまだ{!end}していないの？忘れた？")
                history_simulator.append(end_hint)
            
            simulator = self.adapter.chat_completions(history_simulator)
            action_list = self.action_manager.parse(simulator)
            for action, desc in action_list:
                if action == "!END":
                    should_end = True
                    print("[DEBUG]!ENDが検出された。")
                    break
            if should_end:
                break
            else:
                await self.short_term_memory.add(simulator, role="user")
            await asyncio.sleep(1)

            # アイリの番
            new_history = self.short_term_memory.get_short_term_memory(50)
            new_history.insert(0, self.adapter.create_message('system', prompt_act))
            airi = self.adapter.chat_completions(new_history)
            await self.short_term_memory.add(airi, role="assistant")

            # 対応するコマンドを実行してください
            prompt = self.vlife.queries.load_prompt_from_file(FilePath.PROMPT_ACT_PROCESS_NEW)
            command_list = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                        self.adapter.create_message('user', airi)])
            action_list = self.action_manager.parse(command_list)
            
            print("[SYSTEM]検出されたコマンド：", action_list)
            await self.action_manager.find_match_action(action_list)

            # 次のループに進む
            loop_trial += 1
        
        # await self.short_term_memory.add(f"アイリが楽しい時間を過ごした：")
        # await self.short_term_memory.add(info, narrate=False)

        # コマンドを返す
        self.action_manager.predefined_actions.append(ActNew)
        self.action_manager.predefined_actions.append(ActSleepTillTomorrow)
        # self.action_manager.PREDEFINED_ACTIONS.append(ActStreaming)
        await asyncio.sleep(5) # クールタイムを入れて休憩

    def change_role(self, messages: list):
        for message in messages:
            if message["role"] == 'user':
                message["role"] = 'assistant'
            elif message["role"] == 'assistant':
                message["role"] = 'user'
        return messages

if __name__ == "__main__":
    action_list = [('!NEW_ACTION', '家に行く'), ('!NEW_ACTION', '友達と遊ぶ')]
    for action, desc in action_list:
        if action == ActNew.name:
            # 一番目のアクションだけ実行する
            print("Action detected")
        else:
            # すべてのコマンドを実行する
            print("Not detected")