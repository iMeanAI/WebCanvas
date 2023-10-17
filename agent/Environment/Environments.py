import json5
import configs


class BaseEnvironment:

    def __init__(self, configs: dict = configs.Env_configs) -> None:

        self.current_html_info = None
        self.configs = configs
        self.state_info = None

    def html_denoiser(self) -> None:
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

    def save_environment(self) -> None:
        """
        """
        pass


class DomEnvironment(BaseEnvironment):

    def __init__(self, dom: list, tab_name_list: list, current_tab_name: list, configs: dict = configs.Env_configs) -> None:
        """
        Init Dom environment:
        state_info: 
        """
        super().__init__(configs)

        self.dom = dom
        self.tab_name_list = tab_name_list
        self.current_tab_name = current_tab_name

        self.interactable_element = []
        self.link_element = []
        self.input_element = []
        self.unknown_element = []

    def html_denoiser(self) -> None:
        """
        extract main elements from dom
        return: None
        """

        # 将json格式的dom转换为四种list
        max_token = self.configs["max_token"]
        dom = json5.loads(self.dom, encoding='utf-8')
        len_dom = len(dom)
        for element in dom:
            if element["tagName"] == "input" or element["tagName"] == "textarea":  # 输入型元素
                if "value" in element.keys():  # input元素已键入内容
                    self.input_element.append(
                        f"id:{element['id']}, content:{element['label']}, input_value:{element['value']}")
                else:  # input元素未键入内容
                    self.input_element.append(
                        f"id:{element['id']}, content:{element['label']}")
            elif element["tagName"] == "link":  # 链接型元素
                if len(element['label']) > max_token*2/len_dom:  # 限制长度
                    self.link_element.append(
                        f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
                else:
                    self.link_element.append(
                        f"id:{element['id']}, content:{element['label']}")
            elif element["tagName"] in ["button", "row", "checkbox", "radio", "select", "datalist", "option", "switch"]:  # 交互型元素
                if len(element['label']) > max_token*2/len_dom:  # 限制长度
                    self.interactable_element.append(
                        f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
                else:
                    self.interactable_element.append(
                        f"id:{element['id']}, content:{element['label']}")
            else:
                self.unknown_element.append(
                    f"tag:{element['tagName']},id:{element['id']}, content:{element['label']}")

        return

    def state_init(self,):
        """
        init state information
        """
        pass

    def construct_state_info(self,):
        """
        construct current environment state_info after html denoiser
        return : current state_info
        """
        pass

    def save_environment(self) -> None:
        """
        save main elements from dom
        """
        pass


class HtmlEnvironment(BaseEnvironment):

    def __init__(self, configs) -> None:
        super().__init__(configs)
        pass
