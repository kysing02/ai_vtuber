from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.VLife import VLife

PREDEFINED_ACTIONS = [
    "STREAMING",
    "POST_TWITTER",
    "DIARY_WRITING",
    "ENTER_DISCORD",
    "LEAVE_DISCORD",
    "READ_NEWS",
    "MAKE_MEMO"
]

class Actions:
    def __init__(self, vlife: VLife):
        self.vlife = vlife
        self.adapter = vlife.openai_adapter
        self.all_actions = PREDEFINED_ACTIONS.append(self.__load_saved_actions())

    def __load_saved_actions():
        raise NotImplementedError
    
    def get_available_actions():
        raise NotImplementedError
    
    def parse(text: str):
        raise NotImplementedError

    def execute_actions(self, action_name: str):
        raise NotImplementedError
    
    def create_new_action():
        raise NotImplementedError
    
    def take_action():
        raise NotImplementedError