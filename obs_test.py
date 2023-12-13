from agent.Environment.html_env.actions import Action, create_action
from agent.Environment.html_env.async_env import AsyncHTMLEnvironment
from agent.Environment.html_env.base_env import HTMLEnvironment
from agent.Plan import *
import traceback


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
        if response['id'] == '' or response['id'] is None or response['id'].isdigit() is False:
            element_id = 0
        else:
            element_id = int(response['id'])
        execute_action = create_action(
            elementid=element_id, action_type=action_type, action_input=acton_input)
        return execute_action, previous_trace
    previous_trace = []
    index = 1
    while True:
        for _ in range(3):
            try:
                dict_to_write = await Planning.plan(uuid="uuid", user_request="Go to the official website of taobao to buy a back hat", tab_name_list=None, current_tab_name=None, current_time=None, previous_trace=previous_trace, dom=None, observation=observation)
                if dict_to_write is not None:
                    break
            except Exception as e:
                traceback.print_exc()
                continue 
        print("dict_to_write:\n", dict_to_write)
        execute_action, current_trace = parse_previous_trace(dict_to_write)
        print("execute action:\n",execute_action)
        observation = await env.execute_action(execute_action)
        print(f"new observation {index}:\n", observation)
        previous_trace.append(current_trace)
        print("previous trace:\n",previous_trace)
        if dict_to_write["description"]["thought"].lower() == "finished":
            break
        index += 1

if __name__ == "__main__":
    asyncio.run(main())
