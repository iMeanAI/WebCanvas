import re
import json5

import traceback
from agent.Prompt import *
from ..Utils import *


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
        decoded_result = None
        try:
            decoded_result = json5.loads(message_substring)
        except Exception as e:
            # logger.info(f"Error parsing:\n{result_action_substring}\n")
            traceback.print_exc()

        return decoded_result

    def extract_status_and_summary(self, message) -> dict:
        result_status = "null"
        try:
            result_status = re.findall(
                "status:(.*?)summarization:", message, re.S)[0].strip()
            print(result_status)
        except:
            try:
                result_status = message.split("summarization:")[0].strip()
            except:
                result_status = "null"
        try:
            summary = re.findall("```(.*?)```", message, re.S)[0]
        except:
            summary = message.split("summarization:")[-1].strip()
        status_summary = self.parse_action(summary)
        return status_summary

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
