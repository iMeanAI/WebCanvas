from Prompt import *
from LLM import *


class Planning:
    def __init__(self):
        pass

    @staticmethod
    async def plan(uuid, user_request, tab_name_list, current_tab_name, current_time, previous_trace, dom):
        # 创建GPT查询类
        GPT35 = GPTGenerator35()
        GPT4 = GPTGenerator4()

        # 构建planning prompt及查询
        planning_request = PlanningPromptConstructor().construct(
            user_request, previous_trace, dom, tab_name_list, current_tab_name)

        response = GPT35.request(planning_request)

        # 构建reward prompt及查询
        stringfy_thought_and_action_output = PlanningPromptConstructor().stringfy_thought_and_action(previous_trace)

        reward_request = RewardPromptConstructor().construct(user_request, stringfy_thought_and_action_output) 
