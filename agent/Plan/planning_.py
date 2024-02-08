from agent.Prompt import *
from agent.LLM import *
from .action import *
import time

import logging
import time

current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
logger = logging.getLogger(f"{__name__}_{current_time}")

llm_models = {
    "GPT4": GPTGenerator4,
    "GPT3": GPTGenerator35,
    "GPT4V": GPTGenerator4V
}


async def get_reward_response(user_request: str = "", previous_trace: list = None, model_str: str = "GPT4"):
    model = llm_models[model_str]
    reward_response = ""
    status_and_description = None
    if previous_trace:
        stringfy_thought_and_action_output = ObservationPromptConstructor(
        ).stringfy_thought_and_action(previous_trace)
        reward_request = RewardPromptConstructor().construct(
            user_request, stringfy_thought_and_action_output)
        logger.info(f"Global_reward_Request{reward_request}")
        reward_response, error_message = await model.request(reward_request)
        status_and_description = ActionParser.extract_status_and_description(
            reward_response)
        logger.info(f"Global_Reward_Response:\n{reward_response}")
    return reward_response, status_and_description


async def get_planning_response(mode, user_request, previous_trace, observation, observation_VforD, feedback, status_description):
    planning_constructors = {
        "dom": ObservationPromptConstructor,
        "d_v": D_VObservationPromptConstructor,
        "vision": VisionObservationPromptConstructor
    }
    planning_request = planning_constructors[mode]().construct(
        user_request, previous_trace, observation, observation_VforD, feedback, status_description)
    logger.info(planning_request)
    gpt_instance = GPT4 if mode != "vision" else GPT4V
    return await gpt_instance.request(planning_request)


def extract_planning_response(planning_response, mode, planning_response_thought, planning_response_action, reward_response):
    planning_response_action = {element: planning_response_action.get(element, "") for element in ["element_id", "action", "action_input", "description"]} if mode in {
        "dom", "d_v"} else {element: planning_response_action.get(element, "") for element in ["action", "description"]}

    description = {
        "reward": reward_response if reward_response else None,
        "thought": planning_response_thought,
        "action": (
            f'{planning_response_action["action"]}: {planning_response_action["action_input"]}' if "description" not in planning_response_action.keys() else
            planning_response_action["description"])
        if mode in {"dom", "d_v"} else (
            planning_response_action["action"] if "description" not in planning_response_action.keys() else
            planning_response_action["description"])
    }
    planning_response_action["description"] = description
    return planning_response_action


async def plan(uuid, user_request, previous_trace, observation, feedback, mode, observation_VforD, global_reward=True):
    start_time = time.time()
    GPT35 = GPTGenerator35()
    GPT4 = GPTGenerator4()
    GPT4V = GPTGenerator4V()

    reward_response, status_and_description = await get_reward_response(previous_trace, user_request)
    status_description = status_and_description.get("description", "")

    planning_response, error_message = await get_planning_response(mode, user_request, previous_trace, observation, observation_VforD, feedback, status_description)

    logger.info(f"Openai_Planning_Response:\n{planning_response}")

    planning_response_thought, planning_response_action = ActionParser(
    ).extract_thought_and_action(planning_response)

    if planning_response_action.get('action') == "fill_form":
        JudgeSearchbarRequest = JudgeSearchbarPromptConstructor().construct(
            input_element=observation, planning_response_action=planning_response_action)
        Judge_response, error_message = await GPT35.request(JudgeSearchbarRequest)
        if Judge_response.lower() == "yes":
            planning_response_action['action'] = "fill_search"

    planning_response_action = extract_planning_response(
        planning_response, mode, planning_response_thought, planning_response_action, reward_response)

    execute_time = time.time() - start_time
    logger.info("****************")
    logger.info(planning_response_action)

    dict_to_write = {
        'uuid': uuid,
        'id': planning_response_action.get('element_id', None) if mode in {"dom", "d_v"} else None,
        'action_type': planning_response_action['action'] if mode in {"dom", "d_v"} else planning_response_action['action'],
        'value': planning_response_action.get('action_input', None) if mode in {"dom", "d_v"} else None,
        'description': planning_response_action['description'],
        'execute_time': execute_time,
        'error_message': error_message,
        'openai_response': planning_response
    }
    return dict_to_write
