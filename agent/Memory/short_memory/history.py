import json5
from Prompt import *

class HistoryMemory:

    def __init__(self,previous_trace) -> None:
        """
        previous_trace : list of each previous action and thought info before current environment state
        """
        self.previous_trace = previous_trace
        
    def stringfy_thought_and_action(self):
        """
        return : output after stringfy previous trace
        """
        input_list = json5.loads(self.previous_trace, encoding="utf-8")
        str_output = "["
        for idx, i in enumerate(input_list):
            str_output += f'Step{idx+1}:\"Thought: {i["thought"]}, Action: {i["action"]}\";\n'
        str_output += "]"
        # logger.info(f"\033[32m\nstr_output\n{str_output}\033[0m")#绿色
        # logger.info(f"str_output\n{str_output}")
        return str_output

    
    def get_previous_trace_prompt(self):
        # return prompt_user += eval(previous_trace_prompt)
        previous_trace_prompt = f"The previous thoughts and actions are: {self.stringfy_thought_and_action()}.\n\nYou have done the things above.\n\n"
        return previous_trace_prompt


    def get_cache_trace(self):
        pass
