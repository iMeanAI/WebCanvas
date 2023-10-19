from Prompt import *
from LLM import *
from action import *
import time


class Planning:
    def __init__(self):
        pass

    @staticmethod
    async def plan(uuid, user_request, tab_name_list, current_tab_name, current_time, previous_trace, dom):
        start_time = time.time()
        # 创建GPT查询类
        GPT35 = GPTGenerator35()
        GPT4 = GPTGenerator4()

        if len(previous_trace) > 0:
            # 构建reward prompt及查询
            stringfy_thought_and_action_output = PlanningPromptConstructor(
            ).stringfy_thought_and_action(previous_trace)

            reward_request = RewardPromptConstructor().construct(
                user_request, stringfy_thought_and_action_output)

            reward_response, error_message = GPT4.request(reward_request)
        else:
            reward_response = ""

        # 构建planning prompt及查询
        planning_request = PlanningPromptConstructor().construct(
            user_request, previous_trace, dom, tab_name_list, current_tab_name)

        planning_response, error_message = GPT35.request(planning_request)

        # 提取出planning thought(str)和planning action(dict), 其中planning action拥有action, element_id, action_input, description四个字段
        planning_response_thought, planning_response_action = ActionParser.extract_thought_and_action(
            planning_response)

        # 判断是否是搜索框，如果是则将planning action的action字段改成fill_and_search
        # TODO 移到action文件里
        if planning_response_action == "fill_form":
            # TODO 补全input_element
            judge_searchbar_request = JudgeSearchbarPromptConstructor().construct(
                input_element=1, decoded_result=planning_response_action)
            judge_searchbar_response, error_message = GPT35.request(
                judge_searchbar_request)
            if judge_searchbar_response.lower() == "yes":
                planning_response_action["action"] = "fill_and_search"

        # description应该包括thought(GPT4返回的)和action(planning解析的)两个字段
        planning_response_action["description"] = {
            "thought": reward_response if "reward_response" in locals() else planning_response_thought,
            "action": f'{planning_response_action["action"]}: {planning_response_action["action_input"]}' if "description" not in planning_response_action.keys() else planning_response_action["description"]
        }

        planning_response_action = {element: planning_response_action.get(
            element, "") for element in ["element_id", "action", "action_input"]}

        execute_time = time.time() - start_time
        dict_to_write = {}
        dict_to_write['uuid'] = uuid
        dict_to_write['id'] = planning_response_action['element_id']
        dict_to_write['action_type'] = planning_response_action['action']
        dict_to_write['value'] = planning_response_action['action_input']
        dict_to_write['description'] = planning_response_action['description']
        dict_to_write['execute_time'] = execute_time
        dict_to_write['error_message'] = error_message
        dict_to_write['openai_response'] = planning_response
