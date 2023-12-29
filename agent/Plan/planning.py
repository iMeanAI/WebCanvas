from agent.Prompt import *
from agent.LLM import *
from .action import *
import time


class Planning:
    def __init__(self):
        pass

    @staticmethod
    async def plan(uuid, user_request, previous_trace, observation):  # TODO
        start_time = time.time()
        # 创建GPT查询类
        GPT35 = GPTGenerator35()
        GPT4 = GPTGenerator4()
        if len(previous_trace) > 0:
            stringfy_thought_and_action_output = ObservationPromptConstructor(
            ).stringfy_thought_and_action(previous_trace)
            reward_request = RewardPromptConstructor().construct(
                user_request, stringfy_thought_and_action_output)
            reward_response, error_message = await GPT4.request(reward_request)
            status_summary = ActionParser().extract_status_and_summary(
                reward_response)
            print(f"\033[34mOpenai_Reward_Response:\n{reward_response}")  # 蓝色
            print("\033[0m")
        else:
            reward_response = ""

        # 构建planning prompt及查询
        planning_request = ObservationPromptConstructor().construct(
            user_request, previous_trace, observation)
        print(f"\033[32m{planning_request}")  # 绿色
        print("\033[0m")
        planning_response, error_message = await GPT4.request(planning_request)
        print(f"\033[34mOpenai_Planning_Response:\n{planning_response}")  # 蓝色
        print("\033[0m")
        # 提取出planning thought(str)和planning action(dict), 其中planning action拥有action, element_id, action_input, description四个字段
        planning_response_thought, planning_response_action = ActionParser().extract_thought_and_action(
            planning_response)
        # description应该包括thought(GPT4返回的)和action(planning解析的)两个字段
        planning_response_action["description"] = {
            "reward": status_summary if len(reward_response) > 0 else None,
            "thought": planning_response_thought,
            "action": f'{planning_response_action["action"]}: {planning_response_action["action_input"]}' if "description" not in planning_response_action.keys() else planning_response_action["description"]
        }
        planning_response_action = {element: planning_response_action.get(
            element, "") for element in ["element_id", "action", "action_input", "description"]}
        execute_time = time.time() - start_time
        logger.info("****************")
        logger.info(planning_response_action)
        dict_to_write = {}
        dict_to_write['uuid'] = uuid
        dict_to_write['id'] = planning_response_action['element_id']
        dict_to_write['action_type'] = planning_response_action['action']
        dict_to_write['value'] = planning_response_action['action_input']
        dict_to_write['description'] = planning_response_action['description']
        dict_to_write['execute_time'] = execute_time
        dict_to_write['error_message'] = error_message
        dict_to_write['openai_response'] = planning_response

        return dict_to_write

    @staticmethod
    async def evaluate(user_request, previous_trace, current_trace, observation):  # TODO
        GPT4 = GPTGenerator4()
        current_trace = [current_trace]
        if len(previous_trace) > 0:
            stringfy_previous_trace_output = ObservationPromptConstructor(
            ).stringfy_thought_and_action(previous_trace)
            stringfy_current_trace_output = ObservationPromptConstructor(
            ).stringfy_thought_and_action(current_trace)
            current_reward_response = CurrentRewardPromptConstructor().construct(
                user_request, stringfy_previous_trace_output, stringfy_current_trace_output, observation)
            print(f"\033[32m{current_reward_response}")  # 绿色
            print("\033[0m")
            evaluate_response, error_message = await GPT4.request(current_reward_response)
            score_description = ActionParser().extract_score_and_description(
                evaluate_response)
            # 蓝色
            print(f"\033[34mOpenai_evaluate_Response:\n{score_description}")
            print("\033[0m")
            return score_description
        return ""
