from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.VLife import VLife
# アクションはAIVTuber向けインターフェース
PREDEFINED_ACTIONS = [
    {
        "name": "STREAMING",
        "description": "パソコンを使って、ライブ配信を開始する。",
        "realtime": True
    },
    {
        "name": "POST_TWITTER",
        "description": "Twitterに新しい投稿をする。"
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
        "name": "READ_NEWS",
        "description": "Yahoo新聞を開いて、新聞を読む。"
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

class Actions:
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
    
    def take_action(self):
        # 今、一番したいことは？
        prompt = self.queries.load_prompt_from_file("storage/airi/decisions.txt")
        decision = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', "一番したいこと:")])
        # 今の考えを整理しよう

        
        # 対応するコマンドを実行してください
        prompt = self.queries.load_prompt_from_file("commands.txt")
        command_list = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', decision)])
        
        # 