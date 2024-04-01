import json5
import base64
# used for save_screenshot
import os
from PIL import Image
from io import BytesIO
from datetime import datetime


# class Utility:

# data utils
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
    # 获取当前时间戳，格式为年月日时分秒
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    # 替换路径中的非法字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        task_name = task_name.replace(char, '_')

    # 创建任务文件夹（如果不存在）
    if task_name_id is None:
        task_folder = f'results/screenshots/screenshots_{mode}_{record_time}/{task_name}'
    else:
        task_folder = f'results/screenshots/screenshots_{mode}_{record_time}/{task_name_id}_{task_name}'
    if not os.path.exists(task_folder):
        os.makedirs(task_folder)

    # 解码截图
    image_data = base64.b64decode(screenshot_base64)
    image = Image.open(BytesIO(image_data))

    # 构建截图文件名，包含步骤编号、描述和时间戳
    screenshot_filename = f'{task_folder}/Step{step_number}_{timestamp}_{description}.png'

    # 保存截图到指定文件夹
    image.save(screenshot_filename)


def print_limited_json(obj, limit=500, indent=0):
    """
    限制json的长度
    """
    spaces = ' ' * indent
    if isinstance(obj, dict):
        items = []
        for k, v in obj.items():
            formatted_value = print_limited_json(v, limit, indent + 4)
            items.append(f'{spaces}    "{k}": {formatted_value}')
        return f'{spaces}{{\n' + ',\n'.join(items) + '\n' + spaces + '}'
    elif isinstance(obj, list):
        elements = [print_limited_json(element, limit, indent + 4) for element in obj]
        return f'{spaces}[\n' + ',\n'.join(elements) + '\n' + spaces + ']'
    else:
        truncated_str = str(obj)[:limit] + "..." if len(str(obj)) > limit else str(obj)
        return json5.dumps(truncated_str)
    # Usage within the class or externally:
    # result = print_limited_json(your_object)


def print_info(info, color):
    # 打印带有颜色的信息
    print(f"{color}{info}\033[0m")  # \033[0m 用于重置颜色


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
        # 尝试对字符串进行 Base64 解码
        base64.b64decode(s, validate=True)
        return True, "The string is a valid Base64 encoded string."
    except ValueError:
        # 如果解码抛出 ValueError 异常，则字符串不是有效的 Base64 编码
        return False, "The string is NOT a valid Base64 encoded string."


# 原有的代码
def extract_longest_substring(s):
    start = s.find('{')  # Find the first occurrence of '['
    end = s.rfind('}')  # Find the last occurrence of ']'
    # Check if '[' and ']' were found and if they are in the right order
    if start != -1 and end != -1 and end > start:
        return s[start:end + 1]  # Return the longest substring
    else:
        return None  # Return None if no valid substring was found
