import json5
from .base_prompts import BasePrompts
from .obs_prompts import ObservationPrompts
from jinja2 import Template

from agent.Prompt.base_prompts import BasePrompts
from agent.Environment.environments import DomEnvironment
from agent.Memory.short_memory.history import HistoryMemory


class BasePromptConstructor:
    def __init__(self):
        pass


class PlanningPromptConstructor(BasePromptConstructor):  # 类：构建planning的prompt
    def __init__(self):
        self.prompt_system = BasePrompts.planning_prompt_system
        self.prompt_user = BasePrompts.planning_prompt_user

    # 构建planning的prompt，输出openai可解析的格式
    def construct(
        self,
        user_request: str,
        previous_trace: str,
        dom: str,
        tab_name_list: list,
        current_tab_name: list,
    ) -> list:

        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request)

        if len(previous_trace) > 0:

            env = DomEnvironment(dom=dom,
                                 tab_name_list=tab_name_list, current_tab_name=current_tab_name)
            # add history memory
            self.prompt_user += HistoryMemory(
                previous_trace=previous_trace).construct_previous_trace_prompt()
            interact_element, link_element, input_element, unknown_element = env.html_denoiser()
            self.prompt_user += f"All tabs are {str(tab_name_list)}. Now you are on tab '{str(current_tab_name)}'.\
                The current elements with id are as follows:\n\n"\
                f"interactable elements(like button, select and option): {str(interact_element)}\n\n"\
                f"link element: {str(link_element)}\n\n"\
                f"input elements(like input and textarea): {str(input_element)}"
            if len(unknown_element) > 0:
                self.prompt_user += f"\n\nother elements with tagname: {str(unknown_element)}"

        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]

        return messages

    # 将previous thought和action转化成格式化字符串
    def stringfy_thought_and_action(self, input_list: list) -> str:
        input_list = json5.loads(input_list, encoding="utf-8")
        str_output = "["
        for idx, i in enumerate(input_list):
            str_output += f'Step{idx+1}:\"Thought: {i["thought"]}, Action: {i["action"]}\";\n'
        str_output += "]"
        return str_output


# 类：构建根据dom tree得到的planning的prompt
class ObservationPromptConstructor(BasePromptConstructor):
    def __init__(self):
        self.prompt_system = ObservationPrompts.planning_prompt_system
        self.prompt_user = ObservationPrompts.planning_prompt_user

    def construct(
        self,
        user_request: str,
        previous_trace: str,
        observation: str
    ) -> list:
        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request)
        if len(previous_trace) > 0:
            self.prompt_user += f"current observation or Dom tree is {observation}"
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages

    # 将previous thought和action转化成格式化字符串
    def stringfy_thought_and_action(self, input_list: list) -> str:
        input_list = json5.loads(input_list, encoding="utf-8")
        str_output = "["
        for idx, i in enumerate(input_list):
            str_output += f'Step{idx+1}:\"Thought: {i["thought"]}, Action: {i["action"]}\";\n'
        str_output += "]"
        return str_output


class RewardPromptConstructor(BasePromptConstructor):  # 类：构建reward的prompt
    def __init__(self):
        self.prompt_system = BasePrompts.reward_prompt_system
        self.prompt_user = BasePrompts.reward_prompt_user

    # 构建reward的prompt，输出openai可解析的格式
    def construct(self, user_request: str, stringfy_thought_and_action_output: str) -> list:
        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request, stringfy_thought_and_action_output=stringfy_thought_and_action_output)
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages


# 类：构建判断该元素是否是搜索框的prompt（如果是，则前端需要额外加上回车操作）
class JudgeSearchbarPromptConstructor(BasePromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.judge_searchbar_prompt_system
        self.prompt_user = BasePrompts.judge_searchbar_prompt_user

    # 构建判断是否是搜索框的prompt，输出openai可解析的格式
    # TODO 改掉decoded_result
    def construct(self, input_element, decoded_result) -> list:
        self.prompt_user = Template(self.prompt_user).render(input_element=str(
            input_element), element_id=decoded_result['element_id'], action_input=decoded_result['action_input'])
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages
