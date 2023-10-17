import json5


class HistoryMemory:

    def __init__(self,previous_trace: list) -> None:
        """
        previous_trace: list of each previous action and thought info before current environment state
        """
        self.previous_trace = previous_trace
        
    def stringfy_thought_and_action(self)->str:
        """
        output after stringfy previous trace
        """
        input_list = json5.loads(self.previous_trace, encoding="utf-8")
        str_output = "["
        for idx, i in enumerate(input_list):
            str_output += f'Step{idx+1}:\"Thought: {i["thought"]}, Action: {i["action"]}\";\n'
        str_output += "]"
        return str_output
    
    def ConstructPreviousTracePrompt(self)->str:
        """
        """
        stringfy_thought_and_action_output = self.stringfy_thought_and_action()
        previous_trace_prompt = f"The previous thoughts and actions are: \
            {stringfy_thought_and_action_output}.\n\nYou have done the things above.\n\n"
        return previous_trace_prompt

    def ConstructCacheTrace(self):
        """
        """
        pass


