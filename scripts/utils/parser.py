import re
import emoji

class Parser:
    @staticmethod
    def remove_brackets(text):
        processed_str = re.sub(r"\[.*?\]", "", text)
        processed_str.replace("「", "").replace("」", "")
        return processed_str

    @staticmethod
    def remove_emojis(text):
        return emoji.replace_emoji(text, replace="")  # Remove all emojis

    @staticmethod
    def parse_expression(input_text):
        # Step 1: Remove text inside square brackets
        text = Parser.remove_brackets(input_text).strip()

        # Step 2: Extract the token and remove it
        match = re.search(r"\{(\w+)\}", text)
        token = match.group(1) if match else None
        if token:
            text = text.replace(f"{{{token}}}", "").strip()

        # Step 3: Remove all emojis
        text = Parser.remove_emojis(text).strip()

        return token, text

# Test cases
if __name__ == "__main__":
    Parser.parse_expression("Hello {token1} world!")
    Parser.parse_expression("This is a [test] string with {token2}!")
    Parser.parse_expression("Unsupported emoji 😊 here! {token3}")
    Parser.parse_expression("Nothing here")
    Parser.parse_expression("アイリが今日の予定を立てた {token4}")
    Parser.parse_expression("これは{token5}のテストです")
    Parser.parse_expression("Emoji ❤️✨ removed! {token6}")
    Parser.parse_expression("顔文字 (´・ω・｀) OK {token7}")
