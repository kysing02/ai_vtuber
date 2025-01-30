from datetime import datetime
from scripts.world_simulation.daily_event_maker import DailyEventMaker
from scripts.adapters.hatena_entry_adapter import HatenaEntryAdapter
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.file_manager import FileManager, FilePath

class DiaryMaker:
    def __init__(self):
        self.system_prompt = FileManager.read(FilePath.PROMPT_DIARY)
    
    def __make(self):
        adapter = OpenAIAdapter()
        daily_events = DailyEventMaker.make()
        print(daily_events)
        res = adapter.chat_completions([adapter.create_message("system", self.system_prompt), adapter.create_message("user", daily_events)])
        return res
    
    def post(self):
        entry_text = self.__make()
        # 日時を取得
        entry_title = datetime.now().strftime("%Y年%m月%d日%H:%M:%Sの日記") 
        hatena_entry_adapter = HatenaEntryAdapter()
        hatena_entry_adapter.post(entry_title, entry_text)
        

if __name__ == "__main__":
    diary_maker = DiaryMaker()
    diary_maker.post()