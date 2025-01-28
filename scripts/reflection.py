import re

class Emotion:
    @staticmethod
    def parse_expression(input_text):
        print("RAW TEXT:", input)
        # 正規表現で任意の位置にあるトークンとテキストを抽出
        match = re.search(r"\{(\w+)\}", input_text)
        if match:
            token = match.group(1)  # トークン名を取得
            # トークンを削除した後のテキストを取得
            text = input_text.replace(match.group(0), "").strip()
            print("TOKEN:", token)
            token = token.strip()
            return token, text
        return None, input_text  # トークンが見つからない場合は元の文字列をそのまま返す