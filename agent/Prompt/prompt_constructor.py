import json5

from jinja2 import Template

from agent.Prompt.base_Prompts import BasePrompts
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

    request = {"current_tab_name":"一个用于联系的平台 | Zoom","dom":[{"tagname":"link","id":"1","label":"Skip to main content"},{"tagname":"link","id":"2","label":"Accessibility overview"},{"tagname":"button","id":"3","label":"搜索Search在这里输入搜索...Cancel Search"},{"tagname":"input","id":"4","label":"在这里输入搜索...","value":"admin@imean.ai"},{"tagname":"link","id":"5","label":"\n +852.3002.3757\n"},{"tagname":"link","id":"6","label":"\n +852.3002.3757\n"},{"tagname":"button","id":"7","label":"Call 1.888.799.9666"},{"tagname":"link","id":"8","label":"Call 1.888.799.9666"},{"tagname":"link","id":"9","label":"\n联系销售人员"},{"tagname":"link","id":"10","label":"\n联系销售人员"},{"tagname":"link","id":"11","label":"\n申请演示"},{"tagname":"link","id":"12","label":"\n申请演示"},{"tagname":"link","id":"13","label":"Zoom Home Page"},{"tagname":"button","id":"14","label":"产品"},{"tagname":"button","id":"15","label":"解决方案"},{"tagname":"button","id":"16","label":"资源"},{"tagname":"link","id":"17","label":"套餐和定价"},{"tagname":"link","id":"18","label":"套餐和定价"},{"tagname":"link","id":"19","label":"加入"},{"tagname":"link","id":"20","label":"主持 "},{"tagname":"link","id":"21","label":"\n白板"},{"tagname":"link","id":"22","label":"我的账号"},{"tagname":"link","id":"23","label":"learn more about zoom one"},{"tagname":"link","id":"24","label":"套餐和定价"},{"tagname":"link","id":"25","label":"免费注册"},{"tagname":"link","id":"26","label":"套餐和定价"},{"tagname":"link","id":"27","label":"免费注册"},{"tagname":"link","id":"28","label":"套餐和定价"},{"tagname":"link","id":"29","label":"免费注册"},{"tagname":"link","id":"30","label":"套餐和定价"},{"tagname":"link","id":"31","label":"免费注册"},{"tagname":"link","id":"32","label":"套餐和定价"},{"tagname":"link","id":"33","label":"免费注册"},{"tagname":"link","id":"34","label":"Zoom One"},{"tagname":"link","id":"35","label":"Zoom Spaces"},{"tagname":"link","id":"36","label":"Zoom Events"},{"tagname":"link","id":"37","label":"Zoom Contact Center"},{"tagname":"link","id":"38","label":"Zoom Developers"},{"tagname":"link","id":"39","label":"阅读他们的案例"},{"tagname":"link","id":"40","label":"发现无限可能"},{"tagname":"link","id":"41","label":"探索行业解决方案"},{"tagname":"link","id":"42","label":"Education"},{"tagname":"link","id":"43","label":"Financial"},{"tagname":"link","id":"44","label":"Government"},{"tagname":"link","id":"45","label":"Healthcare"},{"tagname":"link","id":"46","label":"Manufacturing"},{"tagname":"link","id":"47","label":"Retail"},{"tagname":"link","id":"48","label":"阅读我们的博客"},{"tagname":"link","id":"49","label":"开始协作"},{"tagname":"link","id":"50","label":"免费注册"},{"tagname":"link","id":"51","label":"免费注册"},{"tagname":"link","id":"52","label":"获得启发"},{"tagname":"link","id":"53","label":"免费注册"},{"tagname":"link","id":"54","label":"套餐和定价"},{"tagname":"link","id":"55","label":"关于"},{"tagname":"link","id":"56","label":"Zoom博客"},{"tagname":"link","id":"57","label":"客户"},{"tagname":"link","id":"58","label":"我们的团队"},{"tagname":"link","id":"59","label":"招贤纳士"},{"tagname":"link","id":"60","label":"集成"},{"tagname":"link","id":"61","label":"合作伙伴"},{"tagname":"link","id":"62","label":"投资者"},{"tagname":"link","id":"63","label":"新闻"},{"tagname":"link","id":"64","label":"可持续性与ESG"},{"tagname":"link","id":"65","label":"媒体资料包"},{"tagname":"link","id":"66","label":"视频教程"},{"tagname":"link","id":"67","label":"开发人员平台"},{"tagname":"link","id":"68","label":"下载"},{"tagname":"link","id":"69","label":"Zoom 桌面客户端"},{"tagname":"link","id":"70","label":"Zoom Rooms客户端"},{"tagname":"link","id":"71","label":"Zoom Rooms Controller"},{"tagname":"link","id":"72","label":"浏览器扩展"},{"tagname":"link","id":"73","label":"Outlook插件"},{"tagname":"link","id":"74","label":"Android应用"},{"tagname":"link","id":"75","label":"Zoom 虚拟背景"},{"tagname":"link","id":"76","label":"销售"},{"tagname":"link","id":"77","label":"1.888.799.9666"},{"tagname":"link","id":"78","label":"联系销售人员"},{"tagname":"link","id":"79","label":"套餐和定价"},{"tagname":"link","id":"80","label":"申请演示"},{"tagname":"link","id":"81","label":"网络研讨会和直播"},{"tagname":"link","id":"82","label":"\n支持"},{"tagname":"link","id":"83","label":"测试Zoom"},{"tagname":"link","id":"84","label":"账户"},{"tagname":"link","id":"85","label":"\n支持中心"},{"tagname":"link","id":"86","label":"学习中心"},{"tagname":"link","id":"87","label":"反馈"},{"tagname":"link","id":"88","label":"联系我们"},{"tagname":"link","id":"89","label":"无障碍访问"},{"tagname":"link","id":"90","label":"开发人员支持"},{"tagname":"link","id":"91","label":"隐私、安全、法律政策和《现代奴隶制法案》透明度声明"},{"tagname":"link","id":"92","label":"简体中文简体中文"},{"tagname":"link","id":"93","label":"港元($)港元($)"},{"tagname":"link","id":"94","label":"Zoom on 博客Zoom on 博客"},{"tagname":"link","id":"95","label":"Zoom on LinkedInZoom on LinkedIn"},{"tagname":"link","id":"96","label":"Zoom on TwitterZoom on Twitter"},{"tagname":"link","id":"97","label":"Zoom on YoutubeZoom on Youtube"},{"tagname":"link","id":"98","label":"Zoom on FacebookZoom on Facebook"},{"tagname":"link","id":"99","label":"Zoom on InstagramZoom on Instagram"},{"tagname":"link","id":"100","label":"条款"},{"tagname":"link","id":"101","label":"隐私"},{"tagname":"link","id":"102","label":"信任中心"},{"tagname":"link","id":"103","label":"可接受使用准则"},{"tagname":"link","id":"104","label":"法律与合规性"},{"tagname":"link","id":"105","label":"您的隐私选择"},{"tagname":"link","id":"106","label":"Cookie偏好设置"},{"tagname":"button","id":"107","label":"Chat with bot"}],"tab_name_list":["一个用于联系的平台 | Zoom"],"previous_traces":[{"thought":"To create a Zoom meeting that includes admin@imean.ai, I need to navigate to the Zoom website and perform the necessary actions.","action":"goto: https://zoom.us/"},{"thought":"click: Sign In","action":"I will input 'admin@imean.ai' in the search bar to find the option to create a meeting."},{"thought":"The previous actions have not completed the task yet. The next step is to fill_form: {'email': 'admin@imean.ai', 'password': '*****'} and then click: 'Sign In'.","action":"I will input 'admin@imean.ai' in the search bar to find the option to create a meeting."},{"thought":"'loop'","action":"I will input 'admin@imean.ai' in the search bar to find the option to create a meeting."}],"rsp":{"error_message":"","action_type":"fill_and_search","description":{"thought":"'loop'","action":"I will input 'admin@imean.ai' in the search bar to find the option to create a meeting."},"id":"4","uuid":"DsG0kMz2jFkfAAGMskmny","value":"admin@imean.ai"}}
    user_request = ""
    plan = PlanningPromptConstructor().construct(user_request=user_request,previous_trace=request["previous_traces"],dom=request["dom"],tab_name_list=request["tab_name_list"],current_tab_name=request["current_tab_name"])
    print(plan)