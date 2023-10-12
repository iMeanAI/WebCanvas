import json5

class HistoryMemory:
    def __init__(self) -> None:
        pass
        
    def stringfy_thought_and_action(self,input_list):
        """
        input_list : thought and actiton for each step
        return : output after stringfy
        """
        input_list = json5.loads(input_list, encoding="utf-8")
        str_output = "["
        for idx, i in enumerate(input_list):
            str_output += f'Step{idx+1}:\"Thought: {i["thought"]}, Action: {i["action"]}\";\n'
        str_output += "]"
        # logger.info(f"\033[32m\nstr_output\n{str_output}\033[0m")#绿色
        # logger.info(f"str_output\n{str_output}")
        return str_output

    