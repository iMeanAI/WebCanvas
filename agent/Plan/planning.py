from agent.Prompt import *
from agent.LLM import *
from .action import *
import time

from agent.Prompt import *
from agent.LLM import *
from .action import *
import time


class Planning:
    def __init__(self):
        pass

    @staticmethod
    async def plan(uuid, user_request, previous_trace, observation, feedback, mode, observation_VforD,global_reward: bool = True):  # TODO
        start_time = time.time()
        # 创建GPT查询类
        GPT35 = GPTGenerator35()
        GPT4 = GPTGenerator4()
        GPT4V = GPTGenerator4V()
        status_and_description = None
        if len(previous_trace) > 0:
            stringfy_thought_and_action_output = ObservationPromptConstructor().stringfy_thought_and_action(
                previous_trace)
            reward_request = RewardPromptConstructor().construct(
                user_request, stringfy_thought_and_action_output)
            print(f"\033[32mGlobal_reward_Request{reward_request}")  # 绿色
            print("\033[0m")
            reward_response, error_message = await GPT4.request(reward_request)
            status_and_description = ActionParser().extract_status_and_description(
                reward_response)
            print(f"\033[34mGlobal_Reward_Response:\n{reward_response}")  # 蓝色
            print("\033[0m")
        else:
            reward_response = ""

        # 构建planning prompt及查询
        if mode == "dom":
            status_description = ""
            if global_reward:
                status_description = status_and_description.get(
                    "description") if status_and_description and status_and_description.get("description") else ""
            planning_request = ObservationPromptConstructor().construct(
                user_request, previous_trace, observation, feedback, status_description)
            print(f"\033[32m{planning_request}")  # 绿色
            print("\033[0m")
            planning_response, error_message = await GPT4.request(planning_request)
        elif mode == "d_v":
            status_description = ""
            if global_reward:
                status_description = status_and_description.get(
                    "description") if status_and_description and status_and_description.get("description") else ""
            planning_request = D_VObservationPromptConstructor().construct(
                user_request, previous_trace, observation, observation_VforD, feedback, status_description)
            # print(f"\033[32m{planning_request}")  # 绿色 涉及到图片
            # display_string = planning_request[:100] # 截取字符串的前 max_length 个字符
            # print(f"\033[32m{display_string}")
            def print_limited_json(obj, limit=100):
                if isinstance(obj, dict):
                    return {k: print_limited_json(v, limit) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [print_limited_json(element, limit) for element in obj]
                else:
                    return str(obj)[:limit]

            print(f"\033[32m{print_limited_json(planning_request, limit=1000)}")
            print("\033[0m")
            planning_response, error_message = await GPT4V.request(planning_request)
        elif mode == "vision":
            planning_request = VisionObservationPromptConstructor().construct(
                user_request, previous_trace, observation)
            print(f"\033[32m{planning_request}")  # 绿色
            print("\033[0m")
            planning_response, error_message = await GPT4V.request(planning_request)

        print(f"\033[34mOpenai_Planning_Response:\n{planning_response}")  # 蓝色
        print("\033[0m")
        # 提取出planning thought(str)和planning action(dict), 其中planning action拥有action, element_id, action_input, description四个字段
        planning_response_thought, planning_response_action = ActionParser().extract_thought_and_action(
            planning_response)

        if planning_response_action.get('action') == "fill_form":
            JudgeSearchbarRequest = JudgeSearchbarPromptConstructor().construct(
                input_element=observation, planning_response_action=planning_response_action)
            Judge_response, error_message = await GPT35.request(JudgeSearchbarRequest)
            if Judge_response.lower() == "yes":
                planning_response_action['action'] = "fill_search"

        # description应该包括thought(GPT4返回的)和action(planning解析的)两个字段
        planning_response_action["description"] = {
            "reward": status_and_description if len(reward_response) > 0 else None,
            "thought": planning_response_thought,
            "action": (
                f'{planning_response_action["action"]}: {planning_response_action["action_input"]}' if "description" not in planning_response_action.keys() else
                planning_response_action["description"])
            if mode == "dom" or mode == "d_v" else (
                planning_response_action["action"] if "description" not in planning_response_action.keys() else
                planning_response_action["description"])
        }
        if mode == "dom" or mode == "d_v":
            planning_response_action = {element: planning_response_action.get(
                element, "") for element in ["element_id", "action", "action_input", "description"]}
        elif mode == "vision":
            planning_response_action = {element: planning_response_action.get(
                element, "") for element in ["action", "description"]}
        execute_time = time.time() - start_time
        logger.info("****************")
        logger.info(planning_response_action)
        dict_to_write = {}
        dict_to_write['uuid'] = uuid
        if mode == "dom" or mode == "d_v":
            dict_to_write['id'] = planning_response_action['element_id']
            dict_to_write['action_type'] = planning_response_action['action']
            dict_to_write['value'] = planning_response_action['action_input']
        elif mode == "vision":
            dict_to_write['action'] = planning_response_action['action']
        dict_to_write['description'] = planning_response_action['description']
        dict_to_write['execute_time'] = execute_time
        dict_to_write['error_message'] = error_message
        dict_to_write['openai_response'] = planning_response

        return dict_to_write

    # @staticmethod
    # async def evaluate(user_request, previous_trace, current_trace, observation):  # TODO
    #     GPT4 = GPTGenerator4()
    #     current_trace = [current_trace]
    #     if len(previous_trace) > 0:
    #         stringfy_previous_trace_output = ObservationPromptConstructor(
    #         ).stringfy_thought_and_action(previous_trace)
    #         stringfy_current_trace_output = ObservationPromptConstructor(
    #         ).stringfy_thought_and_action(current_trace)
    #         current_reward_response = CurrentRewardPromptConstructor().construct(
    #             user_request, stringfy_previous_trace_output, stringfy_current_trace_output, observation)
    #         print(f"\033[32m{current_reward_response}")  # 绿色
    #         print("\033[0m")
    #         evaluate_response, error_message = await GPT4.request(current_reward_response)
    #         score_description = ActionParser().extract_score_and_description(
    #             evaluate_response)
    #         # 蓝色
    #         print(f"\033[34mOpenai_evaluate_Response:\n{score_description}")
    #         print("\033[0m")
    #         return score_description
    #     return ""

    @staticmethod
    async def evaluate(user_request, previous_trace, current_trace, observation, observation_VforD=""):  # TODO
        GPT4 = GPTGenerator4()
        GPT4V = GPTGenerator4V()
        current_trace = [current_trace]
        if len(previous_trace) > 0:
            stringfy_previous_trace_output = ObservationPromptConstructor(
            ).stringfy_thought_and_action(previous_trace)
            stringfy_current_trace_output = ObservationPromptConstructor(
            ).stringfy_thought_and_action(current_trace)
            if observation_VforD == "":
                current_reward_resquest = CurrentRewardPromptConstructor().construct(
                    user_request, stringfy_previous_trace_output, stringfy_current_trace_output, observation)
                print(f"\033[32m{current_reward_resquest}")  # 绿色
                print("\033[0m")
                evaluate_response, error_message = await GPT4.request(current_reward_resquest)
                score_description = ActionParser().extract_score_and_description(
                    evaluate_response)
                # 蓝色
                print(
                    f"\033[34mCurrent_reward_Response:\n{score_description}")
                print("\033[0m")
                return score_description
            else:
                vision_reward_resquest = VisionRewardPromptConstructor().construct(user_request,
                                                                                   stringfy_previous_trace_output, stringfy_current_trace_output, observation, observation_VforD)
                print(f"\033[32m{vision_reward_resquest}")  # 绿色
                print("\033[0m")
                evaluate_response, error_message = await GPT4V.request(vision_reward_resquest)
                score_description = ActionParser().extract_score_and_description(
                    evaluate_response)
                # 蓝色
                print(
                    f"\033[34mVision_reward_Response:\n{score_description}")
                print("\033[0m")
                return score_description
        return ""
