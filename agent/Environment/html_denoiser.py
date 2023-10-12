import json5
from Prompt import base_Prompts


class Environment:

    def __init__(self, config) -> None:
        
        """
        Environment:
        state_info: 
        """
        self.current_html_info = None
        self.environment_prompt = {}
        self.interactable_element = []
        self.link_element = []
        self.input_element = []
        self.unknown_element = []
        self.configs = config
        self.state_info = []
    
    def html_denoiser(self, dom)->None:

        """
        dom: document object model 
        return: None
        """

        # 将json格式的dom转换为四种list
        max_token = self.configs["max_token"]
        dom = json5.loads(dom, encoding='utf-8')
        len_dom = len(dom)
        for element in dom:
            if element["tagName"] == "input" or element["tagName"] == "textarea": # 输入型元素
                if "value" in element.keys(): # input元素已键入内容
                    self.input_element.append(f"id:{element['id']}, content:{element['label']}, input_value:{element['value']}")
                else:# input元素未键入内容
                    self.input_element.append(f"id:{element['id']}, content:{element['label']}")
            elif element["tagName"] == "link": # 链接型元素
                if len(element['label']) > max_token*2/len_dom: # 限制长度
                    self.link_element.append(f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
                else:
                    self.link_element.append(f"id:{element['id']}, content:{element['label']}")
            elif element["tagName"] in ["button","row","checkbox","radio","select","datalist","option","switch"]: # 交互型元素
                if len(element['label']) > max_token*2/len_dom: # 限制长度
                    self.interactable_element.append(f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
                else:
                    self.interactable_element.append(f"id:{element['id']}, content:{element['label']}")
            else:
                self.unknown_element.append(f"tag:{element['tagName']},id:{element['id']}, content:{element['label']}")

        return None

    def get_prompt_user_message(self):

        """
        return: construct user's prompt with html denoiser or state_info

        """
        html_denoiser_prompt_user = f"All tabs are {str(self.tab_name_list)}. Now you are on tab '{str(self.current_tab_name)}'. The current elements with id are as follows:\n\n"\
                        f"interactable elements(like button, select and option): {str(self.interactable_element)}\n\n"\
                        f"link element: {str(self.link_element)}\n\n"\
                        f"input elements(like input and textarea): {str(self.input_element)}"
        return html_denoiser_prompt_user


    def state_init(self,):
        """
        """
        pass

    def construct_state_info(self):

        """
        construt current environment state_info after html denoiser
        return : current state_info
        """
        pass


