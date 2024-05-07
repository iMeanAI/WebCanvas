from ..Utils.utils import print_info, print_limited_json
from agent.Prompt import *
from agent.LLM import *
from .action import *
import time
import json5
from .action import ResponseError
from logs import logger


class InteractionMode:
    def __init__(self, text_model=None, visual_model=None):
        self.text_model = text_model
        self.visual_model = visual_model

    def execute(self, status_description, user_request, previous_trace, observation, feedback, observation_VforD):
        pass

    async def get_global_reward(self, user_request, previous_trace, observation, current_info, ground_truth_mode,
                                global_reward_mode, ground_truth_data=None, task_name_id=None):
        status_and_description = None
        if len(previous_trace) > 0:
            stringfy_thought_and_action_output = PlanningPromptConstructor().stringfy_thought_and_action(
                previous_trace)
            if not ground_truth_mode:
                reward_request = RewardPromptConstructor().construct(
                    ground_truth_mode=ground_truth_mode,
                    global_reward_mode=global_reward_mode,
                    user_request=user_request,
                    stringfy_thought_and_action_output=stringfy_thought_and_action_output,
                    observation=observation,
                    current_info=current_info)
            elif ground_truth_mode:
                for item in ground_truth_data:
                    if item.get("index") == task_name_id:
                        instruction = item["instruction"]
                        reward_request = RewardPromptConstructor().construct(
                            ground_truth_mode=ground_truth_mode,
                            global_reward_mode=global_reward_mode,
                            user_request=user_request,
                            stringfy_thought_and_action_output=stringfy_thought_and_action_output,
                            observation=observation,
                            current_info=current_info,
                            instruction=instruction)
                        break
                else:
                    logger.info("No task found in the ground truth data.")
                    reward_request = RewardPromptConstructor().construct(
                        ground_truth_mode="false",
                        global_reward_mode=global_reward_mode,
                        user_request=user_request,
                        stringfy_thought_and_action_output=stringfy_thought_and_action_output,
                        observation=observation,
                        current_info=current_info)
            print_info(
                f"Global_Reward_Request:\n{print_limited_json(reward_request, limit=1000)}", "\033[32m")  # 绿色
            reward_response = ""
            for i in range(3):
                try:
                    if "vision" in global_reward_mode:
                        # TODO
                        reward_response, error_message = await self.visual_model.request(reward_request)
                    else:
                        print_info(f"using gpt_global_reward_text: {self.text_model.model}", "purple")
                        reward_response, error_message = await self.text_model.request(reward_request)
                    status_and_description = ActionParser().extract_status_and_description(
                        reward_response)
                    break
                except Exception as e:
                    logger.error(traceback.format_exc())
                    # traceback.print_exc()
                    logger.info(
                        f"planning reward_response or status_and_description error for {i+1} times")
                    # print(
                    #     f"planning reward_response or status_and_description error for {i+1} times")
                    continue
            # print(f"\033[34mGlobal_Reward_Response:\n{reward_response}")  # 蓝色
            logger.info(
                f"\033[34mGlobal_Reward_Response:\n{reward_response}\033[34m")
        else:
            reward_response = ""
        return reward_response, status_and_description


class DomMode(InteractionMode):
    def __init__(self, text_model=None, visual_model=None):
        super().__init__(text_model, visual_model)

    async def execute(self, status_description, user_request, previous_trace, observation, feedback, observation_VforD):
        planning_request = PlanningPromptConstructor().construct(
            user_request, previous_trace, observation, feedback, status_description)
        # print(f"\033[32m{planning_request}")  # 绿色
        # print("\033[0m")
        logger.info(
            f"\033[32mDOM_based_planning_request:\n{planning_request}\033[0m")
        print_info(f"gpt_planning_text_model: {self.text_model.model}", "purple")
        planning_response, error_message = await self.text_model.request(planning_request)
        return planning_response, error_message, None, None


class DomVDescMode(InteractionMode):
    def __init__(self, text_model=None, visual_model=None):
        super().__init__(text_model, visual_model)

    async def execute(self, status_description, user_request, previous_trace, observation, feedback, observation_VforD):
        # dom_v_desc模式的代码
        if observation_VforD != "":
            vision_desc_request = VisionDisc2PromptConstructor().construct(
                user_request, observation_VforD)  # vision description request with user_request
            # vision_desc_request = VisionDisc1PromptConstructor().construct(observation_VforD)
            vision_desc_response, error_message = await self.visual_model.request(vision_desc_request)
        else:
            vision_desc_response = ""
        print(f"\033[36mvision_disc_response:\n{vision_desc_response}")  # 蓝色
        planning_request = ObservationVisionDiscPromptConstructor().construct(
            user_request, previous_trace, observation, feedback, status_description, vision_desc_response)
        # print(f"\033[32m{planning_request}")
        # 紫色
        print(
            f"\033[35mplanning_request:\n{print_limited_json(planning_request, limit=10000)}")
        print("\033[0m")
        planning_response, error_message = await self.text_model.request(planning_request)
        return planning_response, error_message, None, None


class VisionToDomMode(InteractionMode):
    def __init__(self, text_model=None, visual_model=None):
        super().__init__(text_model, visual_model)

    async def execute(self, status_description, user_request, previous_trace, observation, feedback, observation_VforD):
        # vision_to_dom模式的代码
        vision_act_request = ObservationVisionActPromptConstructor().construct(
            user_request, previous_trace, observation_VforD, feedback, status_description)
        max_retries = 3  # 设置最大重试次数为3
        for attempt in range(max_retries):
            vision_act_response, error_message = await self.visual_model.request(vision_act_request)
            # 蓝色输出
            print(f"\033[36mvision_act_response:\n{vision_act_response}")
            print("\033[0m")  # 重置颜色
            planning_response_thought, planning_response_get = ActionParser().extract_thought_and_action(
                vision_act_response)
            actions = {
                'goto': "Found 'goto' in the vision_act_response.",
                'google_search': "Found 'google_search' in the vision_act_response.",
                'switch_tab': "Found 'switch_tab' in the vision_act_response.",
                'scroll_down': "Found 'scroll_down' in the vision_act_response.",
                'scroll_up': "Found 'scroll_up' in the vision_act_response.",
                'go_back': "Found 'go_back' in the vision_act_response."
            }
            # 检查行为是否在预定义的行为列表中
            actions_found = False
            for action, message in actions.items():
                if action == planning_response_get.get('action'):
                    print(message)
                    actions_found = True
                    # action无需改变
                    # `target_element`应该没有，有的话是用不到的
                    break

            # 如果没有找到预定义的行为
            if not actions_found:
                print("None of 'goto', 'google_search', 'switch_tab', 'scroll_down', 'scroll_up', or 'go_back' were found in the vision_act_response.")

                target_element = planning_response_get.get('target_element')
                description = planning_response_get.get('description')

                # 如果目标元素为空或不存在
                if not target_element:
                    print("The 'target_element' is None or empty.")
                    continue  # 继续下一次循环尝试

                # 构建视觉到DOM的请求
                planning_request = VisionToDomPromptConstructor().construct(target_element, description,
                                                                            observation)
                print(f"\033[35mplanning_request:{planning_request}")
                print("\033[0m")

                # 发送请求并等待响应
                planning_response_dom, error_message = await self.text_model.request(planning_request)
                print(
                    f"\033[34mVisionToDomplanning_response:\n{planning_response_dom}")
                print("\033[0m")
                # 解析元素ID
                element_id = ActionParser().get_element_id(planning_response_dom)
                if element_id == "-1":
                    print("The 'element_id' is not found in the planning_response.")
                    continue  # 如果未找到元素ID，则继续下一次循环尝试
                else:
                    planning_response_get['element_id'] = element_id
                    break  # 如果找到元素ID，则退出循环

            else:
                # 如果找到了预定义的行为，则不需要重试，直接退出循环
                break

        planning_response_json_str = json5.dumps(
            planning_response_get, indent=2)
        planning_response = f'```\n{planning_response_json_str}\n```'
        # 检查是否达到最大重试次数
        if attempt == max_retries - 1:
            print("Max retries of vision_act reached. Unable to proceed.")

        return planning_response, error_message, planning_response_thought, planning_response_get


class DVMode(InteractionMode):
    def __init__(self, text_model=None, visual_model=None):
        super().__init__(text_model, visual_model)

    async def execute(self, status_description, user_request, previous_trace, observation, feedback, observation_VforD):
        # d_v模式的代码
        planning_request = D_VObservationPromptConstructor().construct(
            user_request, previous_trace, observation, observation_VforD, feedback, status_description)

        print(
            f"\033[32mplanning_request:\n{print_limited_json(planning_request, limit=1000)}")
        print("\033[0m")
        planning_response, error_message = await self.visual_model.request(planning_request)
        return planning_response, error_message, None, None


class VisionMode(InteractionMode):
    def __init__(self, text_model=None, visual_model=None):
        super().__init__(text_model, visual_model)

    async def execute(self, status_description, user_request, previous_trace, observation, feedback, observation_VforD):
        # vision模式的代码
        planning_request = VisionObservationPromptConstructor(
        ).construct(user_request, previous_trace, observation)
        print(f"\033[32m{planning_request}")  # 绿色
        print("\033[0m")
        logger.info("\033[32m%s\033[0m", planning_request)
        planning_response, error_message = await self.visual_model.request(planning_request)
        return planning_response, error_message, None, None


class Planning:
    @staticmethod
    async def plan(user_request,
                   text_model_name,
                   global_reward_text_model_name,
                   json_model_response, previous_trace, observation, feedback, mode, observation_VforD, ground_truth_mode, ground_truth_data, task_name_id, global_reward_mode, current_info):

        # 创建GPT查询类
        gpt35 = GPTGenerator35()
        gpt4 = GPTGenerator4()
        gpt4v = GPTGenerator4V()
        all_json_models = ["gpt-4-turbo",
                           "gpt-4-turbo-2024-04-09",
                           "gpt-4-turbo-preview",
                           "gpt-4-0125-preview",
                           "gpt-4-1106-preview",
                           "gpt-3.5-turbo",
                           "gpt-3.5-turbo-0125",
                           "gpt-3.5-turbo-preview"]
        if json_model_response:
            if text_model_name in all_json_models:
                gpt_planning_text = GPTGeneratorWithJSON(model=text_model_name)
                gpt_global_reward_text = GPTGeneratorWithJSON(model=global_reward_text_model_name)
            else:
                gpt_planning_text = GPTGenerator(model=text_model_name)
                gpt_global_reward_text = GPTGenerator(model=global_reward_text_model_name)
                logger.info(
                    "The text model does not support JSON mode.")
        else:
            gpt_planning_text = GPTGenerator(model=text_model_name)
            gpt_global_reward_text = GPTGenerator(model=global_reward_text_model_name)

        # get global reward
        reward_response = ""
        status_and_description = ""
        status_description = ""
        if global_reward_mode != "no_global_reward":
            reward_response, status_and_description = await InteractionMode(text_model=gpt_global_reward_text, visual_model=gpt4v).get_global_reward(
                user_request=user_request, previous_trace=previous_trace, observation=observation,
                current_info=current_info, ground_truth_mode=ground_truth_mode, global_reward_mode=global_reward_mode,
                ground_truth_data=ground_truth_data, task_name_id=task_name_id)
            # 构建planning prompt及查询
            status_description = status_and_description.get(
                "description") if status_and_description and status_and_description.get("description") else ""

        modes = {
            "dom": DomMode(text_model=gpt_planning_text),
            "dom_v_desc": DomVDescMode(visual_model=gpt4v, text_model=gpt_planning_text),
            "vision_to_dom": VisionToDomMode(visual_model=gpt4v, text_model=gpt_planning_text),
            "d_v": DVMode(visual_model=gpt4v),
            "vision": VisionMode(visual_model=gpt4v)
        }

        # planning_response_thought, planning_response_action 仅在vision_to_dom模式下有用
        planning_response, error_message, planning_response_thought, planning_response_action = await modes[mode].execute(
            status_description=status_description,
            user_request=user_request,
            previous_trace=previous_trace,
            observation=observation,
            feedback=feedback,
            observation_VforD=observation_VforD)

        logger.info(f"\033[34mOpenai_Planning_Response:\n{planning_response}\033[0m")
        if mode != "vision_to_dom":
            try:
                planning_response_thought, planning_response_action = ActionParser().extract_thought_and_action(
                    planning_response)
            except ResponseError as e:
                logger.error(f"Response Error:{e.message}")
                raise 

        if planning_response_action.get('action') == "fill_form":
            JudgeSearchbarRequest = JudgeSearchbarPromptConstructor().construct(
                input_element=observation, planning_response_action=planning_response_action)
            Judge_response, error_message = await gpt35.request(JudgeSearchbarRequest)
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
        logger.info("****************")
        # logger.info(planning_response_action)
        dict_to_write = {}
        if mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"]:
            dict_to_write['id'] = planning_response_action['element_id']
            dict_to_write['action_type'] = planning_response_action['action']
            dict_to_write['value'] = planning_response_action['action_input']
        elif mode == "vision":
            dict_to_write['action'] = planning_response_action['action']
        dict_to_write['description'] = planning_response_action['description']
        dict_to_write['error_message'] = error_message

        return dict_to_write

 