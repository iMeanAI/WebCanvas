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
                    #     # Non-text messages, add directly without counting tokens
                    #     truncated_messages.append(message)
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

        # else:  # message with 'text' field, directly process text messages
        #     text = message['text']
        #     tokens = encoding.encode(text)
        #     if current_tokens + len(tokens) <= max_tokens:
        #         truncated_messages.append(message)
        #         current_tokens += len(tokens)
        #     else:
        #         max_addable_tokens = max_tokens - current_tokens
        #         if max_addable_tokens > 0:
        #             part_text = encoding.decode(tokens[:max_addable_tokens])
        #             message['text'] = part_text
        #             truncated_messages.append(message)
        #         break

    return current_tokens


def save_token_count_to_file(filename, token_count, message_type):
    """
    Save token count to a file in JSON format.
    :param filename: Name of the file to save the token count
    :param token_count: The token count to save
    :param message_type: Type of the message (input/output)
    """
    data = {"calls": [], "total_tokens": 0}

    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        pass

    call_record = {
        "token_count": token_count,
        "type": message_type
    }

    data["calls"].append(call_record)
    data["total_tokens"] += token_count

    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


# Usage example
# messages = [
#     {"role": "system", "content": "Hello, how are you?"},
#     {"role": "user", "content": [
#         {"type": "text", "text": "Here is the accessibility tree that you should refer to for this task:"},
#         {"type": "text", "text": "current screenshot is:"},
#         {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{base64_image}"}}
#     ]},
#     {"role": "user", "content": [
#         {"type": "text", "text": "Here is a longer text that might push the total tokens over the limit depending on the model tokenization."}
#     ]},
#     {"role": "user", "text": "Final message, if space allows."}
# ]
# messages = "nihao"
#
# token_value = calculation_of_token(messages, model='gpt-3.5-turbo')
# filename = "token_counts.json"
# save_token_count_to_file(filename, token_value, "input")
