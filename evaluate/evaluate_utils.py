"""
The new version only supports Online-Mind2Web task testing
"""
from urllib.parse import urlparse
from playwright.async_api import Page
import re
import toml
import json5
import traceback
import os
from typing import List

from agent.Environment.html_env.async_env import AsyncHTMLEnvironment, ActionExecutionError
from agent.Environment import ActionExecutionError, create_action
from agent.Plan import Planning
from agent.Utils.utils import save_screenshot, is_valid_base64
from agent.Reward.global_reward import GlobalReward
from evaluate import FinishTaskEvaluator, TaskLengthEvaluator, URLEvaluator, ElementEvaluator, TextEvaluator
from logs import logger
import json


def save_token_count_to_file(filename, step_tokens, task_name, global_reward_text_model, planning_text_model, token_pricing):
    data = {
        "task_name": task_name,
        "global_reward_text_model": global_reward_text_model,
        "planning_text_model": planning_text_model,
        "token_pricing": token_pricing,
        "step_tokens": step_tokens
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f)        
        
def read_file(file_path: str = "./data/example/example_130.json") -> List[List]:
    """Read labeled data
    
    Args:
        file_path: Path to the JSON file containing labeled data
        
    Returns:
        List of tasks with their evaluation data
    """
    return_list = []
    try:
        with open(file_path, encoding='utf-8') as f:
            test_data = json5.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json5.JSONDecodeError:
        logger.error(f"Invalid JSON format in file: {file_path}")
        raise

    for task in test_data:
        # task_name = task["task"]
        task_name = task["confirmed_task"]
        # evaluation_data = task["evaluation"]
        evaluation_data = task.get("evaluation", [])
        # reference_task_length = task["reference_task_length"]
        reference_task_length = task["reference_length"]
        task_name_id = task["task_id"]
        reference_evaluate_steps = []
        if "evaluation" not in task:
            task["evaluation"] = []

        return_list.append(
            [task_name, task_name_id, reference_task_length, reference_evaluate_steps])

    return return_list


async def adjust_max_action_step(conditions, current_info, encountered_errors, increase_step):
    """Adjust maximum action steps based on conditions"""
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
    """Extract the domain name from URL
    
    Example: extract 'zhihu' from 'zhihu.com', extract 'google' from 'www.google.com.hk'
    """
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
    """Evaluate step score using traditional method"""
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

async def step_event_evaluate(page: Page, evaluate_steps, env):
    """Evaluate step score using event-based method"""
    step_score = 0
    match_result = []
    
    # Get latest events
    latest_events = env.get_latest_events()
    if not latest_events:
        return evaluate_steps, match_result
        
    event = latest_events[-1]  # Use the latest event
    
    for evaluate in evaluate_steps:
        if evaluate["score"] != 1:
            match_function = evaluate["match_function"]
            score = 0
            
            if match_function == "url_exactly_match":
                score = URLEvaluator.url_exact_match(
                    page.url, evaluate["reference_answer"], evaluate["key"]
                )
            elif match_function == "url_included_match":
                score = URLEvaluator.url_include_match(
                    page.url, evaluate["reference_answer"], evaluate["key"]
                )
            elif match_function == "url_semantic_match":
                score = URLEvaluator.url_semantic_match(
                    page.url, evaluate["reference_answer"], evaluate["key"]
                )

            elif match_function == "element_path_exactly_match":
                score = ElementEvaluator.path_exact_match(
                    event["selector"], 
                    evaluate["reference_answer"],
                    evaluate["method"],
                    page
                )

            elif match_function == "element_path_included_match":
                pass

            elif match_function == "element_value_exactly_match":
                score = ElementEvaluator.element_value_exact_match(
                    event["target_value"],
                    evaluate["reference_answer"]
                )

            elif match_function == "element_value_included_match":
                score = ElementEvaluator.element_value_include_match(
                    event["target_value"], evaluate["reference_answer"]
                )

            elif match_function == "element_value_semantic_match":
                score = ElementEvaluator.element_value_semantic_match(
                    event["target_value"], evaluate["reference_answer"]
                )

            evaluate["score"] = max(evaluate["score"], score)
            
        if evaluate["score"] >= 1:
            match_result.append({evaluate["match_function"]: evaluate["reference_answer"]})
        step_score += evaluate["score"]
    
    return evaluate_steps, match_result

def parse_current_trace(response: dict, env: AsyncHTMLEnvironment, step_reward: dict):
    """Parse current execution trace and prepare for evaluation"""
    thought = response["description"].get("thought")
    action_type = response.get('action_type') if response.get('action_type') else ""
    acton_input = response['value'] if response.get('value') and isinstance(response.get('value'), str) else ""
    action = response["description"].get("action")
    reflection = step_reward.get("description") if step_reward else ""
    current_trace = {"thought": thought, "action": action, "reflection": reflection}
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
    """Read configuration from TOML file
    
    Args:
        toml_path (str, optional): Path to the TOML configuration file.
                                 If None, use the default path.

    Returns:
        dict: Configuration content
    """
    if toml_path is None:
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
        token_pricing=None,
        screenshot_params=None,
        website=None,
        rag_enabled=False,
        rag_path=None,
):  
    await env.reset(website if website else "about:blank")

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
        # Force the first step to navigate to a specific website
        if num_steps == 0 and website and website != "about:blank":
            logger.info(f"**🤖 Force the first step to navigate to a specific website: {website} 🤖**")
            try:
                # Force navigation to a specific website
                await env.page.goto(website, wait_until="domcontentloaded", timeout=10000)
                logger.info(f"-- success: {website}")

                # Update current information
                current_info = {"URL": env.page.url}
                
                # Create a virtual navigation trace record
                navigation_trace = {
                    "thought": f"I need to navigate to the designated website to start the task",
                    "action": f"goto {website}",
                    "reflection": f"Successfully naviged to the specified website: {website}"
                }
                previous_trace.append(navigation_trace)
                
            except Exception as e:
                logger.error(f"-- fail: {e}")
                error_description = f"Failed to navigate to {website}: {str(e)}"
        
        # Screenshot at the beginning of each step
        if screenshot_params:
            if mode in ["d_v", "dom_v_desc", "vision_to_dom"]:
                observation, observation_VforD = await env.get_obs()
                if is_valid_base64(observation_VforD):
                    save_screenshot(
                        mode=screenshot_params["mode"],
                        record_time=screenshot_params["record_time"],
                        task_name=screenshot_params["task_name"],
                        step_number=num_steps,
                        description=f"step_{num_steps}",
                        screenshot_base64=observation_VforD,
                        task_name_id=screenshot_params.get("task_name_id")
                    )
            else:
                observation = await env.get_obs()
                if isinstance(observation, dict) and is_valid_base64(observation.get("screenshot", "")):
                    save_screenshot(
                        mode=screenshot_params["mode"],
                        record_time=screenshot_params["record_time"],
                        task_name=screenshot_params["task_name"],
                        step_number=num_steps,
                        description=f"step_{num_steps}",
                        screenshot_base64=observation["screenshot"],
                        task_name_id=screenshot_params.get("task_name_id")
                    )
            
            # save HTML(Optional)
            # html_content = await env.page.content()
            # html_save_path = os.path.join(screenshot_params["file_path"], "html_screenshots", f"{screenshot_params['task_name']}", 
            #                               f"step_{num_steps}_{screenshot_params['record_time']}.html")
            # os.makedirs(os.path.dirname(html_save_path), exist_ok=True)
            # with open(html_save_path, "w", encoding="utf-8") as html_file:
            #     html_file.write(html_content)
                
            # save screenshot
            png_save_path = os.path.join(screenshot_params["file_path"], "img_screenshots", f"{screenshot_params['task_name']}",
                                           f"step_{num_steps}_{screenshot_params['record_time']}.png")
            os.makedirs(os.path.dirname(png_save_path), exist_ok=True)
            png_bytes = await env.page.screenshot()
            with open(png_save_path, "wb") as png_file:
                png_file.write(png_bytes)
        
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
                    status_description=status_description,
                    rag_enabled=rag_enabled,
                    rag_path=rag_path
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
                    # Use event-based evaluation
                    evaluate_steps, match_result = await step_event_evaluate(
                        page=env.page,
                        evaluate_steps=evaluate_steps,
                        env=env
                    )
                    
                    # If event-based evaluation fails, revert to traditional evaluation
                    if not match_result:
                        evaluate_steps, match_result = await step_evaluate(
                            page=env.page,
                            evaluate_steps=evaluate_steps,
                            input_path=selector,
                            element_value=element_value,
                            text_content=text_content
                        )

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

                if total_step_score == len(reference_evaluate_steps) and len(reference_evaluate_steps) > 0:
                    task_finished = True

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
                if num_steps >= 25:
                    logger.info("**🤖 Breaking loop: Reached maximum step limit of 25 🤖**")
                elif task_global_status == "finished":
                    logger.info("**🤖 Breaking loop: Global reward status indicates task is finished 🤖**")
                elif task_finished:
                    logger.info("**🤖 Breaking loop: All evaluation steps matched successfully 🤖**")
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

    # Update token counting
    save_token_count_to_file(token_counts_filename, step_tokens, task_name, global_reward_text_model,planning_text_model, config["token_pricing"])

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