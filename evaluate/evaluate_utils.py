from evaluate import *
from agent.Plan import *
from playwright.async_api import Page
from agent.Environment.html_env.async_env import AsyncHTMLEnvironment, ActionExecutionError

import re
import toml
import json
import traceback
import os
from agent.Environment import ActionExecutionError, create_action
from agent.Plan import Planning
from agent.Utils.utils import save_screenshot, is_valid_base64
from agent.Reward.global_reward import GlobalReward
from evaluate import FinishTaskEvaluator, TaskLengthEvaluator, URLEvaluator, ElementEvaluator
from logs import logger


def read_file(file_path="./data/example/example_130.json"):
    """Read labeled data"""
    return_list = []
    with open(file_path, encoding='utf-8') as f:
        test_data = json5.load(f)
    for task in test_data:
        task_name = task["task"]
        evaluation_data = task["evaluation"]
        reference_task_length = task["reference_task_length"]
        task_name_id = task["index"]
        reference_evaluate_steps = []
        for i, evaluation in enumerate(evaluation_data):
            match_function = evaluation["match_function_name"]
            if "url" in match_function:
                try:
                    key = evaluation["content"]["key"]
                    reference_answer = evaluation["content"]["reference_answer"]
                    reference_evaluate_steps.append({"match_function": match_function,
                                                     "key": key, "reference_answer": reference_answer, "score": 0})
                except:
                    logger.error(
                        f"url error in task {task_name_id}, step {i}, match_function: {match_function}")
                    exit(1)
            elif "element_path" in match_function:
                try:
                    reference_answer = evaluation["content"]["reference_answer"]
                    method = evaluation["method"]
                    netloc = evaluation["content"]["netloc"]
                    reference_evaluate_steps.append({"match_function": match_function, "method": method,
                                                     "reference_answer": reference_answer, "netloc": netloc,
                                                     "score": 0})
                except:
                    logger.error(
                        f"element_path error in task {task_name_id}, step {i}, match_function: {match_function}")
                    exit(1)
            elif "element_value" in match_function:
                try:
                    reference_answer = evaluation["content"]["reference_answer"]
                    netloc = evaluation["content"]["netloc"]
                    if "path" in evaluation["content"].keys():
                        path = evaluation["content"]["path"]
                        reference_evaluate_steps.append({"match_function": match_function,
                                                         "reference_answer": reference_answer, "netloc": netloc,
                                                         "path": path, "score": 0})
                    else:
                        reference_evaluate_steps.append({"match_function": match_function,
                                                         "reference_answer": reference_answer, "netloc": netloc,
                                                         "score": 0})
                except:
                    logger.error(
                        f"element_value error in task {task_name_id}, step {i}, match_function: {match_function}")
                    exit(1)
            elif "final_answer" in match_function:
                try:
                    reference_answer = evaluation["content"]["reference_answer"]
                    reference_evaluate_steps.append({"match_function": match_function,
                                                     "reference_answer": reference_answer, "score": 0})
                except:
                    logger.error(
                        f"element_value error in task {task_name_id}, step {i}, match_function: {match_function}")
                    exit(1)
            elif "cache_data" in match_function:
                try:
                    reference_answer = evaluation["content"]["reference_answer"]
                    reference_evaluate_steps.append({"match_function": match_function,
                                                     "reference_answer": reference_answer, "score": 0})
                except:
                    logger.error(
                        f"element_value error in task {task_name_id}, step {i}, match_function: {match_function}")
                    exit(1)

        return_list.append(
            [task_name, task_name_id, reference_task_length, reference_evaluate_steps])

    return return_list


async def adjust_max_action_step(conditions, current_info, encountered_errors, increase_step):
    total_increase = 0
    for condition_type, keywords in conditions.items():
        for keyword in keywords:
            if keyword in current_info[condition_type] and keyword not in encountered_errors:
                print(
                    f"Detected '{keyword}' in {current_info[condition_type]}, suggesting increase by {increase_step} steps.")
                total_increase += increase_step
                encountered_errors.add(keyword)
    return total_increase, encountered_errors


def get_netloc(url: str) -> str:
    """Extract the domain name, for example, extract 'zhihu' from 'zhihu.com', extract 'google' from 'www.google.com.hk' """
    url = urlparse(url)
    try:
        if url.netloc.startswith("www"):
            netloc = re.findall(".*?\.(.*?)\..*?", url.netloc)[0]
        else:
            netloc = re.findall("(.*?)\..*?", url.netloc)[0]
    except:
        netloc = ""
    return netloc


async def step_evaluate(page: Page, evaluate_steps=[], input_path=None, element_value=None, text_content=None):
    """Evaluate step score"""
    step_score = 0
    match_result = []
    for evaluate in evaluate_steps:
        score = 0
        if evaluate["score"] != 1:
            match_function = evaluate["match_function"]
            if match_function == "url_exactly_match":
                score = URLEvaluator.url_exact_match(
                    page.url, evaluate["reference_answer"], evaluate["key"])
            elif match_function == "url_included_match":
                score = URLEvaluator.url_include_match(
                    page.url, evaluate["reference_answer"], evaluate["key"])
            elif match_function == "url_semantic_match":
                score = await URLEvaluator.url_semantic_match(
                    page.url, evaluate["reference_answer"], evaluate["key"])
                # print(score, "url_semantic_match")
            elif match_function == "element_path_exactly_match":
                input_netloc = get_netloc(page.url)
                method = evaluate["method"]
                score = ElementEvaluator.path_exact_match(
                    input_path, evaluate["reference_answer"], method, await page.content(), input_netloc,
                    evaluate["netloc"])
                # print(score, "path_exact_match:", input_path,
                #       "***", evaluate["reference_answer"])
            elif match_function == "element_path_included_match":
                pass
                # * Temporarily not doing

            elif match_function == "element_value_exactly_match":
                if input_path is not None and element_value is not None:
                    input_netloc = get_netloc(page.url)

                    # print(element_value)
                    # print(await page.locator(input_path).input_value())
                    if "path" in evaluate.keys():
                        path_score = ElementEvaluator.path_exact_match(input_path, evaluate["path"], "selector",
                                                                       await page.content(), input_netloc,
                                                                       evaluate["netloc"])
                        if path_score == 0:
                            # print("Path mismatch in value evaluation")
                            score = 0
                        else:
                            score = ElementEvaluator.element_value_exact_match(
                                element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                    else:
                        score = ElementEvaluator.element_value_exact_match(
                            element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                    # print(score, "element_value_exactly_match",
                    #       element_value, "*", evaluate["reference_answer"])
                else:
                    score = 0
            elif match_function == "element_value_included_match":
                if input_path is not None and element_value is not None:
                    input_netloc = get_netloc(page.url)
                    if "path" in evaluate.keys():
                        path_score = ElementEvaluator.path_exact_match(input_path, evaluate["path"], "selector",
                                                                       await page.content(), input_netloc,
                                                                       evaluate["netloc"])
                        if path_score == 0:
                            # print("Path mismatch in value evaluation")
                            score = 0
                        else:
                            score = ElementEvaluator.element_value_include_match(
                                element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                    else:
                        score = ElementEvaluator.element_value_include_match(
                            element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                    # print(score, "element_value_included_match",
                    #       element_value, "*", evaluate["reference_answer"])
                else:
                    score = 0
            elif match_function == "element_value_semantic_match":
                if input_path is not None and element_value is not None:
                    input_netloc = get_netloc(page.url)

                    if len(element_value) > 0:
                        if "path" in evaluate.keys():
                            path_score = ElementEvaluator.path_exact_match(input_path, evaluate["path"], "selector",
                                                                           await page.content(), input_netloc,
                                                                           evaluate["netloc"])
                            if path_score == 0:
                                # print("Path mismatch in value evaluation")
                                score = 0
                            else:
                                score = await ElementEvaluator.element_value_semantic_match(
                                    element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                        else:
                            score = await ElementEvaluator.element_value_semantic_match(
                                element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                        # print(score, "element_value_semantic_match",
                        #       element_value, "*", evaluate["reference_answer"])
                else:
                    score = 0
            elif match_function == "cache_data_exact_match":
                if text_content is not None and text_content != "":
                    score = TextEvaluator.text_exact_match(
                        text_content, evaluate["reference_answer"])
            elif match_function == "cache_data_included_match":
                if text_content is not None and text_content != "":
                    score = TextEvaluator.text_included_match(
                        text_content, evaluate["reference_answer"])
            elif match_function == "cache_data_semantic_match":
                if text_content is not None and text_content != "":
                    score = TextEvaluator.text_semantic_match(
                        text_content, evaluate["reference_answer"])
            elif match_function == "final_answer_exact_match":
                if text_content is not None and text_content != "":
                    score = TextEvaluator.text_exact_match(
                        text_content, evaluate["reference_answer"])
            elif match_function == "final_answer_included_match":
                if text_content is not None and text_content != "":
                    score = TextEvaluator.text_included_match(
                        text_content, evaluate["reference_answer"])
            elif match_function == "final_answer_semantic_match":
                if text_content is not None and text_content != "":
                    score = TextEvaluator.text_semantic_match(
                        text_content, evaluate["reference_answer"])

            evaluate["score"] = max(evaluate["score"], score)
        if evaluate["score"] >= 1:
            match_result.append(
                {evaluate["match_function"]: evaluate["reference_answer"]})
        step_score += evaluate["score"]

    return evaluate_steps, match_result


def parse_current_trace(response: dict, env: AsyncHTMLEnvironment, step_reward: dict):
    thought = response["description"].get("thought")
    action_type = response.get(
        'action_type') if response.get('action_type') else ""
    acton_input = response['value'] if response.get(
        'value') and isinstance(response.get('value'), str) else ""
    action = response["description"].get("action")
    reflection = step_reward.get(
        "description") if step_reward else ""
    current_trace = {"thought": thought,
                     "action": action, "reflection": reflection}
    element_value = ""
    text_content = ""
    selector = None
    try:
        element_id = int(response['id'])
    except:
        element_id = 0
    if action_type in ["fill_form", "fill_search", "click", "select_option"]:
        try:
            selector = env.tree.get_selector_and_xpath(
                env.tree.nodeDict[element_id])
            element_value = env.tree.get_element_value(
                env.tree.nodeDict[element_id])
            if action_type in ["fill_form", "fill_search"]:
                element_value = acton_input
        except:
            logger.info(
                "Failed to obtain element_id from the accessibility tree.")
            element_id = 0
            action_type = "None"
    elif action_type in ["get_final_answer", "cache_data"]:
        selector = None
        element_id = 0
        text_content = acton_input
    else:
        selector = None
        element_id = 0
    try:
        execute_action = create_action(
            elementid=element_id, action_type=action_type, action_input=acton_input)
    except Exception as e:
        logger.error(f"Create action error: {e}")
        execute_action = create_action(
            elementid=element_id, action_type="None", action_input="")
    return execute_action, current_trace, selector, element_value, text_content


def read_config(toml_path=None):
    """
    Reads a TOML configuration file from the given path or the default path
    and returns its content as a dictionary.

    Args:
        toml_path (str, optional): The path to the TOML configuration file.
                                           If None, use the default path.

    Returns:
        dict: The content of the configuration file.
    """
    if toml_path is None:
        # default_path = os.path.join(os.path.dirname(__file__), 'default_settings.toml')
        toml_path = 'configs/setting.toml'

    with open(toml_path, 'r') as f:
        config = toml.load(f)

    return config


async def run_task(
        mode,
        task_mode,
        task_name,
        task_uuid,
        config,
        write_result_file_path,
        reference_task_length,
        evaluate_steps,
        reference_evaluate_steps,
        env,
        global_reward_mode,
        global_reward_text_model,
        planning_text_model,
        ground_truth_mode,
        ground_truth_data,
        interaction_mode,
        task_index,
        record_time=None,
        token_pricing=None
):
    await env.reset("about:blank")

    response_error_count = 0
    response_total_count = 0
    vision_reward = None

    # Related to the HTML environment
    observation = ""
    observation_VforD = ""
    error_description = ""
    previous_trace = []

    # Related to response
    out_put = None
    invalid_vision_reward_num = 0

    # If all are matched, the task is completed
    task_finished = False
    task_global_status = ""
    human_interaction_stop_status = False

    # Configuration related to controlling the length of steps
    conditions = config["conditions"]
    increase_step = config["steps"]["batch_tasks_condition_step_increase"]
    encountered_errors = set()
    current_info = {"URL": env.page.url}
    num_steps = 0
    step_index = 0
    if task_mode == "single_task":
        max_steps = int(reference_task_length)
    elif task_mode == "batch_tasks":
        max_steps = int(
            max(config['steps']['batch_tasks_max_action_step'], 1.5 * reference_task_length))
    additional_steps = 0

    # Store the results of the planning process for a task
    task_result = {}
    task_result["task_name"] = task_name
    task_result["id"] = task_uuid
    task_result["reference_task_length"] = reference_task_length
    steps_list = []

    # Store the token counts of each step
    steps_token_counts = 0
    step_tokens = {"steps_tokens_record": [], "steps_token_counts": steps_token_counts}
    steps_planning_input_token_counts = 0
    steps_reward_input_token_counts = 0
    steps_planning_output_token_counts = 0
    steps_reward_output_token_counts = 0
    steps_input_token_counts = 0
    steps_output_token_counts = 0
    token_counts_filename = f"token_results/token_counts_{record_time}_{planning_text_model}_{global_reward_text_model}.json"

    while num_steps < max_steps + additional_steps:
        error_message = ""
        total_step_score = 0
        step_reward = {}
        status_description = ""
        planning_input_token_count = 0
        planning_output_token_count = 0
        reward_token_count = [0, 0]

        logger.info(
            "**🤖 The agent is in the process of starting planning 🤖**")

        if global_reward_mode != 'no_global_reward' and len(previous_trace) > 0:
            step_reward, status_description, reward_token_count = await GlobalReward.evaluate(
                config=config,
                model_name=global_reward_text_model,
                user_request=task_name,
                previous_trace=previous_trace,
                observation=observation,
                current_info=current_info,
                task_name_id=task_uuid,
                global_reward_mode=global_reward_mode,
                ground_truth_mode=ground_truth_mode,
                ground_truth_data=ground_truth_data,
            )

        for _ in range(3):
            response_total_count += 1
            try:
                out_put = await Planning.plan(
                    config=config,
                    user_request=task_name,
                    text_model_name=planning_text_model,
                    previous_trace=previous_trace,
                    observation=observation,
                    feedback=error_description,
                    mode=mode,
                    observation_VforD=observation_VforD,
                    status_description=status_description
                )

                if out_put is not None:
                    break
            except Exception as e:
                out_put = None
                response_error_count += 1
                traceback.print_exc()
                continue

        if out_put:
            planning_input_token_count += out_put.get("planning_token_count", [0, 0])[0]
            planning_output_token_count += out_put.get("planning_token_count", [0, 0])[1]
            each_step_dict = {}
            each_step_dict["step_index"] = step_index
            each_step_dict["dict_result"] = out_put
            execute_action, current_trace, path, element_value, text_content = parse_current_trace(
                out_put, env, step_reward)
            selector, xpath = (
                path[0], path[1]) if path is not None else (None, None)

            each_step_dict["current_trace"] = current_trace
            each_step_dict["selector"] = selector
            each_step_dict["execute_action"] = execute_action
            each_step_dict["element_value"] = element_value
            each_step_dict["text_content"] = text_content

            logger.info(f"-- Planning output: {out_put}")
            logger.info(f"-- Current trace: {current_trace}")
            logger.info(f"-- Action: {execute_action}")
            logger.info(f"-- Selector: {selector}")
            logger.info(f"-- Element value: {element_value}")

            logger.info(
                "**🤖 The agent is in the process of starting evaluation 🤖**")
            if task_mode == "batch_tasks":
                try:
                    evaluate_steps, match_result = await step_evaluate(page=env.page, evaluate_steps=evaluate_steps,
                                                                       input_path=selector, element_value=element_value, text_content=text_content)
                except Exception as ee:
                    logger.info(f"Current step evaluate error :{ee}")

                for evaluate in evaluate_steps:
                    total_step_score += evaluate["score"]

                each_step_dict["score"] = str(
                    total_step_score) + " / " + str(len(reference_evaluate_steps))
                each_step_dict["match_func_result"] = match_result

                logger.info(
                    f"-- Current evaluatation score: {total_step_score} / {len(reference_evaluate_steps)}")
                logger.info(
                    f"-- Current evaluate match result: {match_result}")

                # get status of the task with global reward
                if step_reward:
                    each_step_dict["step_reward"] = step_reward
                    task_global_status = step_reward.get("status")
                else:
                    each_step_dict["step_reward"] = {}

                if total_step_score == len(reference_evaluate_steps):
                    # steps_list.append(each_step_dict)
                    task_finished = True
                    # break

            logger.info(
                "**🤖 The agent is in the process of executing the action 🤖**")

            try:
                await env.execute_action(execute_action)
                previous_trace.append(current_trace)
                error_description = ""
                logger.info("-- Successfully execute the action ")
            except ActionExecutionError as ee:
                error_message = ee.message
                logger.info("-- Failed to execute the action")
                logger.error(
                    f"ActionExecutionError occurred: {error_message}")
                error_description = error_message

            if mode in ["d_v", "dom_v_desc", "vision_to_dom"]:
                observation, observation_VforD = await env.get_obs()
                save_screenshot(mode=mode, record_time=record_time, task_name=task_name,
                                step_number=num_steps, description="obs", screenshot_base64=observation_VforD)
            else:
                observation = await env.get_obs()

            # URL after executing the action
            each_step_dict["step_url"] = env.page.url
            each_step_dict["step_url"] = env.page.url
            each_step_dict["error_message"] = error_message
            each_step_dict["previous_trace"] = str(previous_trace)

            logger.info(
                f"-- The URL is: {env.page.url}")

            if "vision" in global_reward_mode:
                vision_reward = await env.capture()
                save_screenshot(mode=mode, record_time=record_time, task_name=task_name,
                                step_number=num_steps, description="reward",
                                screenshot_base64=vision_reward, task_uuid=task_uuid)
                is_valid, message = is_valid_base64(vision_reward)
                if not is_valid:
                    invalid_vision_reward_num += 1

            current_info = {
                "URL": env.page.url
            }
            if vision_reward:
                current_info.update({"vision_reward": vision_reward})
            logger.info(
                f"**🤖 Time Step: {num_steps + 1}, Total steps: {max_steps + additional_steps} 🤖**")
            step_increase, encountered_errors = await adjust_max_action_step(
                conditions, current_info, encountered_errors, increase_step)
            additional_steps += step_increase
            steps_list.append(each_step_dict)
            step_index += 1
            if num_steps >= 25 or task_global_status == "finished" or task_finished:
                break
        num_steps += 1
        if interaction_mode:
            logger.info(
                "Press Enter to proceed to the next action, or type 'q' to quit the task. If you encounter any unexpected issues such as network connection errors or captcha challenges, please resolve them manually now.")
            a = input()
            if a.lower() == "q":
                logger.info("User requested to quit the program.")
                human_interaction_stop_status = True
                break

        planning_token_count_number = planning_input_token_count + planning_output_token_count
        reward_token_count_number = reward_token_count[0] + reward_token_count[1]
        step_input_token_count = planning_input_token_count + reward_token_count[0]
        step_output_token_count = planning_output_token_count + reward_token_count[1]
        step_token_count = planning_token_count_number + reward_token_count_number
        single_step_tokens = {
            "planning_input_token_count": planning_input_token_count,
            "planning_output_token_count": planning_output_token_count,
            "planning_token_count": planning_token_count_number,
            "reward_input_token_count": reward_token_count[0],
            "reward_output_token_count": reward_token_count[1],
            "reward_token_count": reward_token_count_number,
            "input_token_count": step_input_token_count,
            "output_token_count": step_output_token_count,
            "token_count": step_token_count
        }

        step_tokens["steps_tokens_record"].append(single_step_tokens)

        steps_planning_input_token_counts += planning_input_token_count
        steps_planning_output_token_counts += planning_output_token_count
        steps_reward_input_token_counts += reward_token_count[0]
        steps_reward_output_token_counts += reward_token_count[1]
        steps_input_token_counts += step_input_token_count
        steps_output_token_counts += step_output_token_count
        steps_token_counts += step_token_count

    step_tokens["steps_planning_input_token_counts"] = steps_planning_input_token_counts
    step_tokens["steps_planning_output_token_counts"] = steps_planning_output_token_counts
    step_tokens["steps_reward_input_token_counts"] = steps_reward_input_token_counts
    step_tokens["steps_reward_output_token_counts"] = steps_reward_output_token_counts
    step_tokens["steps_input_token_counts"] = steps_input_token_counts
    step_tokens["steps_output_token_counts"] = steps_output_token_counts
    step_tokens["steps_token_counts"] = steps_token_counts

    save_token_count_to_file(token_counts_filename, step_tokens, task_name, global_reward_text_model,
                             planning_text_model, config["token_pricing"])

    # ! 3. Task evaluation and scoring
    if task_mode == "batch_tasks":
        # step score
        total_step_score = 0
        for evaluate in evaluate_steps:
            total_step_score += evaluate["score"]
        logger.info(
            f"Total step score: {total_step_score} / {len(reference_evaluate_steps)}")

        # length score
        task_evaluator = TaskLengthEvaluator()
        task_length_score = task_evaluator.task_length_score(
            reference_task_length, num_steps)

        logger.info(f"Task length score: {task_length_score}")
        logger.info(
            f"Response error rate: {response_error_count / response_total_count}")

        # finish score
        finish_task_score = FinishTaskEvaluator.finish_task_score(
            len(reference_evaluate_steps), total_step_score)
        logger.info(f"Finish task score: {finish_task_score}")

        # Save the status of the task
        if task_finished:
            task_result["status"] = "finished"
        elif task_global_status == "finished":
            task_result["status"] = "llm_finished"
        elif human_interaction_stop_status:
            task_result["status"] = "early_stop"
        else:
            task_result["status"] = "step_limit"

        task_result["LLM_error_rate"] = str(
            response_error_count / response_total_count)
        task_result["step_list"] = steps_list
        task_result["evaluate_steps"] = reference_evaluate_steps

        json_result_folder = write_result_file_path
        if not os.path.exists(json_result_folder):
            os.makedirs(json_result_folder)
        json_out_file_path = os.path.join(
            json_result_folder, str(task_index) + "_" + str(task_result["id"]) + ".json")
        logger.info(f"Write results to json file: {json_out_file_path}")
        with open(json_out_file_path, 'w') as json_file:
            json.dump(task_result, json_file)
