import re
import yaml
from typing import Dict

def split_japanese_text(text: str):
    """
    Splits Japanese text into smaller segments:
    - Removes "、" separators.
    - Retains continuous punctuation like "！？" or "？！" as a single unit.
    """
    # Define separators but exclude "、" (it will be removed)
    separators = "。！？\n"
    
    # Use regex to split the text while retaining separators
    segments = re.split(f"([{separators}]+)", text)
    
    # Combine text and its separator while skipping "、"
    result = []
    for i in range(0, len(segments), 2):
        base_text = segments[i].replace("、", "")  # Remove "、"
        if i + 1 < len(segments):
            base_text += segments[i + 1]  # Append the separator(s)
        if base_text.strip():  # Ignore empty results
            result.append(base_text.strip())
    
    return result

def get_weekday_name(weekday: int) -> str:
    return {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday", 
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }[weekday]

def get_weekday_japanese(weekday: int) -> str:
    return {
        0: "月",
        1: "火",
        2: "水",
        3: "木", 
        4: "金",
        5: "土",
        6: "日"
    }[weekday]

def decapitalize(s: str) -> str:
    if not s:
        return s
    return s[0].lower() + s[1:]

def replace(replacements: Dict[str,str], content: str) -> str:
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content

def load_config(path: str):
    # TODO: Implement load config file functions
    raise(NotImplementedError)
    try:
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    print(get_weekday_name(0))  # Output: Monday
    print(get_weekday_japanese(6))  # Output: 日