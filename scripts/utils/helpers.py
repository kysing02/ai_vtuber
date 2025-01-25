from typing import Dict

weekday_to_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_to_japanese = ["月", "火", "水", "木", "金", "土", "日"]

def get_weekday_name(weekday: int) -> str:
    return weekday_to_name[weekday]

def get_weekday_japanese(weekday: int) -> str:
    return weekday_to_japanese[weekday]

def decapitalize(s: str) -> str:
    if not s:
        return s
    return s[0].lower() + s[1:]

def replace(replacements: Dict[str,str], content: str) -> str:
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content

if __name__ == "__main__":
    print(get_weekday_name(0))  # Output: Monday
    print(get_weekday_japanese(6))  # Output: 日