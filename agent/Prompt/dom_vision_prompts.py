class DomVisionPrompts:

    example_input = """
        current web tab name is 'Google'
            [40] link 'About'
            [41] link 'Store'
                [186] link 'Gmail'
                [187] link 'Images'
                [163] textarea 'Search'
                [236] button 'See more'
    """

    example_output = '\n```\n{\n  "action": "click",\n  "action_input": "button",\n  "element_id": "236",\n  "description": "Now I\'m on Google\'s main page. I\'m now clicking the button with element_id [236] to see more information."\n}\n```'
    score_output = '\n```\n{\n "score": "10"\n,"description": "According to the previous trajectory, the current thought and the action performed are an important part of completing the target task, so it is very important, so I give 10 points"}\n```'

    d_v_planning_prompt_system = ''''''

    d_v_planning_prompt_user = "The question here is described as \"{{user_request}}\".\n\n"

    current_d_vision_reward_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain task.\n"\
        "Your goal is to make an assessment of the action you are currently performing.\n There are key information you will get：\n"\
        "1. You will get all previous trace including thoughts and actions for achieving the task.\n"\
        "2. You will get current thought and action.\n"\
        "3. You will get key information from current web page,such as accessibility tree.\n"\
        "4. You will also obtain a screenshot of the web page\n"\
        "Please judge whether executing this action is helpful for finishing the target task,and give this action a rating, from 1 to 10, give your points.\n"\
        "Also, you should give the reason or description for giving this score.\n"\
        f"Example output:{str(score_output)}\n"

    current_d_vision_reward_prompt_user = "The target task here is described as \"{{user_request}}\".\n\n"\
        "The previous thought and action are:{{stringfy_previous_trace_output}}."\
        "The current thought and action is: {{stringfy_current_trace_output}}.\n\nYou have done the current action\n\n"
