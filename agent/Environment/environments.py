import json5

class BaseEnvironment():

    def __init__(self,configs) -> None:
        self.configs = configs

    def html_denoiser(self):
        """
        """
        pass
    
    def state_init(self):
        """
        """
        pass

    def construct_state_info(self):
        """
        """
        pass

    def save_environment(self)->None:
        """
        """
        pass

class DomEnvironment(BaseEnvironment):

    def __init__(
        self,
        configs : dict,
        dom: str,
        tab_name_list: list,
        current_tab_name: list
    ):
        super().__init__(configs)
        self.configs = configs
        self.dom = dom
        self.tab_name_list = tab_name_list
        self.current_tab_name = current_tab_name

    def html_denoiser(self) -> None:
        """
        extract four elements from dom
        """
        interact_element = []
        link_element = []
        input_element = []
        unknown_element = []

        # 将json格式的dom转换为四种list
        max_token = self.configs["max_token"]
        if self.dom:
            dom = json5.loads(self.dom, encoding='utf-8')
            len_dom = len(dom)
            for element in dom:
                if element["tagName"] == "input" or element["tagName"] == "textarea": # 输入型元素
                    if "value" in element.keys(): # input元素已键入内容
                        input_element.append(f"id:{element['id']}, content:{element['label']}, input_value:{element['value']}")
                    else:# input元素未键入内容
                        self.input_element.append(f"id:{element['id']}, content:{element['label']}")
                elif element["tagName"] == "link": # 链接型元素
                    if len(element['label']) > max_token*2/len_dom: # 限制长度
                        link_element.append(f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
                    else:
                        self.link_element.append(f"id:{element['id']}, content:{element['label']}")
                elif element["tagName"] in ["button","row","checkbox","radio","select","datalist","option","switch"]: # 交互型元素
                    if len(element['label']) > max_token*2/len_dom: # 限制长度
                        interact_element.append(f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
                    else:
                        interact_element.append(f"id:{element['id']}, content:{element['label']}")
                else:
                    unknown_element.append(f"tag:{element['tagName']},id:{element['id']}, content:{element['label']}")

        return interact_element,link_element,input_element,unknown_element

    def state_init(self):
        """
        init state information
        """
        pass

    def construct_state_info(self):
        """
        construct current environment state_info after env denoiser
        """
        pass

    def save_environment(self) -> None:
        """
        """
        pass


class HtmlEnvironment(BaseEnvironment):

    def __init__(self, configs) -> None:
        super().__init__(configs)
        pass
    
    
