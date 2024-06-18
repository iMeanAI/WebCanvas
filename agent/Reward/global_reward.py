from ..Utils.utils import print_info, print_limited_json
from agent.Prompt import *
from agent.LLM import *
from agent.Plan.action import *
import time
import json5
from logs import logger


class InteractionMode:
    def __init__(self, text_model=None, visual_model=None):
        self.text_model = text_model
        self.visual_model = visual_model

    def execute(self, status_description, user_request, previous_trace, observation, feedback, observation_VforD):
        pass

    async def get_global_reward(self, user_request, previous_trace, observation, current_info, ground_truth_mode,
                                global_reward_mode, ground_truth_data=None, task_name_id=None):
        reward_response = None
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
                f"Global_Reward_Request:\n{print_limited_json(reward_request, limit=1000)}", "\033[32m")  # green
            response_str = ""
            for i in range(3):
                try:
                    if "vision" in global_reward_mode:
                        # TODO
                        response_str, error_message = await self.visual_model.request(reward_request)
                    else:
                        print_info(
                            f"using gpt_global_reward_text: {self.text_model.model}", "purple")
                        response_str, error_message = await self.text_model.request(reward_request)
                    reward_response = ActionParser().extract_status_and_description(
                        response_str)
                    break
                except Exception as e:
                    logger.error(traceback.format_exc())
                    # traceback.print_exc()
                    logger.info(
                        f"planning response_str or reward_response error for {i+1} times")
                    continue

            logger.info(
                f"\033[34mGlobal_response_str:\n{response_str}\033[34m")
        else:
            response_str = ""
        return response_str, reward_response


class GlobalReward:

    @staticmethod
    async def evaluate(
        config,
        model_name,
        user_request,
        previous_trace,
        observation,
        current_info,
        task_name_id,
        global_reward_mode,
        ground_truth_mode,
        ground_truth_data,
    ):

        gpt4v = GPTGenerator4V()

        all_json_models = config["model"]["All_JSON_Models"]
        is_json_response = config["model"]["JSON_Model_Response"]

        if is_json_response:
            if model_name in all_json_models:
                gpt_global_reward_text = GPTGeneratorWithJSON(
                    model=model_name)
            else:
                gpt_global_reward_text = GPTGenerator(
                    model=model_name)
                logger.info(
                    "The text model does not support JSON mode.")
        else:
            gpt_global_reward_text = GPTGenerator(
                model=model_name)
        _, reward_response = await InteractionMode(text_model=gpt_global_reward_text, visual_model=gpt4v).get_global_reward(
            user_request=user_request, previous_trace=previous_trace, observation=observation,
            current_info=current_info, ground_truth_mode=ground_truth_mode, global_reward_mode=global_reward_mode,
            ground_truth_data=ground_truth_data, task_name_id=task_name_id)
        description = reward_response.get(
            "description") if reward_response and reward_response.get("description") else ""
        return reward_response, description
