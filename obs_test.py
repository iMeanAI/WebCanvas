import traceback
import json5
from agent.Plan import *
from os import environ
from sanic import Request, Sanic, response
from sanic.log import logger
from agent.Environment.webarena_env.build_env import BrowserEnvironment
from agent.Environment.html_env.active_elements import ActiveElements
from agent.Environment.html_env.actions import create_action, Action
from agent.Environment.html_env.async_env import AsyncHTMLEnvironment
from agent.Environment.html_env.base_env import HTMLEnvironment
from agent.Memory.short_memory.history import HistoryMemory


async def main():
    env = AsyncHTMLEnvironment(
        max_page_length=8192,
        headless=True,
        slow_mo=1000,
        current_viewport_only=False,
        viewport_size={"width": 1920, "height": 1280},
        save_trace_enabled=False,
        sleep_after_execution=0.0,
    )
    observation = await env.reset()
    def parse_previous_trace(response) -> (Action, list):
        # 临时测试，有问题，后面得用history.py的previous trace
        match = re.compile(r"Thought: (.*)\n\nAction:")
        thought = match.search(response["openai_response"])
        if thought:
            thought = thought.group(1)
        else:
            thought = ""
        action_type = response['action_type']
        acton_input = response['value']
        action = f"{action_type}: {acton_input}"
        previous_trace = {"thought": thought, "action": action}
        if response['id'] == '' or response['id'] is None:
            element_id = 0
        else:
            element_id = int(response['id'])
        execute_action = create_action(
            elementid=element_id, action_type=action_type, action_input=acton_input)
        return execute_action, previous_trace
    previous_trace = []
    index = 1
    while index < 10:
        print("planning前：",previous_trace)
        print("planning前：",observation)
        for _ in range(3):
            try:
                dict_to_write = await Planning.plan(uuid="uuid", user_request="Go to the official website of LOL to check the information of the hero Yasuo", tab_name_list=None, current_tab_name=None, current_time=None, previous_trace=previous_trace, dom=None, observation=observation)
                if dict_to_write is not None:
                    break
            except Exception as e:
                traceback.print_exc()
                continue
        execute_action, current_trace = parse_previous_trace(dict_to_write)
        print("current trace:\n",current_trace)
        print("response:\n",dict_to_write)
        observation = await env.execute_action(execute_action)
        print(f"new observation {index}:\n", observation)
        previous_trace.append(current_trace)
        index += 1

if __name__ == "__main__":
    asyncio.run(main())
