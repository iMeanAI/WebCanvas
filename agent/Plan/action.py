import re
from typing import Tuple, Any, List

import json5
import json

import traceback
from agent.Prompt import *
from ..Utils import *


class ActionParser():
    def __init__(self):
        pass

    # 将OpenAI返回的结果中提取Thought和Action，返回thought(str)和action(dict), 其中action拥有action, element_id, action_input, description四个字段
    def extract_thought_and_action(self, message) -> tuple[Any, Any]:
        # result_thought = "null"
        # try:
        #     result_thought = re.findall(
        #         "Thought:(.*?)Action:", message, re.S)[0].strip()
        # except:
        #     try:
        #         result_thought = message.split("Action:")[0].strip()
        #     except:
        #         result_thought = "null"
        try:
            result_action = re.findall("```(.*?)```", message, re.S)[0]

        except:
            result_action = message

        result_action = self.parse_action(result_action)
        result_thought = result_action.get("thought")
        return result_thought, result_action

    def parse_action(self, message):
        message_substring = extract_longest_substring(message)
        decoded_result = {}
        # 这里的try-except的逻辑在planning里面已经实现了，这里写了那里就没办法retry
        # try:
        decoded_result = json5.loads(message_substring)
        # except Exception as e:
        #     # logger.info(f"Error parsing:\n{result_action_substring}\n")
        #     traceback.print_exc()

        return decoded_result

    def extract_status_and_description(self, message) -> dict:
        # result_status = "null"
        # try:
        #     result_status = re.findall(
        #         "status:(.*?)description:", message, re.S)[0].strip()
        #     print(result_status)
        # except:
        #     try:
        #         result_status = message.split("description:")[0].strip()
        #     except:
        #         result_status = "null"
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

    # @staticmethod
    # def parse_json_output(json_str):
    #     try:
    #         # 尝试解析字符串
    #         return json.loads(json_str)
    #     except json.JSONDecodeError:
    #         # 如果解析失败，尝试替换单引号为双引号后再解析
    #         json_str = json_str.replace("'", '"')
    #         return json.loads(json_str)
