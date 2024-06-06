class VisionToDomPrompts:
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

    vision_act_planning_prompt_system = ''''''

    vision_act_planning_prompt_user = "The question here is described as \"{{user_request}}\".\n\n"

    vision_to_dom_planning_prompt_system = ''''''

