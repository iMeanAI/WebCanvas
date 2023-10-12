import json5


def stringfy_thought_and_action(input_list):
    input_list = json5.loads(input_list, encoding="utf-8")
    str_output = "["
    for idx, i in enumerate(input_list):
        str_output += f'Step{idx+1}:\"Thought: {i["thought"]}, Action: {i["action"]}\";\n'
    str_output += "]"
    # logger.info(f"\033[32m\nstr_output\n{str_output}\033[0m")#绿色
    # logger.info(f"str_output\n{str_output}")
    return str_output


def extract_longest_substring(s):
    start = s.find('{')  # Find the first occurrence of '['
    end = s.rfind('}')  # Find the last occurrence of ']'
    # Check if '[' and ']' were found and if they are in the right order
    if start != -1 and end != -1 and end > start:
        return s[start:end+1]  # Return the longest substring
    else:
        return None  # Return None if no valid substring was found


def process_dom(dom: str, max_token: int = 16000):
    interactable_element = []
    link_element = []
    input_element = []
    unknown_element = []

    dom = json5.loads(dom, encoding='utf-8')
    len_dom = len(dom)
    for element in dom:
        if element["tagName"] == "input" or element["tagName"] == "textarea":  # 输入型元素
            if "value" in element.keys():  # input元素已键入内容
                input_element.append(
                    f"id:{element['id']}, content:{element['label']}, input_value:{element['value']}")
            else:  # input元素未键入内容
                input_element.append(
                    f"id:{element['id']}, content:{element['label']}")
        elif element["tagName"] == "link":  # 链接型元素
            if len(element['label']) > max_token*2/len_dom:  # 限制长度
                link_element.append(
                    f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
            else:
                link_element.append(
                    f"id:{element['id']}, content:{element['label']}")
        elif element["tagName"] in ["button", "row", "checkbox", "radio", "select", "datalist", "option", "switch"]:  # 交互型元素
            if len(element['label']) > max_token*2/len_dom:  # 限制长度
                interactable_element.append(
                    f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
            else:
                interactable_element.append(
                    f"id:{element['id']}, content:{element['label']}")
        else:
            unknown_element.append(
                f"tag:{element['tagName']},id:{element['id']}, content:{element['label']}")
    return interactable_element, link_element, input_element, unknown_element
