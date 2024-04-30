import time
import json5
import requests
from agent.Environment.html_env.async_env import AsyncHTMLEnvironment, ActionExecutionError
from evaluate import *
from agent.Plan import *
from playwright.async_api import Playwright, async_playwright, expect, Page
from agent.Environment.html_env.actions import create_action, Action, ActionTypes

import re
import asyncio
import argparse
import toml

# universal tools
from agent.Utils.utils import *
# evaluate tools
from evaluate_utils import *


def read_file(file_path="./data/data_update_0326/group_sample_all_data_0327.json"):
    '''读取标签数据'''
    return_list = []
    with open(file_path, encoding='utf-8') as f:
        test_data = json5.load(f)
    for task in test_data:
        task_name = task["task"]
        evaluation_data = task["evaluation"]
        reference_task_length = task["reference_task_length"]
        task_name_id = task["index"]
        reference_evaluate_steps = []
        for _, evaluation in enumerate(evaluation_data):
            match_function = evaluation["match_function_name"]
            if "url" in match_function:
                key = evaluation["content"]["key"]
                reference_answer = evaluation["content"]["reference_answer"]
                reference_evaluate_steps.append({"match_function": match_function,
                                                 "key": key, "reference_answer": reference_answer, "score": 0})
            elif "element_path" in match_function:  # TODO
                reference_answer = evaluation["content"]["reference_answer"]
                method = evaluation["method"]
                netloc = evaluation["content"]["netloc"]
                reference_evaluate_steps.append({"match_function": match_function, "method": method,
                                                 "reference_answer": reference_answer, "netloc": netloc,
                                                 "score": 0})

            elif "element_value" in match_function:
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
        return_list.append(
            [task_name, task_name_id, reference_task_length, reference_evaluate_steps])
    # print(return_list)
    # return_list=return_list[1:]
    return return_list


def get_netloc(url: str) -> str:
    '''提取出域名，如zhihu.com提取出zhihu，www.google.com.hk提取出google'''
    url = urlparse(url)
    try:
        if url.netloc.startswith("www"):
            netloc = re.findall(".*?\.(.*?)\..*?", url.netloc)[0]
        else:
            netloc = re.findall("(.*?)\..*?", url.netloc)[0]
    except:
        netloc = ""
    return netloc


async def get_element_content(page: Page, selector):
    '''获取元素内容'''
    try:
        tag_name = await page.eval_on_selector(selector, "element => element.tagName.toLowerCase()")
        if tag_name in ["input", "textarea"]:
            return await page.input_value(selector)
        else:
            return await page.text_content(selector)
    except:
        return ""


async def step_evaluate(page: Page, evaluate_steps=[], input_path=None, element_value=None):
    '''评测步骤打分'''
    step_score = 0
    match_result = []
    for evaluate in evaluate_steps:
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
                # * 暂时不做

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
                            # print("value评测中path不匹配")
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
                            # print("value评测中path不匹配")
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
                                # print("value评测中path不匹配")
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
            elif match_function == "text_exact_match":
                pass  # TODO
            elif match_function == "text_include_match":
                pass
            elif match_function == "text_semantic_match":
                pass

            evaluate["score"] = max(evaluate["score"], score)
        if evaluate["score"] >= 1:
            match_result.append(
                {evaluate["match_function"]: evaluate["reference_answer"]})
        step_score += evaluate["score"]
    # print("current step score:", step_score, "/", len(evaluate_steps))
    # print("current step match result:", match_result)
    return evaluate_steps, match_result
    # print(evaluate_steps)


async def aexec_playwright(code, page):
    '''async执行playwright代码'''
    exec(
        f'async def __ex(page): ' +
        ''.join(f'\n {l}' for l in code.split('\n'))
    )
    # Get `__ex` from local variables, call it and return the result
    return await locals()['__ex'](page)


def parse_current_trace(response: dict, env: AsyncHTMLEnvironment):
    thought = response["description"].get("thought")
    action_type = response['action_type']
    acton_input = response['value']
    action = response["description"].get("action")
    reflection = response["description"].get("reward").get(
        "description") if response["description"].get("reward") else ""
    current_trace = {"thought": thought,
                     "action": action, "reflection": reflection}
    element_value = ""
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
    else:
        selector = None
        element_id = 0
    execute_action = create_action(
        elementid=element_id, action_type=action_type, action_input=acton_input)
    return execute_action, current_trace, selector, element_value


async def get_observation(mode: str, env: AsyncHTMLEnvironment, action: Action):
    if mode in ["d_v", "dom_v_desc", "vision_to_dom"]:
        await env.execute_action(action)
        observation, observation_VforD = await env.get_obs()
        return observation, observation_VforD
    else:
        await env.execute_action(action)
        observation = await env.get_obs()
        return observation


async def main(num_steps=0,
               global_reward_mode="no_global_reward",
               text_model_name="gpt-4-turbo",
               global_reward_text_model_name="gpt-4-turbo",
               json_model_response=False,
               mode="dom",
               ground_truth_mode=False,
               file_path=None):
    # result record for experiments_tasks
    record_time_short = time.strftime("%Y%m%d", time.localtime())
    record_time = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    write_result_file_path = f"./csv_results/group_sample_{record_time_short}/{record_time}_{mode}_{text_model_name}_{global_reward_mode}_{ground_truth_mode}"

    # get reference data in experiment_tasks mode
    file = None
    ground_truth_data = None
    if task_mode == "experiment_tasks":
        file = read_file(file_path=file_path)
    if ground_truth_mode:
        ground_truth_data = read_json_file(ground_truth_file_path)

    with open('./configs/dom.toml', 'r') as f:
        config = toml.load(f)

    # 评测输入范围内的任务
    if raw_data_index != -1:
        re_result = re.split(r'\s|,', raw_data_index)
        raw_data_start_index = int(re_result[0])
        raw_data_end_index = int(re_result[-1]) + 1
    else:
        raw_data_start_index = 0
        raw_data_end_index = len(file)
    print(raw_data_start_index, raw_data_end_index)

    # start_index = 1
    score_dif = [31]
    # for task_index in score_dif:
    # for task_index in range(raw_data_start_index, raw_data_end_index):

    if task_mode == "experiment_tasks":
        task_range = range(8, raw_data_end_index)
        task_range1 = score_dif
    elif task_mode == "single_task":
        task_range = range(0, 1)

    for task_index in task_range:
        response_error_count = 0
        response_total_count = 0
        task_uuid = None
        if task_mode == "experiment_tasks":
            task = file[task_index]
            task_name, task_uuid, reference_task_length, reference_evaluate_steps = task
            logger.info("*" * 100)
            logger.info(f"Start")
            logger.info(f"task index: {task_index}")
            logger.info(f"task name: {task_name}")
            logger.info(f"task reference length: {reference_task_length}")
            logger.info(f"raw data annotation: {reference_evaluate_steps}")
        elif task_mode == "single_task":
            task_name = single_task
            reference_task_length = 10
            reference_evaluate_steps = []
            logger.info(f"task_name: {task_name}")

        # 创建html环境
        env = AsyncHTMLEnvironment(
            mode=mode,
            max_page_length=8192,
            headless=False,
            slow_mo=1000,
            current_viewport_only=False,
            viewport_size={"width": 1920, "height": 1280} if mode == "dom" else {
                "width": 1080, "height": 720},
            save_trace_enabled=False,
            sleep_after_execution=0.0,
            locale="en-US",
            use_vimium_effect=True
        )

        await env.reset("about:blank")

        vision_reward = None

        # html 环境相关
        observation = ""
        observation_VforD = ""
        error_description = ""
        previous_trace = []

        # response 相关
        out_put = None
        invalid_vision_reward_num = 0

        # 如果都匹配到了，任务完成
        evaluate_steps = reference_evaluate_steps
        task_finished = False
        task_global_status = ""
        human_interaction_stop_status = False

        # 控制步骤长度相关配置
        conditions = config["conditions"]
        increase_step = config["basic"]["Condition_Step_Increase"]
        encountered_errors = set()
        current_info = {"URL": env.page.url}
        num_steps = 0
        max_steps = int(
            max(config['basic']['Max_Action_Step'], 1.5*reference_task_length))
        additional_steps = 0

        # planning 后的结果信息保存
        task_result = {}
        task_result["task_name"] = task_name
        task_result["id"] = task_uuid
        task_result["reference_task_length"] = reference_task_length
        steps_list = []

        while num_steps < max_steps + additional_steps:
            error_message = ""
            total_step_score = 0
            logger.info(
                "**🤖 The agent is in the process of starting planning🤖 **")
            for _ in range(3):
                response_total_count += 1
                try:
                    out_put = await Planning.plan(user_request=task_name,
                                                  text_model_name=text_model_name,
                                                  global_reward_text_model_name=global_reward_text_model_name,
                                                  json_model_response=json_model_response,
                                                  previous_trace=previous_trace,
                                                  observation=observation,
                                                  feedback=error_description,
                                                  mode=mode,
                                                  observation_VforD=observation_VforD,
                                                  ground_truth_mode=ground_truth_mode,
                                                  ground_truth_data=ground_truth_data,
                                                  task_name_id=task_uuid,
                                                  global_reward_mode=global_reward_mode,
                                                  current_info=current_info)

                    if out_put is not None:
                        break
                except Exception as e:
                    out_put = None
                    response_error_count += 1
                    traceback.print_exc()
                    continue

            if out_put:
                each_step_dict = {}
                each_step_dict["step_index"] = num_steps
                each_step_dict["dict_result"] = out_put
                execute_action, current_trace, path, element_value = parse_current_trace(
                    out_put, env)
                selector, xpath = (
                    path[0], path[1]) if path is not None else (None, None)

                each_step_dict["current_trace"] = current_trace
                each_step_dict["selector"] = selector
                each_step_dict["execute_action"] = execute_action
                each_step_dict["element_value"] = element_value

                logger.info(f"-- Planning output: {out_put}")
                logger.info(f"-- Current trace: {current_trace}")
                logger.info(f"-- Action: {execute_action}")
                logger.info(f"-- Selector: {selector}")
                logger.info(f"-- Element value: {element_value}")

                logger.info(
                    "**🤖 The agent is in the process of starting evaluation 🤖**")

                evaluate_steps, match_result = await step_evaluate(page=env.page, evaluate_steps=evaluate_steps, input_path=selector)
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
                if out_put["description"].get("reward"):
                    each_step_dict["step_reward"] = out_put["description"].get(
                        "reward")
                    task_global_status = out_put["description"].get(
                        "reward").get("status")
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

                # 执行动作后的url
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
                    f"**🤖 Time Step: {num_steps+1}, Total steps: {max_steps + additional_steps} 🤖**")
                step_increase, encountered_errors = await adjust_max_action_step(
                    conditions, current_info, encountered_errors, increase_step)
                additional_steps += step_increase
                num_steps += 1
                steps_list.append(each_step_dict)
                if num_steps >= 25 or task_global_status == "finished" or task_finished:  # 防止无限循环
                    break

            # a = input(
            #     "Press Enter to proceed to the next action, or type 'q' to quit")
            # if a == "q":
            #     human_interaction_stop_status = True
            #     break
            logger.info(
                "Press Enter to proceed to the next action, or type 'q' to quit the task: ")
            a = input()
            if a.lower() == "q":
                logger.info("User requested to quit the program.")
                human_interaction_stop_status = True
                break

        # ! 3.任务评测打分
        if mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"]:
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
                f"Response error rate: {response_error_count/response_total_count}")

            # finish score
            finish_task_score = FinishTaskEvaluator.finish_task_score(
                len(reference_evaluate_steps), total_step_score)
            logger.info(f"Finish task score: {finish_task_score}")

            # 保存任务完成的状态
            if task_finished:
                task_result["status"] = "finished"
            elif task_global_status == "finished":
                task_result["status"] = "llm_finished"
            elif human_interaction_stop_status:
                task_result["status"] = "early_stop"
            else:
                task_result["status"] = "step_limit"

            task_result["LLM_error_rate"] = str(
                response_error_count/response_total_count)
            task_result["step_list"] = steps_list
            task_result["evaluate_steps"] = reference_evaluate_steps

            json_result_folder = write_result_file_path
            if not os.path.exists(json_result_folder):
                os.makedirs(json_result_folder)
            json_out_file_path = os.path.join(
                json_result_folder, str(task_index) + "_" + task_result["id"] + ".json")
            logger.info(f"Write results to json file: {json_out_file_path}")
            with open(json_out_file_path, 'w') as json_file:
                json.dump(task_result, json_file)

        await env.close()
        del env
        # if a == "q":
        #     break

    print(f"\033[31mtask finished!\033[0m")  # 红色
    input(f"\033[31m按回车键结束\033[0m")


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="Run the agent in different observation modes.")
    parser.add_argument("--observation_mode", choices=["dom", "dom_v_desc", "vision_to_dom", "vision", "d_v"],
                        default="dom",
                        help="Choose interaction mode: "
                             "'dom' for DOM-based interaction, "
                             "'dom_v_desc' for DOM-based interaction with vision description,"
                             "'vision_to_dom' for vision-to-dom interaction, "
                             "'vision' for vision-based interaction, "
                             "'d_v' for DOM-based and vision-based interaction.")
    parser.add_argument("--ground_truth_mode", choices=[True, False],
                        default=False, help="Choose whether to use ground truth data.")
    parser.add_argument("--global_reward_mode",
                        choices=["dom_vision_reward",
                                 "dom_reward",
                                 "vision_reward",
                                 "no_global_reward"],
                        default="dom_reward", help="Choose the mode of global reward.")
    parser.add_argument("--index", "--i", type=str, default=-1)
    args = parser.parse_args()
    interaction_mode = args.observation_mode
    raw_data_index = args.index
    # setting is below
    task_mode = "experiment_tasks"  # "experiment_tasks" or "single_task"
    single_task = "Browse cafes that have outdoor seating and is dog friendly in yelp"
    # - setting: file path of experiment_tasks reference data
    if args.ground_truth_mode:
        # ground_truth_file_path = "./data/ground_truth/GTR_tasks_instructions_0329_FOR_sample_all_data_0327.json"
        ground_truth_file_path = "./data/ground_truth/GT_instructions_202404161811_for_all_data_0328.json"
        # check if ground_truth_file_path exists
        if not os.path.exists(ground_truth_file_path):
            print("ground_truth_file_path not exist!")
            exit()

    # "./data/data_update_0326/group_sample_all_data_0327.json"
    asyncio.run(main(global_reward_mode=args.global_reward_mode,
                     text_model_name="gpt-3.5-turbo",
                     global_reward_text_model_name="gpt-3.5-turbo",
                     json_model_response=True,
                     mode=interaction_mode,
                     ground_truth_mode=args.ground_truth_mode,
                     file_path="./data/data_0328/all_data_0328.json"))
