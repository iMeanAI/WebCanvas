import time
import json5
import requests
from evaluate import *
from agent.Environment import HTMLEnvironment
from agent.Plan import *
from playwright.async_api import Playwright, async_playwright, expect, Page

import re
import asyncio


async def main(num_steps=0):
    # html_env = HTMLEnvironment(
    #     max_page_length=8192,
    #     headless=True,
    #     slow_mo=1000,
    #     current_viewport_only=False,
    #     viewport_size={"width": 1280, "height": 720},
    #     save_trace_enabled=False,
    #     sleep_after_execution=0.0,
    # )
    # html_env.setup("about:blank")

    
    def read_file(path="./data/test.json"):
        '''读取标签数据'''
        with open(path) as f:
            test_data = json5.load(f)

        evaluation_data = test_data[0]["evaluation"]
        reference_task_length = test_data[0]["reference_task_length"]

        reference_evaluate_steps = []
        for i, evaluation in enumerate(evaluation_data):
            match_function = evaluation["match_function"]
            if "url" in match_function:
                key = evaluation["content"]["key"]
                reference_answer = evaluation["content"]["reference_answer"]
                reference_evaluate_steps.append({"match_function": match_function,
                                                "key": key, "reference_answer": reference_answer, "score": 0})
            elif "path" in match_function:  # TODO
                reference_answer = evaluation["content"]["reference_answer"]
                method = evaluation["method"]
                reference_evaluate_steps.append({"match_function": match_function, "method": method,
                                                "reference_answer": reference_answer, "score": 0})

        return reference_task_length, reference_evaluate_steps

    
    def step_evaluate(page: Page, evaluate_steps=[], input_path=None, semantic_method=None):
        '''评测步骤打分'''
        # reference_evaluate_steps, num_steps
        # num_steps += 1
        # page_url = html_env.page.url
        # page_url = page.url
        step_score = 0
        for evaluate in evaluate_steps:
            if evaluate["score"] != 1:
                match_function = evaluate["match_function"]
                if match_function == "url_exact_match":
                    score = URLEvaluator.url_exact_match(page.url, evaluate["reference_answer"], evaluate["key"])
                if match_function == "url_include_match":
                    score = URLEvaluator.url_include_match(page.url, evaluate["reference_answer"], evaluate["key"])
                if match_function == "url_semantic_match":
                    score = URLEvaluator.url_semantic_match(
                        page.url, evaluate["reference_answer"], evaluate["key"], semantic_method=semantic_method)
                if match_function == "path_exact_match":
                    method = evaluate["method"]
                    score = PathEvaluator.path_exact_match(
                        input_path, evaluate["reference_answer"], method, page.content())
                if match_function == "path_include_match":
                    method = evaluate["method"]
                    score = PathEvaluator.path_included_match(
                        input_path, evaluate["reference_answer"], method, page.content())
                if match_function == "path_semantic_match":
                    method = evaluate["method"]
                    score = PathEvaluator.path_semantic_match(
                        input_path, evaluate["reference_answer"], method, page.content(), semantic_method)
                if match_function == "text_exact_match":
                    pass  # TODO
                if match_function == "text_include_match":
                    pass
                if match_function == "text_semantic_match":
                    pass

                evaluate["score"] = max(evaluate["score"], score)
            step_score += evaluate["score"]
        print("current step score:", step_score)
        return evaluate_steps
        # print(evaluate_steps)

    reference_task_length, reference_evaluate_steps = read_file()
    print("raw data:\n", reference_evaluate_steps)


    # # 1. playwright
    async def aexec_playwright(code, page):
        '''async执行playwright代码'''
        exec(
            f'async def __ex(page): ' +
            ''.join(f'\n {l}' for l in code.split('\n'))
        )
        # Get `__ex` from local variables, call it and return the result
        return await locals()['__ex'](page)

    # # 用playwright运行浏览器
    async def run(playwright: Playwright) -> None:
        '''用playwright运行浏览器'''
        evaluate_steps = reference_evaluate_steps
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        replay_codes = open("./data/playwright/steam.txt", "r", encoding="utf-8")
        for num_steps, line in enumerate(replay_codes):
            print("step:", num_steps, line)
            selector = None
            if "page.locator" in line:
                selector = re.findall('page.locator\("(.*?)"\).*?\(\)', line)[0]
                print("selector:", selector)
            line = "await "+line
            print(line)
            await aexec_playwright(line, page)
            evaluate_steps = step_evaluate(page=page, evaluate_steps=evaluate_steps, input_path=selector)
            time.sleep(3)
        return num_steps, evaluate_steps

    async with async_playwright() as playwright:
        num_steps, evaluate_steps = await run(playwright)
    
    
    # 2. planning
    # a = await Planning.plan(uuid=1, user_request="Find Dota 2 game and add all DLC to cart in steam.")
    # print(json5.dumps(a, indent=4))
    # input()
    
    
    # # 任务评测打分

    # step score
    total_step_score = 0
    for evaluate in evaluate_steps:
        total_step_score += evaluate["score"]
    print("\ntotal step score:", total_step_score)

    # length score
    task_evaluator = TaskLengthEvaluator()
    task_length_score = task_evaluator.task_length_score(reference_task_length, num_steps)
    print("task_length_score:", task_length_score)

    # finish score
    finish_task_score = FinishTaskEvaluator.finish_task_score(len(reference_evaluate_steps), total_step_score)
    print("finish_task_score:", finish_task_score)

if __name__ == "__main__":
    asyncio.run(main())
