import re
from typing import Tuple, Any, List

import json5
import json

import traceback
from agent.Prompt import *
from ..Utils import *


class ResponseError(Exception):
    """自定义响应错误类型"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ActionParser():
    def __init__(self):
        pass

    # 将OpenAI返回的结果中提取Thought和Action，返回thought(str)和action(dict), 其中action拥有action, element_id, action_input, description四个字段
    def extract_thought_and_action(self, message) -> tuple[Any, Any]:

        result_action = re.findall("```(.*?)```", message, re.S)[0]
        result_action = self.parse_action(result_action)
        if not result_action:
            raise ResponseError("OpenAI response is an invalid JSON blob")
        elif result_action and result_action.get("action") == '':
            raise ResponseError("OpenAI response action is Empty")
        result_thought = result_action.get("thought")
        return result_thought, result_action

    def parse_action(self, message):
        message_substring = extract_longest_substring(message)
        decoded_result = {}
        decoded_result = json5.loads(message_substring)
        return decoded_result

    def extract_status_and_description(self, message) -> dict:
        try:
            description = re.findall("```(.*?)```", message, re.S)[0]
            status_description = self.parse_action(description)
        except:
            try:
                description = message
                status_description = self.parse_action(description)
            except:
                description = message.split("description:")[-1].strip()
                status_description = self.parse_action(description)

        return status_description

    def extract_score_and_description(self, message) -> dict:
        result_score = "null"
        try:
            result_score = re.findall(
                "score:(.*?)description:", message, re.S)[0].strip()
        except:
            try:
                result_score = message.split("description:")[0].strip()
            except:
                result_score = "null"
        try:
            description = re.findall("```(.*?)```", message, re.S)[0]
        except:
            description = message.split("description:")[-1].strip()
        score_description = self.parse_action(description)
        return score_description

    @staticmethod
    def get_element_id(input_str) -> str:
        # First, try to parse with json.loads()

        # If JSON parsing fails, try to extract with a regular expression
        pattern = r'["\']element_id["\']:\s*["\']?(\d+)["\']?,\s*["\']'
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
        else:
            return '-1'
