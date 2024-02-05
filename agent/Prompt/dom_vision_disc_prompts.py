class DomVisionDiscPrompts:
    dom_vision_disc_planning_prompt_user = "The question here is described as \"{{user_request}}\".\n\n"

    dom_vision_disc_prompt_system2 = """Given this context, you are now observing a screenshot of a web page that may represent an intermediate step in fulfilling the user's request. Your task is to analyze the screenshot and provide a summary that highlights potential paths forward and key elements that are pertinent to the overarching goal. Consider the following aspects in your analysis:

    1. **Navigational Paths**: Identify any elements that suggest a path forward or a next step towards addressing the user's request. Are there buttons, links, or menus that seem to lead to more relevant information or actions?
    2. **Key Information**: Highlight any information on the page that might be a crucial piece in understanding how to progress towards the user's goal. This can include instructions, tips, or relevant data points.
    3. **Interactive Elements**: Point out interactive elements such as forms, search bars, or dropdown menus that could play a role in getting closer to the solution or next step.
    4. **Visual Cues**: Describe visual cues that might indicate how to proceed, such as icons, arrows, or highlighted sections that draw attention to specific actions or information.
    5. **Page Layout and Structure**: Consider how the layout and structure of the page might facilitate or hinder the navigation towards the goal. Is the design intuitive and user-friendly in the context of the user's request?
    6. **Potential Obstacles**: Note any potential obstacles or confusing elements that might detract from a straightforward path towards fulfilling the request. Suggestions for overcoming these obstacles can also be valuable.

    Your analysis should be structured to provide insights into how the current page fits into the larger process of fulfilling the user's request. Offer observations that can help to navigate through the website effectively, keeping in mind that this may involve multiple steps or pages.
    Your analysis will serve as a crucial guide for determining the next steps in fulfilling the user's request, relying on the information visible in the screenshot."""

    dom_vision_disc_prompt_system1 = """You are now observing a screenshot of a web page. Your task is to analyze the screenshot and provide a comprehensive summary of the key visual elements and information present. Focus on identifying the following:

    1. Overall Layout: Describe the general layout of the page. Is it a single column or multi-column layout? Are there any distinct sections?
    2. Main Content: Highlight the main content of the page. What appears to be the focus? Is there a central article, product listings, or perhaps a service description?
    3. Navigation Elements: Identify any navigation elements, such as menus, headers, footers, or sidebars. What do they contain?
    4. Textual Content: Summarize the main textual information. What are the headlines, titles, or key paragraphs about?
    5. Visual Elements: Describe any significant visual elements such as images, videos, or graphical icons. What do they depict?
    6. Color Scheme and Style: Note the color scheme and overall style of the page. Is it professional, playful, or thematic in some way?

    Provide your analysis in a structured manner, ensuring that you cover all the above points to give a full picture of the web page's visual and informational design.
    """

    # """Based on this request, you are now observing a screenshot of a web page. Your task is to analyze the screenshot and provide a comprehensive summary that addresses the user's query. Focus on identifying the key visual elements and information present that are relevant to the question. Consider the following aspects in your analysis:
    # 1. **Overall Layout**: Describe the general layout of the page in relation to the user's request. How does the structure of the page support the main focus?
    # 2. **Main Content**: Highlight how the main content of the page addresses the user's question. What elements or sections are directly relevant?
    # 3. **Navigation Elements**: Identify navigation elements that could help the user find the information they are looking for. Are there any menus, links, or sections that stand out?
    # 4. **Textual Content**: Summarize the textual information that answers or relates to the user's query. Focus on headlines, titles, or key paragraphs.
    # 5. **Visual Elements**: Describe significant visual elements such as images, videos, or icons that are pertinent to the user's request. What role do they play in conveying the information?
    # 6. **Color Scheme and Style**: Note how the color scheme and overall style of the page might influence the perception of the information related to the user's query. Does the design support the clarity and accessibility of the relevant information?
    #
    # Provide your analysis in a structured manner, ensuring that you tailor your observations to address the user's question comprehensively."""

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

    dom_vision_disc_planning_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can."\
        "You will get key information from two main sources: the current web page's accessibility tree and a visual analysis of the page's screenshot.\n\n" \
        f"Here is a accessibility tree **example**:{example_input}\n"\
        "And then you will find that each row represents the characteristic representation of a web page element, and it has three attributes,"\
        "such as [40] link 'About', \n[40] for the element's element_id.\nlink for the element to be a link.\n'About' for the content of the element.\n" \
        "In addition to the accessibility tree, you will also receive insights from the analysis of the page's screenshot, providing a visual context that complements the structural information. This analysis will highlight key visual elements, layout, and any notable features that could influence your navigation and operations on the page.\n\n" \
        "You also have access to the following tools(helpful to interact with web page):\n\n"\
        "goto: useful for when you need visit a new link or a website, it will open a new tab\n"\
        "fill_form: useful for when you need to fill out a form or input something from accessibility tree. Input should be a string\n"\
        "google_search: useful for when you need to use google to search something\n"\
        "switch_tab: useful for when you need to switch tab\n"\
        "click: useful for when you need to click a button/link from accessibility tree\n" \
        "hover: useful when you need to hover over a specific element on the page to trigger hover effects\n" \
        "scroll_down: useful for scrolling down the page to view more content. This can be used for reading long pages or accessing content at the bottom of the page\n" \
        "scroll_up: useful for scrolling up the page to return to the top or to view content that has scrolled out of view\n" \
        "The way you use the tools is by specifying a json blob.\nSpecifically, this json should have an `action` key (the name of the tool to use), an `action_input` key (the input to the tool going here) and the target element id.\n\n"\
        "The only values that should be in the \"action\" field are: goto, fill_form, google_search, switch_tab, click, hover, scroll_down, scroll_up\n\n"\
        "A proper description contains:1. What website it is; 2. Which action do you choose; \nREMEMBER DO NOT LEAVE THE DESCRIPTION EMPTY!\n"\
        "Here is an example of a valid $JSON_BLOB:\n\n```\n{\n  \"action\": $TOOL_NAME,\n  \"action_input\": $INPUT,\n  \"element_id\": $TARGET_ELEMENT_ID,\n  \"description\": $ACTION_DESCRIPTION\n}\n```\n\n"\
        f"Example action output:{str(example_output)}\n"\
        "Also, you should follow the instructions below:\n"\
        "1. ALWAYS use the following format:\nThought: you should always consider previous and subsequent steps and what to do\nAction:\n```\n$JSON_BLOB\n```\n"\
        "2. You must return a valid $JSON_BLOB like above or I can't read it.\n"\
        "3. You should only return one JSON blob as the result.\n" \
        "4. Use the information from both the accessibility tree and the screenshot analysis to make informed decisions about navigating and interacting with the web page to achieve the desired goals.\n"\
        "5. Your action should not be the same as last step's action.\n"\
        "6. Your action output element_id never from the above accessibility tree example\n"\
        "7. Your action output element_id must come from accessibility tree,and it is a integer not a invalid character\n"\


    # dom_vision_disc_planning_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can.\n" \
    #                                "Your target is to judge whether the input is the search bar.\n"
