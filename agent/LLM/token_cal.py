import json


def estimate_tokens(text):
    """Estimate the number of tokens for a given text."""
    return len(text) / 4.8


def truncate_text(text, max_length):
    """Truncate text to fit within the maximum length."""
    return text[:max_length]


def process_content(content, remaining_tokens):
    """Process and possibly truncate content based on remaining token allowance."""
    if isinstance(content, list):
        truncated_content = []
        used_tokens = 0
        for item in content:
            if item['type'] == 'text':
                item_text = item['text']
                item_tokens = estimate_tokens(item_text)
                if used_tokens + item_tokens > remaining_tokens:
                    max_length = int((remaining_tokens - used_tokens) * 4.8)
                    truncated_text = truncate_text(item_text, max_length)
                    truncated_content.append({'type': 'text', 'text': truncated_text})
                    used_tokens += estimate_tokens(truncated_text)
                    break
                truncated_content.append(item)
                used_tokens += item_tokens
            # elif item['type'] == 'image_url':
            #     # Assuming image URLs use a fixed number of tokens
            #     image_tokens = 10
            #     if used_tokens + image_tokens > remaining_tokens:
            #         continue  # Skip adding this image and continue to next item
            #     truncated_content.append(item)
            #     used_tokens += image_tokens
        return truncated_content, used_tokens
    else:
        # Simple text content
        tokens = estimate_tokens(content)
        if tokens > remaining_tokens:
            truncated_content = truncate_text(content, int(remaining_tokens * 4.8))
            return truncated_content, estimate_tokens(truncated_content)
        return content, tokens


def truncate_messages_based_on_estimated_tokens(messages, max_tokens):
    """Truncate a list of messages based on an estimated token limit, using available tokens as fully as possible."""
    current_tokens = 0
    truncated_messages = []

    for message in messages:
        content = message['content']
        processed_content, used_tokens = process_content(content, max_tokens - current_tokens)
        if used_tokens > 0:
            truncated_messages.append({'role': message['role'], 'content': processed_content})
            current_tokens += used_tokens
        if current_tokens >= max_tokens:
            break

    return truncated_messages

# Usage example
# messages = [
#     {"role": "system", "content": "aaaaaaaaaaa"},
#     {"role": "user", "content": "aaa"},
#     {"role": "user", "content": [
#         {"type": "text", "text": "\nHere is the accessibility tree that you should refer to for this task:\nobservation"},
#         {"type": "text", "text": "current screenshot is:"},
#         {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,base64_image_data"}}
#     ]}
# ]

# Truncate the message list with a maximum token limit
# max_allowed_tokens = 100
# truncated_messages = truncate_messages_based_on_estimated_tokens(messages, max_tokens=max_allowed_tokens)
# # for msg in truncated_messages:
# #     print(msg)
# print(json.dumps(truncated_messages, indent=4))
