class BasePrompts:
    example_output = '\n```\n{\n  "action": "click",\n  "action_input": "link",\n  "element_id": "14",\n  "description": "Now I\'m on Google\'s main page. I should input text into the search bar. Then I will select the correct link from the result page."\n}\n```'

    planning_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can. You have access to the following tools:\n\n"\
        "goto: useful for when you need visit a link or a website, it will open a new tab\n"\
        "fill_form: useful for when you need to fill out a form on the current website. Input should be a string\n"\
        "google_search: useful for when you need to use google to search something\n"\
        "switch_tab: useful for when you need to switch tab\n"\
        "click: useful for when you need to click a button/link\n"\
        "The way you use the tools is by specifying a json blob.\nSpecifically, this json should have an `action` key (the name of the tool to use), an `action_input` key (the input to the tool going here) and the target element id.\n\n"\
        "The only values that should be in the \"action\" field are: goto, fill_form, google_search, switch_tab, click\n\n"\
        "A proper description contains:1. What website it is; 2. Which action do you choose; 3. Your next action plan to do.\nREMEMBER DO NOT LEAVE THE DESCRIPTION EMPTY!\n"\
        "Here is an example of a valid $JSON_BLOB:\n\n```\n{\n  \"action\": $TOOL_NAME,\n  \"action_input\": $INPUT,\n  \"element_id\": $TARGET_ELEMENT_ID,\n  \"description\": $ACTION_DESCRIPTION\n}\n```\n\n"\
        f"Example action output:{str(example_output)}\n"\
        "Also, you should follow the instructions below:\n"\
        "1. ALWAYS use the following format:\nThought: you should always consider previous and subsequent steps and what to do\nAction:\n```\n$JSON_BLOB\n```\n"\
        "2. You must return a valid $JSON_BLOB like above or I can't read it.\n"\
        "3. You should only return one JSON blob as the result."\
        "4. Your action should not be the same as last step's action."

    planning_prompt_user = "The question here is described as \"{{user_request}}\".\n\n"

    reward_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals."

    reward_prompt_user = "The question here is described as \"{{user_request}}\".\n\n"\
        "The previous thoughts and actions are: {{stringfy_thought_and_action_output}}.\n\nYou have done the things above.\n\n"\
        "Tools are goto(jump to url), fill_form(fill in the blank), google_search, switch_tab(switch window tab) and click. You should only use tools above!\n"\
        "Consider whether previous actions have done the task(ignore the detail actions)?\nIf true, just return 'finished'(without quotation marks);\nElse, return what's next step you plan to do.\n"\
        "For example, if your goal is to set up a calendar or meeting or send an e-mail, you should not output 'finished' until you click send/submit/save button;"\
        "If your goal is to goto somewhere and get some information, you should not output 'finished' until you see the correct information on webpage.\n"\
        "If you find that the actions of the last two steps are the same, it is determined that the process is stuck in a local optimum solution and you should output 'loop'(without quotation marks)."\
        "If you find that the task is too difficult to complete, you should output 'hard'."\
        "Take a deep breath, please think carefully!"

    judge_searchbar_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can.\n"\
        "Your target is to judge whether the input is the search bar.\n"
    judge_searchbar_prompt_user = "Now the webpage's input elements are below: {{input_element}}\n"\
        "Last step you have fill in the input(id={{element_id}}) with text:{{action_input}}"\
        "Judge whether the input is the search bar. If the blank is search bar, return yes, else return no. You should only return one word!"

    semantic_match_prompt_system = "Now you are an assistant to judge whether 2 elements are semantically same.\n"\
    "If they are the same, you should return 1. If they are not related, you should return 0. "
    "If they are related but not identical, return a decimal (two decimal places) between 0 and 1 of the degree of relevance you think."\
    "Remember, you should only return a number without any punctuation or explanation!"  # TODO
    semantic_match_prompt_user = "you should judge by the function below:{{semantic_method}}.\n\nmy answer is:{{input_answer}}\nreference answer is:{{reference_answer}}"
