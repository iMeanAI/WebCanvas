import re
import json5
from Utils import *
import traceback
from Prompt import *


class ActionParser():
    def __init__(self):
        pass

    # 将OpenAI返回的结果中提取Thought和Action，返回thought(str)和action(dict), 其中action拥有action, element_id, action_input, description四个字段
    def extract_thought_and_action(self, message) -> (str, dict):
        result_thought = "null"
        try:
            result_thought = re.findall(
                "Thought:(.*?)Action:", message, re.S)[0].strip()
        except:
            try:
                result_thought = message.split("Action:")[0].strip()
            except:
                result_thought = "null"
        try:
            result_action = re.findall("```(.*?)```", message, re.S)[0]
        except:
            result_action = message.split("Action:")[-1].strip()

        result_action = self.parse_action(result_action)

        return result_thought, result_action

    def parse_action(self, message):
        message_substring = extract_longest_substring(message)

        try:
            decoded_result = json5.loads(message_substring)
        except Exception as e:
            # logger.info(f"Error parsing:\n{result_action_substring}\n")
            traceback.print_exc()

        return decoded_result
