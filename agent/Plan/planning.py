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
        # 类构造函数，目前为空

    @staticmethod
    async def plan(uuid, user_request, previous_trace, observation, mode, observation_VforD):  # TODO
        start_time = time.time()
        # 开始时间记录

        # 创建GPT查询类的实例
        GPT35 = GPTGenerator35()
        GPT4 = GPTGenerator4()
        GPT4V = GPTGenerator4V()
        # 这些实例分别代表不同版本的GPT模型

        if len(previous_trace) > 0:
            # 如果之前的追踪记录不为空
            stringfy_thought_and_action_output = ObservationPromptConstructor().stringfy_thought_and_action(previous_trace)
            # 将之前的追踪记录转换为字符串格式

            reward_request = RewardPromptConstructor().construct(user_request, stringfy_thought_and_action_output)
            # 构造奖励请求

            reward_response, error_message = await GPT4.request(reward_request)
            # 发送奖励请求并等待响应

            status_summary = ActionParser().extract_status_and_summary(reward_response)
            # 解析响应，提取状态和总结

            print(f"\033[34mOpenai_Reward_Response:\n{reward_response}")  # 蓝色
            print("\033[0m")
            # 打印奖励响应（蓝色文字）

        else:
            reward_response = ""
            # 如果之前没有追踪记录，则奖励响应为空

        # 构建计划请求并进行查询
        if mode == "dom":
            planning_request = ObservationPromptConstructor().construct(
                user_request, previous_trace, observation)
            print(f"\033[32m{planning_request}")  # 绿色
            print("\033[0m")
            # 打印计划请求（绿色文字）    
            planning_response, error_message = await GPT35.request(planning_request)
        elif mode == "d_v":
            planning_request = D_VObservationPromptConstructor().construct(
                user_request, previous_trace, observation, observation_VforD)
            print(f"\033[32m{planning_request}") # 绿色 涉及到图片
            # display_string = planning_request[:100] # 截取字符串的前 max_length 个字符
            # print(f"\033[32m{display_string}")
            # print("\033[0m")
            planning_response, error_message = await GPT4V.request(planning_request)
        elif mode == "vision":
            planning_request = VisionObservationPromptConstructor().construct(
                user_request, previous_trace, observation)
            print(f"\033[32m{planning_request}")  # 绿色
            print("\033[0m")
            # 打印计划请求（绿色文字） 
            planning_response, error_message = await GPT4V.request(planning_request)

        print(f"\033[34mOpenai_Planning_Response:\n{planning_response}")  # 蓝色
        print("\033[0m")
        # 发送计划请求并等待响应，然后打印响应（蓝色文字）

        # 提取计划响应中的思考（字符串）和行动（字典），其中mode == "dom"时的行动包含action, element_id, action_input, description四个字段
        planning_response_thought, planning_response_action = ActionParser().extract_thought_and_action(planning_response)

        # description字段应该包括thought（GPT4返回的）和action（计划解析的）
        planning_response_action["description"] = {
            "reward": status_summary if len(reward_response) > 0 else None,
            "thought": planning_response_thought,
            "action": (f'{planning_response_action["action"]}: {planning_response_action["action_input"]}' if "description" not in planning_response_action.keys() else planning_response_action["description"] ) if mode == "dom" else (planning_response_action["action"] if "description" not in planning_response_action.keys() else planning_response_action["description"])
        }
        # 更新planning_response_action字典，确保它包含必要的字段

        if mode == "dom" or mode == "d_v":
            planning_response_action = {element: planning_response_action.get(element, "") for element in ["element_id", "action", "action_input", "description"]}
        elif mode == "vision":
            planning_response_action = {element: planning_response_action.get(element, "") for element in ["action", "description"]}
        # 确保所有必要字段都存在于planning_response_action中，即使某些字段可能为空

        execute_time = time.time() - start_time
        # 计算执行时间

        logger.info("****************")
        logger.info(planning_response_action)
        # 记录计划响应行动

        dict_to_write = {}
        # 准备写入的字典

        # 将相关信息填充到dict_to_write中
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

        thought = planning_response_thought
        action = planning_response_action["description"].get('action')
        current_trace  = {"thought":{thought},"action":action}
        # 更新当前追踪记录

        return dict_to_write
        # 返回写入字典
    
