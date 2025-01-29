import re

class Emotion:
    @staticmethod
    def parse_expression(input_text):
        print("RAW TEXT:", input_text)
        # Match the first occurrence of {token} anywhere in the text
        match = re.search(r"\{(\w+)\}", input_text)
        if match:
            token = match.group(1)  # Extract the token inside {}
            # Remove the token and the surrounding {} from the input text
            text = re.sub(r"\{\w+\}", "", input_text).strip()
            print("TOKEN:", token)
            return token, text
        return None, input_text
    
class Reflection:
    def __init__(self):
        raise NotImplementedError