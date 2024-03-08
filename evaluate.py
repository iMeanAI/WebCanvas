import time
import json5
import requests
from agent.Environment.html_env.async_env import AsyncHTMLEnvironment
from agent.Environment.html_env.vision_async_env import VisionAsyncHTMLEnvironment
from evaluate import *
from agent.Plan import *
from playwright.async_api import Playwright, async_playwright, expect, Page
from agent.Environment.html_env.actions import create_action, Action, ActionTypes

import re
import asyncio
import argparse
import toml

from result import write_result_to_excel

# 解析命令行参数
parser = argparse.ArgumentParser(
    description="Run the agent in different modes.")
parser.add_argument("--mode", choices=["dom", "dom_v_desc", "vision_to_dom", "vision", "d_v"], default="dom",
                    help="Choose interaction mode: "
                         "'dom' for DOM-based interaction, "
                         "'dom_v_desc' for DOM-based interaction with vision description,"
                         "'vision_to_dom' for vision-to-dom interaction, "
                         "'vision' for vision-based interaction, "
                         "'d_v' for DOM-based and vision-based interaction.")
parser.add_argument("--index", "--i", type=str, default=-1)
args = parser.parse_args()
interaction_mode = args.mode
raw_data_index = args.index


def read_file(file_path="./data/group1.json"):
    '''读取标签数据'''
    return_list = []
    with open(file_path) as f:
        test_data = json5.load(f)
    for task in test_data:
        task_name = task["task"]
        evaluation_data = task["evaluation"]
        reference_task_length = task["reference_task_length"]
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
                                                 "reference_answer": reference_answer, "netloc": netloc, "score": 0})
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
            [task_name, reference_task_length, reference_evaluate_steps])
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
        # 获取元素的标签名
        tag_name = await page.eval_on_selector(selector, "element => element.tagName.toLowerCase()")

        if tag_name in ["input", "textarea"]:
            # 对于 input 或 textarea 元素
            return await page.input_value(selector)
        else:
            # 对于其他元素
            return await page.text_content(selector)
    except:
        return ""


async def step_evaluate(page: Page, evaluate_steps=[], input_path=None, element_value=None):
    '''评测步骤打分'''
    # reference_evaluate_steps, num_steps
    # num_steps += 1
    # page_url = html_env.page.url
    # page_url = page.url
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
                print(score, "url_semantic_match")
            elif match_function == "element_path_exactly_match":
                input_netloc = get_netloc(page.url)
                method = evaluate["method"]
                score = ElementEvaluator.path_exact_match(
                    input_path, evaluate["reference_answer"], method, await page.content(), input_netloc,
                    evaluate["netloc"])
                print(score, "path_exact_match:", input_path,
                      "***", evaluate["reference_answer"])
            elif match_function == "element_path_included_match":
                pass
                # * 暂时不做

            elif match_function == "element_value_exactly_match":
                if input_path is not None and element_value is not None:
                    input_netloc = get_netloc(page.url)

                    print(element_value)
                    # print(await page.locator(input_path).input_value())
                    if "path" in evaluate.keys():
                        path_score = ElementEvaluator.path_exact_match(input_path, evaluate["path"], "selector",
                                                                       await page.content(), input_netloc,
                                                                       evaluate["netloc"])
                        if path_score == 0:
                            print("value评测中path不匹配")
                            score = 0
                        else:
                            score = ElementEvaluator.element_value_exact_match(
                                element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                    else:
                        score = ElementEvaluator.element_value_exact_match(
                            element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                    print(score, "element_value_exactly_match",
                          element_value, "*", evaluate["reference_answer"])
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
                            print("value评测中path不匹配")
                            score = 0
                        else:
                            score = ElementEvaluator.element_value_include_match(
                                element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                    else:
                        score = ElementEvaluator.element_value_include_match(
                            element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                    print(score, "element_value_included_match",
                          element_value, "*", evaluate["reference_answer"])
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
                                print("value评测中path不匹配")
                                score = 0
                            else:
                                score = await ElementEvaluator.element_value_semantic_match(
                                    element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                        else:
                            score = await ElementEvaluator.element_value_semantic_match(
                                element_value, evaluate["reference_answer"], input_netloc, evaluate["netloc"])
                        print(score, "element_value_semantic_match",
                              element_value, "*", evaluate["reference_answer"])
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
    print("current step score:", step_score, "/", len(evaluate_steps))
    print("current step match result:", match_result)
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


async def parse_current_trace(response: dict, env: AsyncHTMLEnvironment):
    thought = response["description"].get("thought")
    action_type = response['action_type']
    acton_input = response['value']
    action = response["description"].get("action")
    current_trace = {"thought": thought, "action": action}
    element_value = None
    try:
        element_id = int(response['id'])
    except:
        element_id = 0
    #! env.tree.nodeDict[element_id]勿动，调用映射关系，否则selector会出错
    if action_type in ["fill_form", "fill_search", "click"]:
        try:
            selector = env.tree.get_selector_and_xpath(
                env.tree.nodeDict[element_id])

            if action_type in ["fill_form", "fill_search"]:
                element_value = acton_input
            else:
                element_value = await get_element_content(env.page, selector)
        except:
            print("accessibility tree don't have this element_id")
            selector = None
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


async def main(num_steps=0, mode="dom"):
    record_time = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    file = read_file()

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

    # for task_index in range(raw_data_start_index, raw_data_end_index):

    # # start_index = 1
    score_dif = [2, 3, 10, 15, 22, 32, 40, 47, 51,
                 54, 55, 63, 72, 75, 79, 87, 89, 101, 103, 105]
    # # for task_index in range(start_index, len(file)):
    # for task_index in [1]:
    for task_index in score_dif:
        task = file[task_index]
        task_name, reference_task_length, reference_evaluate_steps = task
        print("task index:", task_index)
        print("task_name:", task_name)
        print("reference_task_length:", reference_task_length)
        print("raw data:\n", reference_evaluate_steps)
        # #! # 1. playwright
        # # 用playwright运行浏览器
        # async def run(playwright: Playwright) -> None:
        #     '''用playwright运行浏览器'''
        #     evaluate_steps = reference_evaluate_steps
        #     browser = await playwright.chromium.launch(headless=False)
        #     context = await browser.new_context(locale="en-US")
        #     page = await context.new_page()
        #     replay_codes = open("./data/playwright/google_test.txt", "r", encoding="utf-8")
        #     for num_steps, line in enumerate(replay_codes):
        #         print("step:", num_steps, line)
        #         selector = None
        #         input_value = None
        #         if "page.locator" in line:
        #             # selector, action, action_value = re.findall('page.locator\("(.*?)"\).(*?)\((.*?)\)', line)
        #             selector, action = re.findall('page.locator\("(.*?)"\).(.*?)\(.*?\)', line)[0]
        #             print("selector:", selector)
        #             print("action:", action)
        #             if action == "fill":
        #                 input_value = re.findall('page.locator\(".*?"\).*?\("(.*?)"\)', line)[0]
        #                 print("input_value", input_value)
        #             else:
        #                 input_value = await get_element_content(page, selector)
        #         line = "await "+line
        #         print(line)
        #         evaluate_steps = await step_evaluate(page=page, evaluate_steps=evaluate_steps, input_path=selector, element_value=input_value)
        #         time.sleep(3)
        #         await aexec_playwright(line, page)
        #         time.sleep(2)
        #     return num_steps, evaluate_steps

        # async with async_playwright() as playwright:
        #     num_steps, evaluate_steps = await run(playwright)

        # ! # 2. planning
        if mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"]:
            env = AsyncHTMLEnvironment(
                mode=mode,
                max_page_length=8192,
                headless=False,
                slow_mo=1000,
                current_viewport_only=False,
                viewport_size={"width": 1920, "height": 1280} if mode == "dom" else {
                    "width": 1080, "height": 720},
                # "width": 1080, "height": 720
                save_trace_enabled=False,
                sleep_after_execution=0.0,
                locale="en-US",
                use_vimium_effect=True
            )
        elif mode == "vision":
            env = VisionAsyncHTMLEnvironment(
                # mode=mode,
                max_page_length=8192,
                headless=False,
                slow_mo=1000,
                current_viewport_only=False,
                viewport_size={"width": 1920, "height": 1280},
                save_trace_enabled=False,
                sleep_after_execution=0.0,
                locale="en-US",
                use_vimium_effect=True
            )

        DF = config['basic']['default']
        GR = config['basic']['global_reward']
        CR = config['basic']['current_step_reward']
        PT = config['basic']['previous_trace']

        observation = ""
        observation_VforD = ""
        await env.reset("about:blank")
        # if mode in ["d_v", "dom_v_desc", "vision_to_dom"]:
        #     observation, observation_VforD = await env.reset("about:blank")
        #     await env.reset("about:blank")
        # else:
        #     observation = await env.reset("about:blank")
        previous_trace = []
        evaluate_steps = reference_evaluate_steps
        last_action_description = ""
        dict_to_write = None
        step_index_list = []
        score_list = []
        step_reward_list = []
        dict_result_list = []
        url_list = []
        current_trace_list = []
        selector_list = []
        action_list = []
        previoust_trace_list = []
        match_func_result_list = []
        task_finished = False
        step_error_count = 0
        task_error = False
        for num_steps in range(max(config['basic']['Max_Action_Step'],1.5*reference_task_length)):
            step_index_list.append(num_steps)
            total_step_score = 0
            # break
            print("planning前previous_trace：", previous_trace)
            print("planning前observation：", observation)
            for _ in range(3):
                try:
                    if DF:
                        dict_to_write = await Planning.plan(uuid=1, user_request=task_name,
                                                            previous_trace=previous_trace, observation=observation,
                                                            feedback=last_action_description, mode=mode,
                                                            observation_VforD=observation_VforD)
                        if dict_to_write is not None:
                            break
                    elif GR == False:
                        dict_to_write = await Planning.plan(uuid=1, user_request=task_name,
                                                            previous_trace=previous_trace, observation=observation,
                                                            feedback=last_action_description, mode=mode,
                                                            observation_VforD=observation_VforD, global_reward=False)
                        if dict_to_write is not None:
                            break
                    elif CR == False:
                        dict_to_write = await Planning.plan(uuid=1, user_request=task_name,
                                                            previous_trace=previous_trace, observation=observation,
                                                            feedback="", mode=mode, observation_VforD=observation_VforD)
                        if dict_to_write is not None:
                            break
                    elif PT == False:
                        dict_to_write = await Planning.plan(uuid=1, user_request=task_name, observation=observation,
                                                            feedback=last_action_description, mode=mode,
                                                            observation_VforD=observation_VforD)
                        if dict_to_write is not None:
                            break
                except Exception as e:
                    traceback.print_exc()
                    continue

            print("dict_to_write:", dict_to_write)
            dict_result_list.append(str(dict_to_write))
            if mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"]:
                execute_action, current_trace, path, element_value = await parse_current_trace(
                    dict_to_write, env)
                selector, xpath = (
                    path[0], path[1]) if path is not None else (None, None)
                print("current trace:\n", current_trace)
                current_trace_list.append(str(current_trace))
                print("response:\n", execute_action)
                action_list.append(str(execute_action))
                print("selector:", selector)
                selector_list.append(selector)
                evaluate_steps, match_result = await step_evaluate(page=env.page, evaluate_steps=evaluate_steps, input_path=selector)
                print("执行动作前的url", env.page.url)
                for evaluate in evaluate_steps:
                    total_step_score += evaluate["score"]
                print(total_step_score, "/", len(reference_evaluate_steps))
                score_str = str(total_step_score) + " / " + \
                    str(len(reference_evaluate_steps))
                match_func_result_list.append(str(match_result))
                score_list.append(score_str)
                if total_step_score == len(reference_evaluate_steps):
                    task_finished = True
                    break
                # input()
                if mode in ["d_v", "dom_v_desc", "vision_to_dom"]:
                    await env.execute_action(execute_action)
                    observation, observation_VforD = await env.get_obs()
                    save_screenshot(mode=mode, record_time=record_time, task_name=task_name, step_number=num_steps, description="obs", screenshot_base64=observation_VforD)
                else:
                    await env.execute_action(execute_action)
                    observation = await env.get_obs()

                print("执行动作后的url", env.page.url)
                url_list.append(env.page.url)

                # current_trace = [current_trace]
                current_reward = await Planning.evaluate(user_request=task_name, previous_trace=previous_trace,
                                                         current_trace=current_trace, observation=observation)
                step_reward_str = current_reward if current_reward else "X"
                step_reward_list.append(str(step_reward_str))
                if current_reward and int(current_reward.get("score")) < config['basic']['Step_Score_Threshold']:
                    execute_action.update(
                        {"element_id": 0, "action_type": ActionTypes.GO_BACK})
                    if mode in ["d_v", "dom_v_desc", "vision_to_dom"]:
                        await env.execute_action(execute_action)
                        observation, observation_VforD = await env.get_obs()
                        save_screenshot(mode=mode, record_time=record_time, task_name=task_name, step_number=num_steps, description="new-obs",
                                        screenshot_base64=observation_VforD)
                    else:
                        await env.execute_action(execute_action)
                        observation = await env.get_obs()
                    last_action_description = current_reward.get("description")
                else:
                    last_action_description = ""
                    previous_trace.append(current_trace)
                if current_reward and int(current_reward.get("score")) < 4:
                    step_error_count += 1
                else:
                    step_error_count = 0

            elif mode == "vision":
                execute_action = dict_to_write["action"]
                thought = dict_to_write["description"].get("thought")
                action = dict_to_write["description"].get("action")
                current_trace = {"thought": thought, "action": action}
                print("执行动作前的url", env.page.url)
                if await env.vision_execute_action(execute_action):
                    break
                print("vision_execute_action finished!")
                observation = await env.get_obs()
                print("执行动作后的url", env.page.url)

                previous_trace.append(current_trace)
                if dict_to_write["description"].get('reward'):
                    if "loop" in dict_to_write["description"].get('reward').get("status"):
                        previous_trace = []
                        previous_trace.append(current_trace)
            previoust_trace_list.append(previous_trace)
            a = input("回车继续下一个Action，按q退出")
            if a == "q" or step_error_count > 3:
                break
            # if step_error_count > 3:
            #     task_error = True
            #     break
        # a = await Planning.plan(uuid=1, user_request="Find Dota 2 game and add all DLC to cart in steam.")
        # print(json5.dumps(a, indent=4))
        # input()

        # ! 3.任务评测打分
        if mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"]:
            # step score
            total_step_score = 0
            for evaluate in evaluate_steps:
                total_step_score += evaluate["score"]
            print("\ntotal step score:", total_step_score,
                  "/", len(reference_evaluate_steps))

            # write_result_to_excel(
            #     task_name=task_name,
            #     task_id=task_index,
            #     task_finished=task_finished,
            #     error_occ=task_error,
            #     step_index_list=step_index_list,
            #     score_list=score_list,
            #     step_reward_list=step_reward_list,
            #     dict_result_list=dict_result_list,
            #     url_list=url_list,
            #     current_trace_list=current_trace_list,
            #     previous_trace_list=previoust_trace_list,
            #     selector_list=selector_list,
            #     action_list=action_list,
            #     match_func_result_list=match_func_result_list
            # )

            # length score
            task_evaluator = TaskLengthEvaluator()
            task_length_score = task_evaluator.task_length_score(
                reference_task_length, num_steps)
            print("task_length_score:", task_length_score)

            # finish score
            finish_task_score = FinishTaskEvaluator.finish_task_score(
                len(reference_evaluate_steps), total_step_score)
            print("finish_task_score:", finish_task_score)

        a = input("回车继续，按q退出")
        await env.close()
        del env
        if a == "q":
            break

    print(f"\033[31mtask finished!\033[0m")  # 红色
    input(f"\033[31m按回车键结束\033[0m")


if __name__ == "__main__":
    asyncio.run(main(mode=interaction_mode))
