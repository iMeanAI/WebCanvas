class DomVisionDiscPrompts:
    dom_vision_disc_planning_prompt_user = "The question here is described as \"{{user_request}}\".\n\n"

    dom_vision_disc_prompt_system = """Given this context, you are now observing a screenshot of a web page that may represent an intermediate step in fulfilling the user's request. Your task is to analyze the screenshot and provide a summary that highlights potential paths forward and key elements that are pertinent to the overarching goal. Consider the following aspects in your analysis:

    1. **Navigational Paths**: Identify any elements that suggest a path forward or a next step towards addressing the user's request. Are there buttons, links, or menus that seem to lead to more relevant information or actions?
    2. **Key Information**: Highlight any information on the page that might be a crucial piece in understanding how to progress towards the user's goal. This can include instructions, tips, or relevant data points.
    3. **Interactive Elements**: Point out interactive elements such as forms, search bars, or dropdown menus that could play a role in getting closer to the solution or next step.
    4. **Visual Cues**: Describe visual cues that might indicate how to proceed, such as icons, arrows, or highlighted sections that draw attention to specific actions or information.
    5. **Page Layout and Structure**: Consider how the layout and structure of the page might facilitate or hinder the navigation towards the goal. Is the design intuitive and user-friendly in the context of the user's request?
    6. **Potential Obstacles**: Note any potential obstacles or confusing elements that might detract from a straightforward path towards fulfilling the request. Suggestions for overcoming these obstacles can also be valuable.

    Your analysis should be structured to provide insights into how the current page fits into the larger process of fulfilling the user's request. Offer observations that can help to navigate through the website effectively, keeping in mind that this may involve multiple steps or pages."""


    # """Based on this request, you are now observing a screenshot of a web page. Your task is to analyze the screenshot and provide a comprehensive summary that addresses the user's query. Focus on identifying the key visual elements and information present that are relevant to the question. Consider the following aspects in your analysis:
    # 1. **Overall Layout**: Describe the general layout of the page in relation to the user's request. How does the structure of the page support the main focus?
    # 2. **Main Content**: Highlight how the main content of the page addresses the user's question. What elements or sections are directly relevant?
    # 3. **Navigation Elements**: Identify navigation elements that could help the user find the information they are looking for. Are there any menus, links, or sections that stand out?
    # 4. **Textual Content**: Summarize the textual information that answers or relates to the user's query. Focus on headlines, titles, or key paragraphs.
    # 5. **Visual Elements**: Describe significant visual elements such as images, videos, or icons that are pertinent to the user's request. What role do they play in conveying the information?
    # 6. **Color Scheme and Style**: Note how the color scheme and overall style of the page might influence the perception of the information related to the user's query. Does the design support the clarity and accessibility of the relevant information?
    #
    # Provide your analysis in a structured manner, ensuring that you tailor your observations to address the user's question comprehensively."""

    # """You are now observing a screenshot of a web page. Your task is to analyze the screenshot and provide a comprehensive summary of the key visual elements and information present. Focus on identifying the following:
    #
    # 1. Overall Layout: Describe the general layout of the page. Is it a single column or multi-column layout? Are there any distinct sections?
    # 2. Main Content: Highlight the main content of the page. What appears to be the focus? Is there a central article, product listings, or perhaps a service description?
    # 3. Navigation Elements: Identify any navigation elements, such as menus, headers, footers, or sidebars. What do they contain?
    # 4. Textual Content: Summarize the main textual information. What are the headlines, titles, or key paragraphs about?
    # 5. Visual Elements: Describe any significant visual elements such as images, videos, or graphical icons. What do they depict?
    # 6. Color Scheme and Style: Note the color scheme and overall style of the page. Is it professional, playful, or thematic in some way?
    #
    # Provide your analysis in a structured manner, ensuring that you cover all the above points to give a full picture of the web page's visual and informational design.
    # """


    dom_vision_disc_planning_prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can.\n" \
                                    "Your target is to judge whether the input is the search bar.\n"
