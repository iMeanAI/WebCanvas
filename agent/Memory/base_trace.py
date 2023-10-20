
from typing import List
import re

class OnceStep:

    def __init__(
        self,
        step_num: int = None,
        thought: str = "",
        action: str = ""
        
    ):
        self.thought = thought
        self.action = action
        self.step_num = step_num


class BaseTrace:

    def __init__(self):
        
        self.trace_output: dict = {}
        
    def parse_trace(
        self,
        trace: str
    )->List[OnceStep]:

        """
        """
        trace = trace.lower()
        steps_list = []
        matches = re.findall(r'step(\d+):(.*?)(?=(step\d+:|\]))', trace, re.DOTALL)
        for match in matches:
            thought_action = {}
            step_num = int(match[0])
            each_step_info = match[1].strip()
            thought,action = self._parse_step(each_step_info=each_step_info)
            steps_list.append(OnceStep(step_num=step_num,thought=thought,action=action))
            thought_action["thought"] = thought
            thought_action["action"] = action
            self.trace_output[f'step{step_num}'] = {"thought and action": thought_action}

        return steps_list

    def _parse_step(self,each_step_info: str):

        """
        extract each step's action and thought from step_info 
        """
        thought: str = ""
        action: str = ""
        match = re.search(r'thought:(.*?),\s*action:(.*?)$', each_step_info, re.DOTALL)
        try:
            if match:
                thought = match.group(1).strip()
                action = match.group(2).strip()
        except Exception as e:
            print(e)
            print("match error")
        
        return thought,action

    def get_trace(self):
        return self.trace_output


if __name__ == "__main__":

    previous_trace = "["
    step1 = f"Step1:\"Thought: To submit a merge request on git.starblazer.cn for the project imean-docker, we need to navigate to the project's repository page and find the option to create a new merge request. We will then fill out the necessary information and submit the merge request., Action: goto: https://git.starblazer.cn\";\n"
    step2 = f"Step2:\"Thought: To submit a merge request on git.starblazer.cn for the project imean-docker, we need to navigate to the project's repository page and find the option to create a new merge request. We will then fill out the necessary information and submit the merge request., Action: goto: https://git.starblazer.cn\";\n"
    previous_trace = previous_trace + step1 + step2 + "]"
    base_trace = BaseTrace()
    steps_list = base_trace.parse_trace(previous_trace)

    print(base_trace.get_trace())