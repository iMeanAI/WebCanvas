import json

import tiktoken


def calculation_of_token(messages, model='gpt-3.5-turbo', max_tokens=4096):
    """
    Calculate the number of tokens in the messages.
    :param messages: List of messages to calculate tokens for
    :param model: Model to use for tokenization
    :param max_tokens: Maximum number of tokens allowed
    :return: Number of tokens in the messages
    """
    # Load encoding for the model
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: Model not found. Using default encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    truncated_messages = []
    current_tokens = 0

    if isinstance(messages, str):
        tokens = encoding.encode(messages)
        current_tokens += len(tokens)
    else:
        for message in messages:
            # if 'content' in message:  # message with 'content' field
            content = message.get('content', None)
            if content is None:
                print("Warning: Message content is None. Skipping.")
                break
            if isinstance(content,
                          list):  # If content is a list, it may be prompt_elements and needs further processing
                for element in content:
                    if 'text' in element.get('type', ''):  # Processing text messages
                        text = element['text']
                        tokens = encoding.encode(text)
                        current_tokens += len(tokens)

                        # if current_tokens + len(tokens) <= max_tokens:
                        #     truncated_messages.append(message)
                        #     current_tokens += len(tokens)
                        # else:
                        #     max_addable_tokens = max_tokens - current_tokens
                        #     if max_addable_tokens > 0:
                        #         part_text = encoding.decode(tokens[:max_addable_tokens])
                        #         element['text'] = part_text
                        #         truncated_messages.append(message)
                        #         break
                    # else:
                    #     # Non-text messages
                    #     break
            else:  # content is not a list, directly process text messages
                tokens = encoding.encode(content)
                current_tokens += len(tokens)
                # if current_tokens + len(tokens) <= max_tokens:
                #     truncated_messages.append(message)
                #     current_tokens += len(tokens)
                # else:
                #     max_addable_tokens = max_tokens - current_tokens
                #     if max_addable_tokens > 0:
                #         part_content = encoding.decode(tokens[:max_addable_tokens])
                #         message['content'] = part_content
                #         truncated_messages.append(message)
                #     break

    return current_tokens


def save_token_count_to_file(filename, step_tokens, task_name, global_reward_text_model, planning_text_model, token_pricing):
    """
    Save token count to a file in JSON format.
    :param filename: Name of the file to save the token count
    :param step_tokens: Number of tokens used in steps
    :param task_name: Name of the task associated with the token count
    :param global_reward_text_model: Model used for reward modeling
    :param planning_text_model: Model used for planning
    :param token_pricing: Pricing information for models
    """

    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"calls": [],
                "total_planning_input_tokens": 0,
                "total_planning_output_tokens": 0,
                "total_reward_input_tokens": 0,
                "total_reward_output_tokens": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                }

    call_record = {
        "task_name": task_name,
        "step_tokens": step_tokens
    }

    data["calls"].append(call_record)
    data["total_planning_input_tokens"] += step_tokens["steps_planning_input_token_counts"]
    data["total_planning_output_tokens"] += step_tokens["steps_planning_output_token_counts"]
    data["total_reward_input_tokens"] += step_tokens["steps_reward_input_token_counts"]
    data["total_reward_output_tokens"] += step_tokens["steps_reward_output_token_counts"]
    data["total_input_tokens"] += step_tokens["steps_input_token_counts"]
    data["total_output_tokens"] += step_tokens["steps_output_token_counts"]
    data["total_tokens"] += step_tokens["steps_token_counts"]

    # if "total_planning_input_token_cost" not in data:
    #     if planning_text_model in token_pricing["pricing_models"]:
    #         data["total_planning_input_token_cost"] = 0
    # if "total_planning_input_token_cost" in data:
    if planning_text_model in token_pricing["pricing_models"]:
        if "total_planning_input_token_cost" not in data:
            data["total_planning_input_token_cost"] = 0
        if "total_planning_output_token_cost" not in data:
            data["total_planning_output_token_cost"] = 0
        data["total_planning_input_token_cost"] += step_tokens["steps_planning_input_token_counts"] * token_pricing[f"{planning_text_model}_input_price"]
        data["total_planning_output_token_cost"] += step_tokens["steps_planning_output_token_counts"] * token_pricing[f"{planning_text_model}_output_price"]

    if global_reward_text_model in token_pricing["pricing_models"]:
        if "total_reward_input_token_cost" not in data:
            data["total_reward_input_token_cost"] = 0
        if "total_reward_output_token_cost" not in data:
            data["total_reward_output_token_cost"] = 0
        data["total_reward_input_token_cost"] += step_tokens["steps_reward_input_token_counts"] * token_pricing[f"{global_reward_text_model}_input_price"]
        data["total_reward_output_token_cost"] += step_tokens["steps_reward_output_token_counts"] * token_pricing[f"{global_reward_text_model}_output_price"]

    if planning_text_model in token_pricing["pricing_models"] and global_reward_text_model in token_pricing["pricing_models"]:
        if "total_input_token_cost" not in data:
            data["total_input_token_cost"] = 0
        if "total_output_token_cost" not in data:
            data["total_output_token_cost"] = 0
        if "total_token_cost" not in data:
            data["total_token_cost"] = 0
        data["total_input_token_cost"] += data["total_planning_input_token_cost"] + data["total_reward_input_token_cost"]
        data["total_output_token_cost"] += data["total_planning_output_token_cost"] + data["total_reward_output_token_cost"]
        data["total_token_cost"] += data["total_input_token_cost"] + data["total_output_token_cost"]

    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
