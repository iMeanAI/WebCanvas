import time
import json5
import requests
from evaluate import *
from agent.Environment import HTMLEnvironment
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import re

if __name__ == "__main__":

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

    num_steps = 0

    # 读取标签数据
    def read_file(path="./data/test.json"):
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

    # 评测步骤打分
    def step_evaluate(page: Page, input_path=None, semantic_method=None):
        global reference_evaluate_steps, num_steps
        num_steps += 1
        # page_url = html_env.page.url
        # page_url = page.url
        step_score = 0
        for evaluate in reference_evaluate_steps:
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
                    pass
                if match_function == "text_include_match":
                    pass
                if match_function == "text_semantic_match":
                    pass

                evaluate["score"] = max(evaluate["score"], score)
            step_score += evaluate["score"]
        print("current step score:", step_score)
        return evaluate["score"]
        # print(evaluate_steps)

    reference_task_length, reference_evaluate_steps = read_file()
    print("raw data:\n", reference_evaluate_steps)

    # 用playwright运行浏览器
    def run(playwright: Playwright) -> None:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        replay_codes = open("./data/playwright/steam.txt", "r", encoding="utf-8")
        for i, line in enumerate(replay_codes):
            print("step:", i, line)
            selector = None
            if "page.locator" in line:
                selector = re.findall('page.locator\("(.*?)"\).*?\(\)', line)[0]
                print("selector:", selector)
            exec(line)
            step_evaluate(page, selector)
            time.sleep(3)

    with sync_playwright() as playwright:
        run(playwright)

    # 任务评测打分

    # step score
    total_step_score = 0
    for evaluate in reference_evaluate_steps:
        total_step_score += evaluate["score"]
    print("\ntotal step score:", total_step_score)

    # length score
    task_evaluator = TaskLengthEvaluator()
    task_length_score = task_evaluator.task_length_score(reference_task_length, num_steps)
    print("task_length_score:", task_length_score)

    # finish score
    finish_task_score = FinishTaskEvaluator.finish_task_score(len(reference_evaluate_steps), total_step_score)
    print("finish_task_score:", finish_task_score)
