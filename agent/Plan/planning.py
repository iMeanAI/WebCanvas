from agent.Prompt import *
from agent.LLM import *


class Planning:
    def __init__(self):
        pass

    @staticmethod
    async def plan(uuid, user_request, tab_name_list, current_tab_name, current_time, previous_trace, dom):
        GPT35 = GPTGenerator35()
        GPT4 = GPTGenerator4()

        planning_request = PlanningPromptConstructor().construct(
            user_request, previous_trace, dom, tab_name_list, current_tab_name)

        response = GPT35.request(planning_request)

        
        
