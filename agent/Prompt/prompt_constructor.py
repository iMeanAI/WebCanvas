import json5
from agent.Prompt.base_Prompts import BasePrompts
from jinja2 import Template

from agent.Environment.Environments import DomEnvironment
from agent.Memory.short_memory.history import HistoryMemory
from agent.configs import Env_configs


class PromptConstructor:
    def __init__(self):
        pass


class PlanningPromptConstructor(PromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.planning_prompt_system
        self.prompt_user = BasePrompts.planning_prompt_user

    # 构建planning的prompt，输出openai可解析的格式

    def construct(self, user_request: str, previous_trace: str, dom: str, tab_name_list: list, current_tab_name: str, max_token: int = 16000) -> list:
        
        # init prompt_user
        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request)
        
        if len(previous_trace) > 0:
            # init Environment 
            env = DomEnvironment(configs=Env_configs,dom=dom,tab_name_list=tab_name_list,current_tab_name=current_tab_name)
            # add history memory
            self.prompt_user += HistoryMemory(previous_trace=previous_trace).ConstructPreviousTracePrompt()
            self.prompt_user += env.ConstructEnvPrompt()

        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        
        return messages


class RewardPromptConstructor(PromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.reward_prompt_system
        self.prompt_user = BasePrompts.reward_prompt_user

    def construct(self, user_request: str, stringfy_thought_and_action_output: str) -> list:
        self.prompt_user = Template(self.prompt_user).render(
            user_request=user_request, stringfy_thought_and_action_output=stringfy_thought_and_action_output)
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages


class JudgeSearchbarPromptConstructor(PromptConstructor):
    def __init__(self):
        self.prompt_system = BasePrompts.judge_searchbar_prompt_system
        self.prompt_user = BasePrompts.judge_searchbar_prompt_user

    # TODO 改掉decoded_result
    def constructor(self, user_request: str, input_element, decoded_result) -> list:
        self.prompt_user = Template(self.prompt_user).render(input_element=str(
            input_element), element_id=decoded_result['element_id'], action_input=decoded_result['action_input'])
        messages = [{"role": "system", "content": self.prompt_system}, {
            "role": "user", "content": self.prompt_user}]
        return messages


if __name__ == "__main__":

    res = BasePrompts.planning_prompt_system
    # request = {"currenttabname":"Tsinghua University official website - Google Search","dom":[{"tagname":"link","id":"1","label":"Skip to main content"},{"tagname":"link","id":"2","label":"Turn off continuous scrolling"},{"tagname":"link","id":"3","label":"Accessibility help"},{"tagname":"link","id":"4","label":"Accessibility feedback"},{"tagname":"link","id":"5","label":"Go to Google Home"},{"tagname":"textarea","id":"6","label":"Search"},{"tagname":"button","id":"7","label":" Clear"},{"tagname":"button","id":"8","label":"Search by voice"},{"tagname":"button","id":"9","label":"Search by image"},{"tagname":"button","id":"10","label":"Search"},{"tagname":"button","id":"11","label":"Settings"},{"tagname":"link","id":"12","label":"Google apps"},{"tagname":"link","id":"13","label":"Google Account: ivan a  \n(ivanty0111@gmail.com)"},{"tagname":"link","id":"14","label":"Add Login"},{"tagname":"link","id":"15","label":"Images"},{"tagname":"link","id":"16","label":"Add Admissions"},{"tagname":"link","id":"17","label":"Add Degrees"},{"tagname":"link","id":"18","label":"Add Courses"},{"tagname":"link","id":"19","label":"News"},{"tagname":"link","id":"20","label":"Videos"},{"tagname":"link","id":"21","label":"Shopping"},{"tagname":"link","id":"22","label":"Maps"},{"tagname":"button","id":"23","label":"All filters"},{"tagname":"button","id":"24","label":"Tools"},{"tagname":"button","id":"25","label":"SafeSearch"},{"tagname":"link","id":"26","label":"清华大学https://www.tsinghua.edu.cn"},{"tagname":"button","id":"27","label":"About this result"},{"tagname":"link","id":"28","label":"International Students"},{"tagname":"link","id":"29","label":"Schools & Departments"},{"tagname":"link","id":"30","label":"Admissions"},{"tagname":"link","id":"31","label":"Programs in English"},{"tagname":"link","id":"32","label":"More results from tsinghua.edu.cn »"},{"tagname":"link","id":"33","label":"清华大学"},{"tagname":"button","id":"34","label":"About this result"},{"tagname":"button","id":"35","label":"About this result"},{"tagname":"button","id":"36","label":"What is the Harvard of China?What is the Harvard of China?What is the Harvard of China?What is the Harvard of China?"},{"tagname":"button","id":"37","label":"How hard is it to get into Tsinghua University in China?How hard is it to get into Tsinghua University in China?How hard is it to get into Tsinghua University in China?How hard is it to get into Tsinghua University in China?"},{"tagname":"button","id":"38","label":"What GPA do you need for Tsinghua University?What GPA do you need for Tsinghua University?What GPA do you need for Tsinghua University?What GPA do you need for Tsinghua University?"},{"tagname":"button","id":"39","label":"Is Tsinghua University Ivy League?Is Tsinghua University Ivy League?Is Tsinghua University Ivy League?Is Tsinghua University Ivy League?"},{"tagname":"button","id":"40","label":"Feedback"},{"tagname":"link","id":"41","label":"Wikipediahttps://en.wikipedia.org"},{"tagname":"button","id":"42","label":"About this result"},{"tagname":"link","id":"43","label":"Tsinghua Undergraduate Admissionshttps://international.join-tsinghua.edu.cn"},{"tagname":"button","id":"44","label":"About this result"},{"tagname":"link","id":"45","label":"Tsinghua Undergraduate Admissionshttps://international.join-tsinghua.edu.cn"},{"tagname":"button","id":"46","label":"About this result"},{"tagname":"link","id":"47","label":"National Tsing Hua University"},{"tagname":"button","id":"48","label":"About this result"},{"tagname":"link","id":"49","label":"U.S. News & World Reporthttps://www.usnews.com"},{"tagname":"button","id":"50","label":"About this result"},{"tagname":"link","id":"51","label":"Schwarzman Scholars"},{"tagname":"button","id":"52","label":"About this result"},{"tagname":"button","id":"53","label":"About this result"},{"tagname":"link","id":"54","label":"Tsinghua university official website login"},{"tagname":"link","id":"55","label":"Tsinghua university official website degrees"},{"tagname":"link","id":"56","label":"Tsinghua university official website courses"},{"tagname":"link","id":"57","label":"Tsinghua university official website admissions"},{"tagname":"link","id":"58","label":" university"},{"tagname":"link","id":"59","label":"tsinghua university "},{"tagname":"link","id":"60","label":"tsinghua university "},{"tagname":"link","id":"61","label":"tsinghua university "},{"tagname":"link","id":"62","label":"More results"}],"tabnamelist":["Tsinghua University official website - Google Search"],"previoustraces":[{"thought":"To find the link to the Tsinghua University admissions page, I can use Google search to look for the official website. Once I find the website, I can click on the link to go to the admissions page.","action":"I will search for the Tsinghua University official website on Google."},{"thought":"goto(\"https://www.tsinghua.edu.cn/en/index.htm\")","action":"I will click on the link to go to the Tsinghua University admissions page."}],"rsp":{"error_message":"","action_type":"click","description":{"thought":"goto(\"https://www.tsinghua.edu.cn/en/index.htm\")","action":"I will click on the link to go to the Tsinghua University admissions page."},"id":"57","uuid":"Tr0iy_wjuYNvN8G5x9VID","value":"link"}}
    # print(request.keys())
    # print(request["currenttabname"])
    # print(request["previoustraces"])
    # print(request["tabnamelist"])
    # print(request["dom"])
    # print(request["rsp"])
    # PlanningPromptConstructor().construct(user_request="123",previous_trace="[]",)
    # print(res)
