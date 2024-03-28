import json5


class HistoryMemory:
    def __init__(self, previous_trace: list=[],reflection: str = "") -> None:
        self.previous_trace = previous_trace
        self.reflection = reflection

    def add_trace(self, thought, action):
        self.previous_trace.append({"thought":thought,"action":action})

    def stringfy_thought_and_action(self) -> str:
        input_list = json5.loads(self.previous_trace, encoding="utf-8")
        str_output = ""
        if len(input_list) > 2:
            str_output = "["
            # for idx, i in enumerate(input_list[:-1]):
            #     str_output += f'Step{idx+1}:\"Thought: {i["thought"]}, Action: {i["action"]},Reflection: {i["reflection"]}\";\n'
            # str_output += "]"
            for idx in range(len(input_list)-1):
                str_output += f'Step{idx+1}:\"Thought: {input_list[idx]["thought"]}, Action: {input_list[idx]["action"]},Reflection: {input_list[idx+1]["reflection"]}\";\n'
            str_output += "]"
            current_trace = input_list[-1]
            str_output += f'The last Step: \"Thought: {current_trace["thought"]}, Action: {current_trace["action"]},Reflection: {self.reflection}\";\n'
        else:
            current_trace = input_list[-1]
            str_output += f'The last Step: \"Thought: {current_trace["thought"]}, Action: {current_trace["action"]},Reflection: {self.reflection}\";\n'
        return str_output

    def construct_previous_trace_prompt(self) -> str:
        stringfy_thought_and_action_output = self.stringfy_thought_and_action()
        previous_trace_prompt = f"The previous thoughts and actions are: \
            {stringfy_thought_and_action_output}.\n\nYou have done the things above.\n\n" #TODO：对reward的描述
        return previous_trace_prompt

    def construct_cache_trace(self):
        pass
