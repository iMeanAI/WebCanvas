class BasePrompts:

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

    planning_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can."\
        "You will get key information from current web page,such as accessibility tree\n\n"\
        f"Here is a accessibility tree example:{example_input}\n"\
        "And then you will find that each row represents the characteristic representation of a web page element, and it has three attributes,"\
        "such as [40] link 'About', \n[40] for the element's element_id.\nlink for the element to be a link.\n'About' for the content of the element"\
        "You also have access to the following tools(helpful to interact with web page):\n\n"\
        "goto: useful for when you need visit a new link or a website, it will open a new tab\n"\
        "fill_form: useful for when you need to fill out a form or input something from accessibility tree. Input should be a string\n"\
        "google_search: useful for when you need to use google to search something\n"\
        "switch_tab: useful for when you need to switch tab\n"\
        "click: useful for when you need to click a button/link from accessibility tree\n"\
        "The way you use the tools is by specifying a json blob.\nSpecifically, this json should have an `action` key (the name of the tool to use), an `action_input` key (the input to the tool going here) and the target element id.\n\n"\
        "The only values that should be in the \"action\" field are: goto, fill_form, google_search, switch_tab, click\n\n"\
        "A proper description contains:1. What website it is; 2. Which action do you choose; \nREMEMBER DO NOT LEAVE THE DESCRIPTION EMPTY!\n"\
        "Here is an example of a valid $JSON_BLOB:\n\n```\n{\n  \"action\": $TOOL_NAME,\n  \"action_input\": $INPUT,\n  \"element_id\": $TARGET_ELEMENT_ID,\n  \"description\": $ACTION_DESCRIPTION\n}\n```\n\n"\
        f"Example action output:{str(example_output)}\n"\
        "Also, you should follow the instructions below:\n"\
        "1. ALWAYS use the following format:\nThought: you should always consider previous and subsequent steps and what to do\nAction:\n```\n$JSON_BLOB\n```\n"\
        "2. You must return a valid $JSON_BLOB like above or I can't read it.\n"\
        "3. You should only return one JSON blob as the result.\n"\
        "4. Your action should not be the same as last step's action.\n"\
        "5. Your action output element_id never from the above accessibility tree example\n"\
        "6. Your action output element_id must come from accessibility tree,and it is a integer not a invalid character\n"\
        # "6. If you don't get the accessibility tree of web page, please keep action output element_id is None.\n"\

    planning_prompt_user = "The question here is described as \"{{user_request}}\".\n\n"

    global_reward_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain task."\
        "Your objective is to assess the completion status of the target task by analyzing the preceding trajectory and assigning an appropriate score ranging from 0% to 100%"\
        "This entails acquiring crucial details, including the score from the most recent task accomplishment and the distinctive features of the new web page, represented through an accessibility tree or screenshot."\
        "If you are entirely certain about completing the target task, just return 'finished'(without quotation marks);\n"\
        "If you believe you have completed the intermediate steps of the target task but not entirely finish the target task,you should return 'doing'(without quotation marks);\n"\
        "If you find that the target task is too difficult to complete, you should return 'hard'(without quotation marks);\n"\
        "If you find that the the last two steps of previous actions are the same, it is determined that the process is stuck in a local optimum solution and you should return 'loop'(without quotation marks);\n"\
        "Also, you should have description for completing the target task base on the score\n"\
        "Above all,you should return the status of completing the targe task and description of task completion"\
        "Here is an example of a valid $JSON_BLOB:\n\n```\n{\n  \"status\": $finished,\n  \"description\": $description,\n }\n```\n\n"\

    # "Tools are goto(jump to url), fill_form(fill in the blank), google_search, switch_tab(switch window tab) and click. You should only use tools above!\n"\
    # "If your goal is to goto somewhere and get some information, you should not output 'finished' until you see the correct information on webpage.\n"\
    # "For example, if your goal is to set up a calendar or meeting or send an e-mail, you should not output 'finished' until you click send/submit/save button;"\

    global_reward_prompt_user = "The target task here is described as \"{{user_request}}\".\n\n"\
        "The previous thoughts and actions are: {{stringfy_thought_and_action_output}}.\n\nYou have done the things above.\n\n"\


    current_reward_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain task.\n"\
        "Your goal is to make an assessment of the action you are currently performing.\n There are key information you will get：\n"\
        "1. You will get all previous trace including thoughts and actions for achieving the task.\n"\
        "2. You will get current thought and action.\n"\
        "3. You will get key information from current web page,such as accessibility tree.\n"\
        "Please judge whether executing this action is helpful for finishing the target task,and give this action a rating, from 1 to 10, give your points.\n"\
        "Also, you should give the reason or description for giving this score.\n"\
        f"Example output:{str(score_output)}\n"

    current_reward_prompt_user = "The target task here is described as \"{{user_request}}\".\n\n"\
        "The previous thought and action are:{{stringfy_previous_trace_output}}."\
        "The current thought and action is: {{stringfy_current_trace_output}}.\n\nYou have done the current action\n\n"\

    judge_searchbar_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can.\n"\
        "Your target is to judge whether the input is the search bar.\n"
    judge_searchbar_prompt_user = "Now the webpage's accessibility tree(the key information of current web page)is below: {{input_element}}\n"\
        "Last step you have fill in the input(id={{element_id}}) with text:{{action_input}}"\
        "Judge whether the input is the search bar. If the blank is search bar, return yes, else return no. You should only return one word!"
    semantic_match_prompt_system = "Now you are an assistant to judge whether 2 elements are semantically same.\n"\
        "If they are the same, you should return 1. If they are not related, you should return 0. "\
        "If they are related but not identical, return a decimal (two decimal places) between 0 and 1 of the degree of relevance you think."\
        "Remember, you should only return a number without any punctuation or explanation!"  # TODO
    semantic_match_prompt_user = "you should judge by the function below:{{semantic_method}}.\n\nmy answer is:{{input_answer}}\nreference answer is:{{reference_answer}}"
