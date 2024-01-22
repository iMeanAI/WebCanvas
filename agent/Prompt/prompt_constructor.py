import base64

import json5
from .old_base_prompts import OldBasePrompts
from .base_prompts import BasePrompts
from .dom_vision_prompts import DomVisionPrompts
from .vision_prompts import VisionPrompts
from jinja2 import Template

from agent.Environment.environments import DomEnvironment
from agent.Memory.short_memory.history import HistoryMemory


class BasePromptConstructor:
    def __init__(self):
        pass


class PlanningPromptConstructor(BasePromptConstructor):  # 类：构建planning的prompt
    def __init__(self):
        self.prompt_system = OldBasePrompts.planning_prompt_system
        self.prompt_user = OldBasePrompts.planning_prompt_user

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
        self.prompt_system = BasePrompts.planning_prompt_system
        self.prompt_user = BasePrompts.planning_prompt_user

    def construct(
        self,
        user_request: str,
        previous_trace: str,
        observation: str,
        feedback: str = "",
        status_description: str = ""
    ) -> list:
        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request)
        if len(previous_trace) > 0:
            self.prompt_user += HistoryMemory(
                previous_trace=previous_trace).construct_previous_trace_prompt()
            if status_description != "":
                self.prompt_user + \
                    f"Task completion description is {status_description}"
            if feedback != "":
                self.prompt_user += f"An invalid action description is below:\n {feedback}\n"
            self.prompt_user += observation
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


class D_VObservationPromptConstructor(BasePromptConstructor):
    def __init__(self):
        self.prompt_system = DomVisionPrompts.d_v_planning_prompt_system
        self.prompt_user = DomVisionPrompts.d_v_planning_prompt_user


    @staticmethod
    def is_valid_base64(s):
        """
        Validate if a given string is a valid Base64 encoded string.

        :param s: String to be checked.
        :return: A tuple (bool, str) where the first element is True if the string is a valid Base64 encoded string,
                 and the second element is a message indicating the result or the type of error.

        byCarl: 本方法仅用于判断图片是否是base64编码，后期程序稳定时可以考虑删除
        """
        if s is None:
            return False, "The string is None."

        if not isinstance(s, str):
            return False, "The input is not a string."

        if len(s) == 0:
            return False, "The string is empty."

        try:
            # 尝试对字符串进行 Base64 解码
            base64.b64decode(s, validate=True)
            return True, "The string is a valid Base64 encoded string."
        except ValueError:
            # 如果解码抛出 ValueError 异常，则字符串不是有效的 Base64 编码
            return False, "The string is NOT a valid Base64 encoded string."

    def construct(
        self,
        user_request: str,
        previous_trace: str,
        observation: str,
        observation_VforD: str,
        feedback: str = ""
    ) -> list:
        is_valid, message = D_VObservationPromptConstructor.is_valid_base64(
            observation_VforD)
        print("prompt_constructor.py D_VObservationPromptConstructor:", message, "\n")
        rendered_prompt = Template(self.prompt_user).render(
            user_request=user_request)
        prompt_elements = [{"type": "text", "text": rendered_prompt}]
        if len(previous_trace) > 0:
            history_memory = HistoryMemory(previous_trace=previous_trace)
            trace_prompt = history_memory.construct_previous_trace_prompt()
            prompt_elements.append({"type": "text", "text": trace_prompt})
            if feedback != "":
                prompt_elements.append(
                    {"type": "text", "text": f"There an invalid action description is below:\n {feedback}\n"})
            prompt_elements.append(
                {"type": "text", "text": f"current observation or Dom tree is {observation}"})
            prompt_elements.append(
                {"type": "text", "text": "current screenshot is:"})
            print("len of prompt_elements before observation_VforD:",
                  len(prompt_elements))
            prompt_elements_str = json5.dumps(prompt_elements)
            print("len of prompt_elements_str before observation_VforD:", len(
                prompt_elements_str))  # 这将打印出转换为JSON字符串的prompt_elements的长度
            print("len of about gpt token of prompt_elements_str before observation_VforD:", len(
                prompt_elements_str)/5.42, "\n")
            prompt_elements.append(
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{observation_VforD}"}})
        # 构造最终的消息负载
        messages = [{"role": "system", "content": self.prompt_system},
                    {"role": "user", "content": prompt_elements}]
        # print(prompt_elements)
        print("messages finished!\n")
        return messages

    # 将previous thought和action转化成格式化字符串
    def stringfy_thought_and_action(self, input_list: list) -> str:
        input_list = json5.loads(input_list, encoding="utf-8")
        str_output = "["
        for idx, i in enumerate(input_list):
            str_output += f'Step{idx + 1}:\"Thought: {i["thought"]}, Action: {i["action"]}\";\n'
        str_output += "]"
        return str_output


class RewardPromptConstructor(BasePromptConstructor):  # 类：构建reward的prompt
    def __init__(self):
        self.prompt_system = BasePrompts.global_reward_prompt_system
        self.prompt_user = BasePrompts.global_reward_prompt_user

    # 构建reward的prompt，输出openai可解析的格式
    def construct(self, user_request: str, stringfy_thought_and_action_output: str, observation: str = "") -> list:
        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request, stringfy_thought_and_action_output=stringfy_thought_and_action_output)
        self.prompt_user += observation
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages


# 类：构建reward的prompt
class CurrentRewardPromptConstructor(BasePromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.current_reward_prompt_system
        self.prompt_user = BasePrompts.current_reward_prompt_user

    # 构建reward的prompt，输出openai可解析的格式
    def construct(
        self,
        user_request: str,
        stringfy_previous_trace_output: str,
        stringfy_current_trace_output: str,
        observation: str
    ) -> list:
        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request, stringfy_previous_trace_output=stringfy_previous_trace_output, stringfy_current_trace_output=stringfy_current_trace_output)
        self.prompt_user += f"current observation or accessibility tree is {observation}"
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages


# 类：构建vision reward的prompt
class VisionRewardPromptConstructor(BasePromptConstructor):
    def __init__(self):
        self.prompt_system = DomVisionPrompts.current_d_vision_reward_prompt_system
        self.prompt_user = DomVisionPrompts.current_d_vision_reward_prompt_user

    def construct(
        self,
        user_request: str,
        stringfy_previous_trace_output: str,
        stringfy_current_trace_output: str,
        observation: str,
        observation_VforD: str
    ) -> list:

        if not D_VObservationPromptConstructor.is_valid_base64(observation_VforD):
            print("提供的observation_VforD不是有效的Base64编码")

        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request, stringfy_previous_trace_output=stringfy_previous_trace_output, stringfy_current_trace_output=stringfy_current_trace_output)
        self.prompt_user += f"the key information of current web page is: {observation}"
        prompt_elements = [{"type": "text", "text": self.prompt_user}]
        # 添加当前观察（图像数据）
        prompt_elements.append(
            {"type": "text", "text": "the screenshot of current web page is :"})
        prompt_elements.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{observation_VforD}"}})

        # 构造最终的消息负载
        messages = [{"role": "system", "content": self.prompt_system},
                    {"role": "user", "content": prompt_elements}]
        return messages


# 类：构建判断该元素是否是搜索框的prompt（如果是，则前端需要额外加上回车操作）
class JudgeSearchbarPromptConstructor(BasePromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.judge_searchbar_prompt_system
        self.prompt_user = BasePrompts.judge_searchbar_prompt_user

    # 构建判断是否是搜索框的prompt，输出openai可解析的格式
    # TODO 改掉decoded_result
    def construct(self, input_element, planning_response_action) -> list:
        self.prompt_user = Template(self.prompt_user).render(input_element=str(
            input_element), element_id=planning_response_action['element_id'], action_input=planning_response_action['action_input'])
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages


class SemanticMatchPromptConstructor(BasePromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.semantic_match_prompt_system
        self.prompt_user = BasePrompts.semantic_match_prompt_user

    def construct(self, input_answer, semantic_method) -> list:
        self.prompt_user = Template(self.prompt_user).render(
            semantic_method=semantic_method, input_answer=input_answer)
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages
