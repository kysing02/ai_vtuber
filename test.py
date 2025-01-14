from openai_adapter import OpenAIAdapter
from world.WorldTime import WorldTime

if __name__ == "__main__":
    adapter = OpenAIAdapter()
    worldtime = WorldTime.create_real_time()
    sample_system_text = """あなたはコラショという高校生です．今の行動によって，時間がどれぐらい進みましたかを推測して下さい。正しい答えはなく，自由です。ただし，他のパラメータを参考してください。答えを{time: {hours:, mins:}}の形で答えて下さい. 0を入れても構いません{理由: }"""
    sample_user_text = f"""
    今日の予定は：
    13:00 放課後
    15:30 宿題
    19:00 晩ごはん
    19:30 塾
    22:00 寝る

    今の気分(0-100)は：
    喜 40
    怒 10
    哀 30
    楽 10

    性格：
    真面目
    自粛

    位置距離：
    友達の家から自分の家まで：30分

    今考えていること：
    今日の宿題やらないとまずいなー

    今の行動：
    あなたは時計を見ました．今の時間は{worldtime}です．
    あなたは今友達の家で新作ゲーム「FF15」を遊んでいます．
    """
    res = adapter.chat_completions([adapter.create_message("system", sample_system_text), adapter.create_message('user', sample_user_text)])
    print(res)