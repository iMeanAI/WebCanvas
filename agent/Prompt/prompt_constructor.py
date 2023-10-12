import json5
from base_prompts import BasePrompts
from jinja2 import Template
import Tool


class PromptConstructor:
    def __init__(self):
        pass


class PlanningPromptConstructor(PromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.planning_prompt_system
        self.prompt_user = BasePrompts.planning_prompt_user
        self.interactable_element = []
        self.link_element = []
        self.input_element = []
        self.unknown_element = []

    # 构建planning的prompt，输出openai可解析的格式
    def construct(self, user_request: str, previous_trace: str, dom: str, tab_name_list: list, current_tab_name: str, max_token: int = 16000) -> list:
        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request)
        if len(previous_trace) > 0:
            
            self.interactable_element, self.link_element, self.input_element, self.unknown_element = Tool.process_dom(dom)
            stringfy_thought_and_action_output = Tool.stringfy_thought_and_action(
                previous_trace)
            self.prompt_user += f"The previous thoughts and actions are: {stringfy_thought_and_action_output}.\n\nYou have done the things above.\n\n"
            self.prompt_user += f"All tabs are {str(tab_name_list)}. Now you are on tab '{str(current_tab_name)}'. The current elements with id are as follows:\n\n"\
                f"interactable elements(like button, select and option): {str(self.interactable_element)}\n\n"\
                f"link element: {str(self.link_element)}\n\n"\
                f"input elements(like input and textarea): {str(self.input_element)}"
            if len(self.unknown_element) > 0:
                prompt_user += f"\n\nother elements with tagname: {str(self.unknown_element)}"


        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages


class RewardPromptConstructor(PromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.reward_prompt_system
        self.prompt_user = BasePrompts.reward_prompt_user

    def construct(self, user_request: str, stringfy_thought_and_action_output: str) -> list:
        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request, stringfy_thought_and_action_output=stringfy_thought_and_action_output)
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages


class JudgeSearchbarPromptConstructor(PromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.judge_searchbar_prompt_system
        self.prompt_user = BasePrompts.judge_searchbar_prompt_user

    # TODO 改掉decoded_result
    def constructor(self, user_request: str, input_element, decoded_result) -> list:
        self.prompt_user = Template(self.prompt_user).render(input_element=str(
            input_element), element_id=decoded_result['element_id'], action_input=decoded_result['action_input'])
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages


if __name__ == "__main__":
    res = BasePrompts.planning_prompt_system
    print(res)
