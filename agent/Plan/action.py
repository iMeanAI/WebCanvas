import re
from typing import Tuple, Any, List

import json5
import json

import traceback
from agent.Prompt import *
from ..Utils import *


class ResponseError(Exception):
    """Custom response error type"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ActionParser():
    def __init__(self):
        pass

    # Extract Thought and Action from the results returned by LLM,
    # return thought (str) and action (dict), where action has four fields: action, element_id, action_input, description
    def extract_thought_and_action(self, message) -> tuple[str, dict]:
        result_action = None
        try:
            result_action = re.findall("```(.*?)```", message, re.S)[0]
            result_action = self.parse_action(message)
        except:
            try:
                result_action = self.parse_action(message)
            except:
                result_action = self.parse_action_with_re(message)
        if not result_action:
            raise ResponseError(
                "Response is an invalid JSON blob or Empty!")
        elif result_action and result_action.get("action") == '':
            raise ResponseError(
                "Response action is Empty, Please try again.")
        result_thought = result_action.get("thought")
        return result_thought, result_action

    def parse_action_with_re(self, message):
        pattern = r'"thought"\s*:\s*"([^"]*)"\s*,\s*"action"\s*:\s*"([^"]*)"\s*,\s*"action_input"\s*:\s*"([^"]*)"\s*,\s*"element_id"\s*:\s*(null|\d*)\s*,\s*"description"\s*:\s*"([^"]*)"'
        match = re.search(pattern, message)
        if match:
            thought = str(match.group(1))
            action = str(match.group(2))
            action_input = str(match.group(3))
            element_id = str(match.group(4))
            description = str(match.group(5))
            thought = re.sub(r'\s+', ' ', thought).strip()
            action = re.sub(r'\s+', ' ', action).strip()
            action_input = re.sub(r'\s+', ' ', action_input).strip()
            element_id = re.sub(r'\s+', ' ', element_id).strip()
            description = re.sub(r'\s+', ' ', description).strip()
            result_dict = {
                "thought": thought,
                "action": action,
                "action_input": action_input,
                "element_id": element_id,
                "description": description
            }
            return result_dict

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
