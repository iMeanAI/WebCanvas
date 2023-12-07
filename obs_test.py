from agent.Environment.html_env.build_tree import HTMLTree, HTMLEnvironment
from agent.Environment.webarena_env.build_env import BrowserEnvironment
from agent.Environment.html_env.active_elements import ActiveElements
from playwright.sync_api import sync_playwright
import requests


if __name__ == "__main__":

    env = HTMLEnvironment(
        max_page_length=8192,
        headless=True,
        slow_mo=1000,
        current_viewport_only=False,
        viewport_size={"width": 1280, "height": 720},
        save_trace_enabled=False,
        sleep_after_execution=0.0,
    )

    # SHOPPING
    # obs = env.reset(
    #     "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:7770")
    # print(obs)
    # print(env.execute_action(331))

    # REDDIT
    # obs = env.reset(
    #     "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:9999")
    # print(obs)

    # GITLAB
    # obs = env.reset(
    #     "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:8023")
    # print(obs)
    # print(env.execute_action(94))

    #MAP
    obs = env.reset(
        "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:3000")
    print(env.page.url)
    print(env.execute_action(393))
    



    