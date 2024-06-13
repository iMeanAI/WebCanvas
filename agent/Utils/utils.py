import json5
import base64
# used for save_screenshot
import os
from PIL import Image
from io import BytesIO
from datetime import datetime
# used for download_data and upload_result
import requests
import json

# class Utility:

# data utils


def download_data(url, dest_path):
    response = requests.get(url)
    with open(dest_path, 'wb') as file:
        file.write(response.content)

# def upload_result(url, data):
#     response = requests.post(url, json=data)
#     return response.status_code, response.text


def upload_result(url, data):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.status_code, response.json()


def save_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def read_json_file(file_path):
    """
    Read and parse a JSON file.

    Args:
    - file_path: str, the path of the JSON file.

    Returns:
    - Returns the parsed data on success.
    - Returns an error message on failure.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json5.load(file)
            return data
    except FileNotFoundError:
        return f"File not found: {file_path}"


def save_screenshot(mode: str, record_time: str, task_name: str, step_number: int, description: str,
                    screenshot_base64: str, task_name_id: str = None):

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        task_name = task_name.replace(char, '_')

    if task_name_id is None:
        task_folder = f'results/screenshots/screenshots_{mode}_{record_time}/{task_name}'
    else:
        task_folder = f'results/screenshots/screenshots_{mode}_{record_time}/{task_name_id}_{task_name}'
    if not os.path.exists(task_folder):
        os.makedirs(task_folder)

    image_data = base64.b64decode(screenshot_base64)
    image = Image.open(BytesIO(image_data))

    screenshot_filename = f'{task_folder}/Step{step_number}_{timestamp}_{description}.png'

    image.save(screenshot_filename)


def print_limited_json(obj, limit=500, indent=0):
    """
    """
    spaces = ' ' * indent
    if isinstance(obj, dict):
        items = []
        for k, v in obj.items():
            formatted_value = print_limited_json(v, limit, indent + 4)
            items.append(f'{spaces}    "{k}": {formatted_value}')
        return f'{spaces}{{\n' + ',\n'.join(items) + '\n' + spaces + '}'
    elif isinstance(obj, list):
        elements = [print_limited_json(
            element, limit, indent + 4) for element in obj]
        return f'{spaces}[\n' + ',\n'.join(elements) + '\n' + spaces + ']'
    else:
        truncated_str = str(obj)[:limit] + \
            "..." if len(str(obj)) > limit else str(obj)
        return json5.dumps(truncated_str)
    # Usage within the class or externally:
    # result = print_limited_json(your_object)


def print_info(info, color):
    if color == 'yellow':
        print(f"\033[33m{info}\033[0m")
    elif color == 'red':
        print(f"\033[31m{info}\033[0m")
    elif color == 'green':
        print(f"\033[32m{info}\033[0m")
    elif color == 'cyan':
        print(f"\033[36m{info}\033[0m")
    elif color == 'blue':
        print(f"\033[34m{info}\033[0m")
    elif color == 'purple':
        print(f"\033[35m{info}\033[0m")
    elif color == 'white':
        print(f"\033[37m{info}\033[0m")
    elif color == 'black':
        print(f"\033[30m{info}\033[0m")
    elif color == 'bold':
        print(f"\033[1m{info}\033[0m")
    elif color == 'underline':
        print(f"\033[4m{info}\033[0m")
    else:
        print(f"{color}{info}\033[0m")  # \033[0m


def is_valid_base64(s):
    """
    Validate if a given string is a valid Base64 encoded string.

    :param s: String to be checked.
    :return: A tuple (bool, str) where the first element is True if the string is a valid Base64 encoded string,
             and the second element is a message indicating the result or the type of error.

    Usage:  is_valid, message = is_valid_base64(s)
    This function is only used to determine whether the picture is base64 encoded.
    """
    if s is None:
        return False, "The string is None."

    if not isinstance(s, str):
        return False, "The input is not a string."

    if len(s) == 0:
        return False, "The string is empty."

    try:
        base64.b64decode(s, validate=True)
        return True, "The string is a valid Base64 encoded string."
    except ValueError:
        return False, "The string is NOT a valid Base64 encoded string."


def extract_longest_substring(s):
    start = s.find('{')  # Find the first occurrence of '['
    end = s.rfind('}')  # Find the last occurrence of ']'
    # Check if '[' and ']' were found and if they are in the right order
    if start != -1 and end != -1 and end > start:
        return s[start:end + 1]  # Return the longest substring
    else:
        return None  # Return None if no valid substring was found
