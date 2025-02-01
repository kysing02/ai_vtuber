import re
from scripts.commands.action import *
from file_manager import FilePath
if TYPE_CHECKING:
    from scripts.vlife import VLife

# アクションはAIVTuber向けインターフェース
class ActionManager:
    PREDEFINED_ACTIONS: list[Action] = [
        # ActStreaming,
        ActPostTwitter,
        ActWriteDiary,
        ActEnterDiscord,
        ActLeaveDiscord,
        ActEnterDiscordVoiceChat,
        ActLeaveDiscordVoiceChat,
        ActReadNews,
        ActSearchNews,
        ActMakeMemo,
        ActReadMemo,
        ActCheckSchoolEvents,
        ActCheckTimeTable,
        ActChangeTodayPlan,
        ActCheckDateTime,
        ActSleepTillTomorrow,
        ActChatDeveloper,
        # ActCheckDeveloperChat,
        ActNew
    ]
    
    def __init__(self, vlife: "VLife"):
        self.vlife = vlife
        self.queries = vlife.queries
        self.adapter = vlife.openai_adapter
        self.reflection = vlife.reflection
        # self.all_actions = ActionManager.PREDEFINED_ACTIONS.append(self.__load_saved_actions())

    def get_available_actions_str(self):
        available_actions = "今実行できるコマンドのリスト：\n"
        for action in ActionManager.PREDEFINED_ACTIONS:
            available_actions = available_actions + f"{action.name} : {action.description}\n"
        return available_actions
    
    def parse(self, text: str):
        # Regular expression to match commands
        command_pattern = re.compile(r'\{!(.*?)\}')
        
        # Find all commands in the input string
        commands = command_pattern.findall(text)
        
        # List to store the final result as (command, description)
        result = []
        
        for command in commands:
            # Split the command into name and description (if any)
            if " " in command:
                # Split into command name and description
                command_name, description = command.split(maxsplit=1)
                result.append((f"!{command_name}", description))
            else:
                # If no description, set description to empty string
                result.append((f"!{command}", ""))
        
        return result
    
    async def take_action(self):
        # 今の考えを整理しよう
        thought = self.reflection.reflect_thought()
        print("[SYSTEM]アイリが今考えていること：", thought)

        # 今、一番したいことは？
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_ACT)
        decision = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', "一番したいこと:")])
        print("[SYSTEM]アイリが今一番したいこと：", decision)

        # 対応するコマンドを実行してください
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_ACT_PROCESS)
        command_list = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                       self.adapter.create_message('user', decision)])

        # 対応するコマンドに応じて行動を取る
        print("[SYSTEM]出力されたコマンド：", command_list)

        action_list = self.parse(command_list)

        print("[SYSTEM]検出されたコマンド：", action_list)
        for action, desc in action_list:
            if action == ActNew.name:
                # 一番目のアクションだけ実行する
                perform = ActNew(self.vlife)
                await perform.execute(desc)
                await perform.end()
            elif action == ActChatDeveloper.name:
                perform = ActChatDeveloper(self.vlife)
                await perform.execute(desc)
                await perform.end()
            else:
                # すべてのコマンドを実行する
                for predefined_act in ActionManager.PREDEFINED_ACTIONS:
                    if action == predefined_act.name:
                        perform: Action = predefined_act(self.vlife)
                        await perform.execute()
                        await perform.end()

    def ask(self, question: str):
        prompt = self.queries.load_prompt_from_file(FilePath.PROMPT_ASK)
        reply = self.adapter.chat_completions([self.adapter.create_message('system', prompt),
                                               self.adapter.create_message('user', question)])
        return reply