from agent.Environment.html_env.build_tree import HTMLTree, HTMLEnvironment
from agent.Environment.webarena_env.build_env import BrowserEnvironment
from agent.Environment.html_env.active_elements import ActiveElements
from agent.Environment.html_env.actions import create_action


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
    observation = env.reset(
        "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:7770")
    print("current observation:\n", observation)
    action = create_action(
        elementid=459, action_type="fill_form", action_input="xbox")
    next_observation = env.execute_action(action)
    print("the next observation:\n", next_observation)
    selector, xpath = env.tree.get_selector_and_xpath(1587)
    print("selector:", selector)

    # REDDIT
    # observation = env.reset(
    #     "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:9999")
    # print(observation)

    # GITLAB
    # observation = env.reset(
    #     "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:8023")
    # print(observation)

    # MAP
    # observation = env.reset(
    #     "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:3000")
    # print(observation)

