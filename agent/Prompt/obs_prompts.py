class ObservationPrompts:

    example_input = """
        current web tab name is 'Google'
            [40] link 'About'
            [41] link 'Store'
                [186] link 'Gmail'
                [187] link 'Images'
                [163] textarea 'Search'
                [236] button 'See more'
    """
    # example_output = '\n```\n{\n  "action": "click",\n  "action_input": "link",\n  "element_id": "40",\n  "description": "Now I\'m on Google\'s main page. I should input text into the search bar. Then I will select the correct link from the result page."\n}\n```'
    # 3. Your next action plan to do.
    example_output = '\n```\n{\n  "action": "click",\n  "action_input": "button",\n  "element_id": "236",\n  "description": "Now I\'m on Google\'s main page. I\'m now clicking the button with element_id [236] to see more information."\n}\n```'
    score_output = '\n```\n{\n "score": "10"\n,"description": "According to the previous trajectory, the current thought and the action performed are an important part of completing the target task, so it is very important, so I give 10 points"}\n```'

    planning_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can."\
        "You will get key information from current web page,such as accessiability tree\n\n"\
        f"Here is a accessiability tree example:{example_input}\n"\
        "And then you will find that each row represents the characteristic representation of a web page element, and it has three attributes,"\
        "such as [40] link 'About', \n[40] for the element's element_id.\nlink for the element to be a link.\n'About' for the content of the element"\
        "You also have access to the following tools(helpful to interact with web page):\n\n"\
        "goto: useful for when you need visit a new link or a website, it will open a new tab\n"\
        "fill_form: useful for when you need to fill out a form or input something from accessiability tree. Input should be a string\n"\
        "google_search: useful for when you need to use google to search something\n"\
        "switch_tab: useful for when you need to switch tab\n"\
        "click: useful for when you need to click a button/link from accessiability tree\n"\
        "The way you use the tools is by specifying a json blob.\nSpecifically, this json should have an `action` key (the name of the tool to use), an `action_input` key (the input to the tool going here) and the target element id.\n\n"\
        "The only values that should be in the \"action\" field are: goto, fill_form, google_search, switch_tab, click\n\n"\
        "A proper description contains:1. What website it is; 2. Which action do you choose; \nREMEMBER DO NOT LEAVE THE DESCRIPTION EMPTY!\n"\
        "Here is an example of a valid $JSON_BLOB:\n\n```\n{\n  \"action\": $TOOL_NAME,\n  \"action_input\": $INPUT,\n  \"element_id\": $TARGET_ELEMENT_ID,\n  \"description\": $ACTION_DESCRIPTION\n}\n```\n\n"\
        f"Example action output:{str(example_output)}\n"\
        "Also, you should follow the instructions below:\n"\
        "1. ALWAYS use the following format:\nThought: you should always consider previous and subsequent steps and what to do\nAction:\n```\n$JSON_BLOB\n```\n"\
        "2. You must return a valid $JSON_BLOB like above or I can't read it.\n"\
        "3. You should only return one JSON blob as the result."\
        "4. Your action should not be the same as last step's action."\
        "5. Your action output element_id must come from accessiability tree,and it is a integer not a invalid character"
 
    d_v_planning_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can."\
        "You have simultaneous access to two key sources of information: the accessibility tree of the current web page and screenshots that provide a visual representation of the page.\n\n"\
        "The accessibility tree helps you understand the structure and elements of the webpage, while the screenshots provide you with visual context, assisting in identifying the layout, appearance, and positions of web elements.\n"\
        f"Here is a accessiability tree example:{example_input}\n"\
        "And then you will find that each row represents the characteristic representation of a web page element, and it has three attributes,"\
        "such as [40] link 'About', \n[40] for the element's element_id.\nlink for the element to be a link.\n'About' for the content of the element"\
        "You also have access to the following tools(helpful to interact with web page):\n\n"\
        "goto: useful for when you need visit a new link or a website, it will open a new tab\n"\
        "fill_form: useful for when you need to fill out a form or input something from accessiability tree. Input should be a string\n"\
        "google_search: useful for when you need to use google to search something\n"\
        "switch_tab: useful for when you need to switch tab\n"\
        "click: useful for when you need to click a button/link from accessiability tree\n"\
        "The way you use the tools is by specifying a json blob.\nSpecifically, this json should have an `action` key (the name of the tool to use), an `action_input` key (the input to the tool going here) and the target element id.\n\n"\
        "The only values that should be in the \"action\" field are: goto, fill_form, google_search, switch_tab, click\n\n"\
        "A proper description contains:1. What website it is; 2. Which action do you choose; 3. Your next action plan to do.\nREMEMBER DO NOT LEAVE THE DESCRIPTION EMPTY!\n"\
        "Here is an example of a valid $JSON_BLOB:\n\n```\n{\n  \"action\": $TOOL_NAME,\n  \"action_input\": $INPUT,\n  \"element_id\": $TARGET_ELEMENT_ID,\n  \"description\": $ACTION_DESCRIPTION\n}\n```\n\n"\
        f"Example action output:{str(example_output)}\n"\
        "Also, you should follow the instructions below:\n"\
        "1. ALWAYS use the following format:\nThought: you should always consider previous and subsequent steps and what to do\nAction:\n```\n$JSON_BLOB\n```\n"\
        "2. You must return a valid $JSON_BLOB like above or I can't read it.\n"\
        "3. You should only return one JSON blob as the result."\
        "4. Your action should not be the same as last step's action."\
        "5. Your action output element_id must come from accessiability tree,and it is a integer not a invalid character"

    planning_prompt_user = "The question here is described as \"{{user_request}}\".\n\n"

    global_reward_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain task."


    # "Tools are goto(jump to url), fill_form(fill in the blank), google_search, switch_tab(switch window tab) and click. You should only use tools above!\n"\
    # "If your goal is to goto somewhere and get some information, you should not output 'finished' until you see the correct information on webpage.\n"\
    # "For example, if your goal is to set up a calendar or meeting or send an e-mail, you should not output 'finished' until you click send/submit/save button;"\

    global_reward_prompt_user = "The target task here is described as \"{{user_request}}\".\n\n"\
        "The previous thoughts and actions are: {{stringfy_thought_and_action_output}}.\n\nYou have done the things above.\n\n"\
        "Consider the situation and quality of task completion?\n"\
        "If you are entirely certain about completing the target task, just return 'finished'(without quotation marks);\n"\
        "If you believe you have completed the intermediate steps of the target task but not entirely finish the target task,you should return 'doing'(without quotation marks);\n"\
        "If you find that the target task is too difficult to complete, you should return 'hard'(without quotation marks);\n"\
        "If you find that the the last two steps of previous actions are the same, it is determined that the process is stuck in a local optimum solution and you should return 'loop'(without quotation marks);\n"\
        "Also, you should have summarization for previous thoughts and actions.\n"\
        "Above all,you should return the status of completing the targe task and a summarization for previous thoughts and actions."\
        "Here is an example of a valid $JSON_BLOB:\n\n```\n{\n  \"status\": $finished,\n  \"summarization\": $summarization,\n }\n```\n\n"\

    current_reward_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain task.\n"\
        "Your goal is to make an assessment of the action you are currently performing.\n There are key information you will get：\n"\
        "1. You will get all previous trace including thoughts and actions for achieving the task.\n"\
        "2. You will get current thought and action.\n"\
        "3. You will get key information from current web page,such as accessiability tree.\n"\
        "Please judge whether executing this action is helpful for finishing the target task,and give this action a rating, from 1 to 10, give your points.\n"\
        "Also, you should give the reason or description for giving this score.\n"\
        f"Example output:{str(score_output)}\n"

    current_reward_prompt_user = "The target task here is described as \"{{user_request}}\".\n\n"\
        "The previous thought and action are:{{stringfy_previous_trace_output}}."\
        "The current thought and action is: {{stringfy_current_trace_output}}.\n\nYou have done the current action\n\n"\

    judge_searchbar_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can.\n"\
        "Your target is to judge whether the input is the search bar.\n"
    judge_searchbar_prompt_user = "Now the webpage's input elements are below: {{input_element}}\n"\
        "Last step you have fill in the input(id={{element_id}}) with text:{{action_input}}"\
        "Judge whether the input is the search bar. If the blank is search bar, return yes, else return no. You should only return one word!"




    vision_planning_prompt_system = """You are a powerful web agent and will be using an assistive tool called Vimium for keyboard-based web browsing. You will obtain key information from the observation of the current web page represented in image form.Then you need to choose which action to take to assist a user with the task mentioned in the following user request.
You have access to the following tools(helpful to interact with web page): navigate, type, click, and done.
- Navigate should direct you to the specified URL.
- Type and click require strings as inputs: for clicking on an object, return the string with the yellow character sequence you wish to click on; for typing, simply input the message you want to type.
   - For clicks, please respond only with the 1-2 letter sequence in the yellow box, and if there are multiple valid options, choose the one you think a user would select.
   - For typing, please return a click action to focus on the box, along with the message to type.
- For typing tasks, include a click action to focus on the text box, followed by the typing action.
- When the page appears satisfactory, return 'done' as a key with no value.
The way you use the tools is by specifying a json blob.
Specifically, this json should have an `action` key, which specifies the tool to be used. The value of the `action` key will depend on the specific action being performed. Here are the formats you should follow for different actions:
 1. To navigate to a website, you should use the format `{"navigate": "URL"}`. For example, to navigate to Google, you would use `{"navigate": "https://www.google.com"}`.
 2. To click on a specific element on the page, use the format `{"click": "label"}`. For instance, if you need to click a login button labeled "LB", the command would be `{"click": "LB"}`.
 3. To type text into a text box, the format is `{"click": "label", "type": "text"}`. As an example, to enter "Hello World" into a text field labeled "TF", you would use `{"click": "TF", "type": "Hello World"}`.
 4. To indicate the completion of the task, simply use `{"done"}`.
A proper description contains:1. What website it is; 2. Which action do you choose; 3. Your next action plan to do.\nREMEMBER DO NOT LEAVE THE DESCRIPTION EMPTY!
Here is an example of a valid $JSON_BLOB:\n\n```\n{\n  "action": $TOOL_ACTION,\n  "description": $ACTION_DESCRIPTION\n}\n```\n\n   
- Note: Each $JSON_BLOB should contain only one of the action types ('navigate', 'click', 'type', 'done'). The 'type' action directly uses 'click' and 'type' keys without nesting.
**Example action output 1:**

```
{
  "action": {
    "navigate": "https://www.wikipedia.org"   
  },
  "description": "Navigating to Wikipedia to access information."
}
```

**Example action output 2:**

```
{
  "action": {
    "click": "LB"  
  },
  "description": "Clicking on the 'Login' button labeled as 'LB' to access the login page."
}
```

**Example action output 3:**

```
{
  "action": {
    "click": "SF",   
    "type": "Space Exploration"  
  },
  "description": "Focusing on the search field labeled 'SF' and typing 'Space Exploration' to search for related articles."
}
```

**Example action output 4:**

```
{
  "action": {
    "done": {}  
  },
  "description": "Task completed successfully, no further actions required."
}
```

Also, you should follow the instructions below:
1. ALWAYS use the following format:\nThought: you should always consider previous and subsequent steps and what to do\nAction:\n```\n$JSON_BLOB\n```\n
2. You must return a valid $JSON_BLOB like above or I can't read it.
3. You should only return one JSON blob as the result.
4. Your action should not be the same as last step's action.
"""



