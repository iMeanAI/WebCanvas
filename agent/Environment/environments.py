import json5
from typing import Any, Union

class DomEnvironment:
    def __init__(
        self,
        dom: str,
        tab_name_list: list,
        current_tab_name: list,
        max_token: int = 16000
    ):
        self.max_token = max_token
        self.dom = dom
        self.tab_name_list = tab_name_list
        self.current_tab_name = current_tab_name

    def html_denoiser(self) -> (list, list, list, list):
        interact_element = []
        link_element = []
        input_element = []
        unknown_element = []
        # 将json格式的dom转换为四种list
        max_token = self.max_token
        if self.dom:
            dom = json5.loads(self.dom, encoding='utf-8')
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
                        interact_element.append(
                            f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
                    else:
                        interact_element.append(
                            f"id:{element['id']}, content:{element['label']}")
                else:
                    unknown_element.append(
                        f"tag:{element['tagName']},id:{element['id']}, content:{element['label']}")

        return interact_element, link_element, input_element, unknown_element

