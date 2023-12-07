import json5


class HistoryMemory:
    def __init__(self, previous_trace: list=[]) -> None:
        self.previous_trace = previous_trace

    def add_trace(self, thought, action):
        self.previous_trace.append({"thought":thought,"action":action})

    def stringfy_thought_and_action(self) -> str:
        input_list = json5.loads(self.previous_trace, encoding="utf-8")
        str_output = "["
        for idx, i in enumerate(input_list):
            str_output += f'Step{idx+1}:\"Thought: {i["thought"]}, Action: {i["action"]}\";\n'
        str_output += "]"
        return str_output

    def construct_previous_trace_prompt(self) -> str:
        stringfy_thought_and_action_output = self.stringfy_thought_and_action()
        previous_trace_prompt = f"The previous thoughts and actions are: \
            {stringfy_thought_and_action_output}.\n\nYou have done the things above.\n\n"
        return previous_trace_prompt

    def construct_cache_trace(self):
        pass
