from agent.Prompt import *
from agent.LLM import *
from .action import *
import time

from agent.Prompt import *
from agent.LLM import *
from .action import *
import time
import json
import json5


class Planning:
    def __init__(self):
        pass

    @staticmethod
    async def plan(uuid, user_request, previous_trace, observation, feedback, mode, observation_VforD, global_reward: bool = True):  # TODO
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
            reward_response = ""
            for i in range(3):
                try:
                    reward_response, error_message = await GPT4.request(reward_request)
                    status_and_description = ActionParser().extract_status_and_description(
                        reward_response)
                    break
                except Exception as e:
                    traceback.print_exc()
                    print(f"planning reward_response or status_and_description error for {i+1} times")
                    # logger.error(f"Error in reward_response: {e}")
                    continue
            print(f"\033[34mGlobal_Reward_Response:\n{reward_response}")  # 蓝色
            print("\033[0m")
        else:
            reward_response = ""

        # 限制json的长度
        def print_limited_json(obj, limit=500, indent=0):
            spaces = ' ' * indent
            if isinstance(obj, dict):
                items = []
                for k, v in obj.items():
                    # Increase indent for nested objects
                    formatted_value = print_limited_json(v, limit, indent + 4)
                    items.append(f'{spaces}    "{k}": {formatted_value}')
                return f'{spaces}{{\n' + ',\n'.join(items) + '\n' + spaces + '}'
            elif isinstance(obj, list):
                # Apply indent to list elements and format each element
                elements = [print_limited_json(element, limit, indent + 4) for element in obj]
                return f'{spaces}[\n' + ',\n'.join(elements) + '\n' + spaces + ']'
            else:
                # Truncate string if it exceeds the limit and ensure proper JSON formatting
                truncated_str = str(obj)[:limit] + "..." if len(str(obj)) > limit else str(obj)
                return json5.dumps(truncated_str)

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
        elif mode == "dom_v_desc":
            status_description = ""
            if global_reward:
                status_description = status_and_description.get(
                    "description") if status_and_description and status_and_description.get("description") else ""
            if observation_VforD != "":
                vision_desc_request = VisionDisc2PromptConstructor().construct(
                    user_request, observation_VforD)  # vision description request with user_request
                # vision_desc_request = VisionDisc1PromptConstructor().construct(observation_VforD)
                vision_desc_response, error_message = await GPT4V.request(vision_desc_request)
            else:
                vision_desc_response = ""
            print(f"\033[36mvision_disc_response:\n{vision_desc_response}")  # 蓝色
            planning_request = ObservationVisionDiscPromptConstructor().construct(
                user_request, previous_trace, observation, feedback, status_description, vision_desc_response)
            # print(f"\033[32m{planning_request}")
            print(f"\033[35mplanning_request:\n{print_limited_json(planning_request, limit=10000)}")  # 紫色
            print("\033[0m")
            planning_response, error_message = await GPT4.request(planning_request)
        elif mode == "vision_to_dom":
            status_description = ""
            if global_reward:
                status_description = status_and_description.get(
                    "description") if status_and_description and status_and_description.get("description") else ""
            vision_act_request = ObservationVisionActPromptConstructor().construct(
                user_request, previous_trace, observation_VforD, feedback, status_description)
            max_retries = 3  # 设置最大重试次数为3
            for attempt in range(max_retries):
                vision_act_response, error_message = await GPT4V.request(vision_act_request)
                print(f"\033[36mvision_act_response:\n{vision_act_response}")  # 蓝色输出
                print("\033[0m")  # 重置颜色
                planning_response_thought, planning_response_action = ActionParser().extract_thought_and_action(
                    vision_act_response)
                actions = {
                    'goto': "Found 'goto' in the vision_act_response.",
                    'google_search': "Found 'google_search' in the vision_act_response.",
                    'switch_tab': "Found 'switch_tab' in the vision_act_response.",
                    'scroll_down': "Found 'scroll_down' in the vision_act_response.",
                    'scroll_up': "Found 'scroll_up' in the vision_act_response."
                }
                # 检查行为是否在预定义的行为列表中
                actions_found = False
                for action, message in actions.items():
                    if action == planning_response_action.get('action'):
                        print(message)
                        actions_found = True
                        # action无需改变
                        # `target_element`应该没有，有的话是用不到的
                        break

                # 如果没有找到预定义的行为
                if not actions_found:
                    print(
                        "None of 'goto', 'google_search', 'switch_tab', 'scroll_down', or 'scroll_up' were found in the vision_act_response.")

                    target_element = planning_response_action.get('target_element')
                    description = planning_response_action.get('description')

                    # 如果目标元素为空或不存在
                    if not target_element:
                        print("The 'target_element' is None or empty.")
                        continue  # 继续下一次循环尝试

                    # 构建视觉到DOM的请求
                    planning_request = VisionToDomPromptConstructor().construct(target_element, description, observation)
                    print(f"\033[35mplanning_request:{planning_request}")
                    print("\033[0m")

                    # 发送请求并等待响应
                    planning_response, error_message = await GPT4.request(planning_request)
                    print(f"\033[34mVisionToDomplanning_response:\n{planning_response}")
                    print("\033[0m")
                    # 解析元素ID
                    element_id = ActionParser().get_element_id(planning_response)
                    if element_id == "-1":
                        print("The 'element_id' is not found in the planning_response.")
                        continue  # 如果未找到元素ID，则继续下一次循环尝试
                    else:
                        planning_response_action['element_id'] = element_id
                        break  # 如果找到元素ID，则退出循环

                else:
                    # 如果找到了预定义的行为，则不需要重试，直接退出循环
                    break

            action_json_str = json5.dumps(planning_response_action, indent=2)
            # 将 "Action:" 文本和 JSON 字符串拼接，JSON 字符串用三个单引号包围
            action_result = f'Action:\n```\n{action_json_str}\n```'
            planning_response = f"Thought: {planning_response_thought}\n\n" + action_result
            # 检查是否达到最大重试次数
            if attempt == max_retries - 1:
                print("Max retries of vision_act reached. Unable to proceed.")
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

            print(f"\033[32mplanning_request:\n{print_limited_json(planning_request, limit=1000)}")
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
        if mode != "vision_to_dom":
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
            if mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"] else (
                planning_response_action["action"] if "description" not in planning_response_action.keys() else
                planning_response_action["description"])
        }
        if mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"]:
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
        if mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"]:
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
                                                                                   stringfy_previous_trace_output,
                                                                                   stringfy_current_trace_output,
                                                                                   observation, observation_VforD)
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
