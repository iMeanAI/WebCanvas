import json
import openai
import time
import logging
import json5
import re
import asyncio
import traceback


from concurrent.futures import ThreadPoolExecutor, as_completed
from retry import retry
from functools import partial
import multiprocessing
# logging.basicConfig(level=logging.DEBUG)

from os import environ
from sanic import Request, Sanic, response
from sanic.log import logger

# import cohere
# cohere_key = environ.get('COHERE_API_KEY')
# co = cohere.Client(cohere_key)


SOLAR_APP_VERSION = environ.get("SOLAR_APP_VERSION", "dev")

openai.api_key = environ.get("OPENAI_API_KEY")
# get API key from top-right dropdown on OpenAI website
MODEL = environ.get("OPENAI_MODEL", "gpt-3.5-turbo-16k-0613")

example_output = '\n```\n{\n  "action": "click",\n  "action_input": "link",\n  "element_id": "14",\n  "description": "Now I\'m on Google\'s main page. I should input text into the search bar. Then I will select the correct link from the result page."\n}\n```'

app = Sanic("imean-context-gpt35")

max_token = 16000

@app.get("/")
async def health(request: Request):
    return response.text("version: " + SOLAR_APP_VERSION)


@app.post("/api/contextual_planning")
async def planning(request: Request):
    logger.info('process start!')
    
    async def planning_(request: Request):
        uuid = request.json['uuid']
        user_request = request.json["request"]
        tab_name_list = request.json["tab_name_list"]
        current_tab_name = request.json["current_tab_name"]
        current_time = request.json['current_time']
        previous_trace = request.json['previous_trace']
        dom = request.json['dom']
        error_message = ''

        interactable_element = []
        link_element = []
        input_element = []
        unknown_element = []

        prompt_system = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can. You have access to the following tools:\n\n"\
            "goto: useful for when you need visit a link or a website, it will open a new tab\n"\
            "fill_form: useful for when you need to fill out a form on the current website. Input should be a string\n"\
            "google_search: useful for when you need to use google to search something\n"\
            "switch_tab: useful for when you need to switch tab\n"\
            "click: useful for when you need to click a button/link\n"\
            "The way you use the tools is by specifying a json blob.\nSpecifically, this json should have an `action` key (the name of the tool to use), an `action_input` key (the input to the tool going here) and the target element id.\n\n"\
            "The only values that should be in the \"action\" field are: goto, fill_form, google_search, switch_tab, click\n\n"\
            "A proper description contains:1. What website it is; 2. Which action do you choose; 3. Your next action plan to do.\nREMEMBER DO NOT LEAVE THE DESCRIPTION EMPTY!\n"\
            "Here is an example of a valid $JSON_BLOB:\n\n```\n{\n  \"action\": $TOOL_NAME,\n  \"action_input\": $INPUT,\n  \"element_id\": $TARGET_ELEMENT_ID,\n  \"description\": $ACTION_DESCRIPTION\n}\n```\n\n"\
            f"Example action output:{str(example_output)}\n"\
            "Also, you should follow the instructions below:\n"\
            "1. ALWAYS use the following format:\nThought: you should always consider previous and subsequent steps and what to do\nAction:\n```\n$JSON_BLOB\n```"\
            "2. You must return a valid $JSON_BLOB like above or I can't read it.\n"\
            "3. You should only return one JSON blob as the result."\
            "4. Your action should not be the same as last step's action."
            
        prompt_user = f"The question here is described as \"{user_request}\".\n\n"
        
        def stringfy_thought_and_action(input_list):
            input_list = json5.loads(input_list, encoding="utf-8")
            str_output = "["
            for idx, i in enumerate(input_list):
                str_output += f'Step{idx+1}:\"Thought: {i["thought"]}, Action: {i["action"]}\";\n'
            str_output += "]"
            # logger.info(f"\033[32m\nstr_output\n{str_output}\033[0m")#绿色
            # logger.info(f"str_output\n{str_output}")
            return str_output
        if len(previous_trace) > 0:
            # 将json格式的dom转换为四种list
            dom = json5.loads(dom, encoding='utf-8')
            len_dom = len(dom)
            for element in dom:
                if element["tagName"] == "input" or element["tagName"] == "textarea": # 输入型元素
                    if "value" in element.keys(): # input元素已键入内容
                        input_element.append(f"id:{element['id']}, content:{element['label']}, input_value:{element['value']}")
                    else:# input元素未键入内容
                        input_element.append(f"id:{element['id']}, content:{element['label']}")
                elif element["tagName"] == "link": # 链接型元素
                    if len(element['label']) > max_token*2/len_dom: # 限制长度
                        link_element.append(f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
                    else:
                        link_element.append(f"id:{element['id']}, content:{element['label']}")
                elif element["tagName"] in ["button","row","checkbox","radio","select","datalist","option","switch"]: # 交互型元素
                    if len(element['label']) > max_token*2/len_dom: # 限制长度
                        interactable_element.append(f"id:{element['id']}, content:{element['label'][:int(max_token*2/len_dom)]}")
                    else:
                        interactable_element.append(f"id:{element['id']}, content:{element['label']}")
                else:
                    unknown_element.append(f"tag:{element['tagName']},id:{element['id']}, content:{element['label']}")
            stringfy_thought_and_action_output = stringfy_thought_and_action(previous_trace)
            prompt_user += f"The previous thoughts and actions are: {stringfy_thought_and_action_output}.\n\nYou have done the things above.\n\n"
            
            prompt_user_if_finish = prompt_user + "Tools are goto(jump to url), fill_form(fill in the blank), google_search, switch_tab(switch window tab) and click. You should only use tools above!\n"\
                "Consider whether previous actions have done the task(ignore the detail actions)?\nIf true, just return 'finished'(without quotation marks);\nElse, return what's next step you plan to do.\n"\
                "For example, if your goal is to set up a calendar or meeting or send an e-mail, you should not output 'finished' until you click send/submit/save button;"\
                "If your goal is to goto somewhere and get some information, you should not output 'finished' until you see the correct information on webpage.\n"\
                "If you find that the actions of the last two steps are the same, it is determined that the process is stuck in a local optimum solution and you should output 'loop'(without quotation marks)."\
                "If you find that the task is too difficult to complete, you should output 'hard'."\
                "Take a deep breath, please think carefully!"
            messages_if_finish = [{"role":"system","content":"You are an assistant to help navigate and operate the web page to achieve certain goals."},
                            {"role": "user", "content": prompt_user_if_finish}]
            
            prompt_user += f"All tabs are {str(tab_name_list)}. Now you are on tab '{str(current_tab_name)}'. The current elements with id are as follows:\n\n"\
                f"interactable elements(like button, select and option): {str(interactable_element)}\n\n"\
                f"link element: {str(link_element)}\n\n"\
                f"input elements(like input and textarea): {str(input_element)}"
            
            if len(unknown_element) > 0:
                prompt_user += f"\n\nother elements with tagname: {str(unknown_element)}"
        
        # prompt_user += "\n\nLet's think step by step."
        messages = [{"role":"system","content":prompt_system},{"role": "user", "content": prompt_user}]
        
        start_time = time.time()

        OpenAI_error_flag = False
        
        async def generate_35(messages):
            loop = asyncio.get_event_loop()
            data = {
                'model':"gpt-3.5-turbo-16k-0613",
                'max_tokens': 500,
                'temperature': 0.7,
                'messages': messages,
                'stop': ["Observation:"]
            }
            func = partial(openai.ChatCompletion.create, **data)
            return await loop.run_in_executor(None, func)
        async def generate_4(messages):
            loop = asyncio.get_event_loop()
            data = {
                'model':"gpt-4",
                'max_tokens': 500,
                'temperature': 0.7,
                'messages': messages,
                'stop': ["Observation:"]
            }
            func = partial(openai.ChatCompletion.create, **data)
            return await loop.run_in_executor(None, func)
        
        try:
            future_if_finish_result = ""
            prompt_user = prompt_user.replace("\n","\\n")
            logger.info(f"\033[33muser_request: {user_request}\033[0m")#黄色
            logger.info(f"\033[33m{prompt_user}\033[0m")#黄色

            cpu_count = multiprocessing.cpu_count()
            with ThreadPoolExecutor(max_workers = cpu_count * 2) as pool:
                future_answer = pool.submit(generate_35, messages)
                if len(previous_trace) > 0:
                    future_if_finish = pool.submit(generate_4, messages_if_finish)
                
                future_answer_result = await future_answer.result()
                if len(previous_trace) > 0:
                    future_if_finish_result = json5.loads((await future_if_finish.result()).choices[0])["message"]["content"]

            # openai_response = generate(messages)
            
            pool.shutdown()
            openai_response = future_answer_result
        except openai.error.APIError as e:
        #Handle API error here, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
            error_message = f"OpenAI API returned an API Error: {e}"
            OpenAI_error_flag = True
            pass
        except openai.error.APIConnectionError as e:
            #Handle connection error here
            error_message = f"Failed to connect to OpenAI API: {e}"
            OpenAI_error_flag = True
            print(f"Failed to connect to OpenAI API: {e}")
            pass
        except openai.error.RateLimitError as e:
            #Handle rate limit error (we recommend using exponential backoff)
            OpenAI_error_flag = True
            error_message = f"OpenAI API request exceeded rate limit: {e}"
            print(f"OpenAI API request exceeded rate limit: {e}")
            pass    
        end_time = time.time()
        execute_time = end_time - start_time
        # response_json = json.loads(response.to_json())
        
        if OpenAI_error_flag == False:
            if future_if_finish_result.lower() in ["finished", "loop", "hard"]:
                dict_to_write = {}
                dict_to_write['uuid'] = uuid
                dict_to_write['action_type'] = "stop"
                dict_to_write['execute_time'] = execute_time
                dict_to_write['error_message'] = error_message
                dict_to_write['openai_response'] = openai_response
            else:
                my_openai_obj = list(openai_response.choices)[0]
                result = my_openai_obj.to_dict()['message']['content']
                # logger.info(f"\033[32mopenai result:\n{result}\033[0m")#绿色
                logger.info(f"\033[32mopenai result:\n{result}\033[0m")#绿色
                result_thought = "null"
                try:
                    result_thought = re.findall("Thought:(.*?)Action:",result ,re.S)[0].strip()
                except:
                    try:
                        result_thought = result.split("Action:")[0].strip()
                    except:
                        result_thought = "null"
                try:
                    result_action = re.findall("```(.*?)```",result ,re.S)[0]
                except:
                    result_action = result.split("Action:")[-1].strip()
                # logger.info(f"\033[35m\nThought: {result_thought}\033[0m")#紫色
                # logger.info(f"\033[35m\nAction: {result_action}\033[0m")#紫色
                logger.info(f"Thought(GPT-4): {future_if_finish_result}\nAction: {result_action}")
                

                def extract_longest_substring(s):
                    start = s.find('{')  # Find the first occurrence of '['
                    end = s.rfind('}')  # Find the last occurrence of ']'
                    if start != -1 and end != -1 and end > start:  # Check if '[' and ']' were found and if they are in the right order
                        return s[start:end+1]  # Return the longest substring
                    else:
                        return None  # Return None if no valid substring was found
                    
                def add_description(s):
                    return f'{s["action"]}: {s["action_input"]}'
                    

                # check and refine the format
                Format_flag = True
                result_action_substring = extract_longest_substring(result_action)
                
                try:
                    decoded_result = json5.loads(result_action_substring)
                except Exception as e:
                    logger.info(f"Error parsing:\n{result_action_substring}\n")
                    traceback.print_exc()

                # 判断是否需要搜索操作（按下按钮/回车）
                if decoded_result["action"] == "fill_form":
                    prompt_system_if_search = "You are an assistant to help navigate and operate the web page to achieve certain goals. Answer the following questions as best you can.\n"\
                        f"Your target is to judge whether the input is the search bar.\n"
                    prompt_user_if_search = f"Now the webpage's input elements are below: {str(input_element)}\n"\
                        f"Last step you have fill in the input(id={decoded_result['element_id']}) with text:{decoded_result['action_input']}"\
                        "Judge whether the input is the search bar. If the blank is search bar, return yes, else return no. You should only return one word!"
                    message_if_search = [{"role":"system","content":prompt_system_if_search},{"role": "user", "content": prompt_user_if_search}]
                    logger.info(f"prompt_user_if_search:{prompt_user_if_search}")
                    cpu_count = multiprocessing.cpu_count()
                    with ThreadPoolExecutor(max_workers = cpu_count) as pool:
                        future_if_search = pool.submit(generate_35, message_if_search)
                        future_if_search_result = json5.loads((await future_if_search.result()).choices[0])["message"]["content"]
                        logger.info(f"future_if_search_result:{future_if_search_result}")
                        if future_if_search_result.lower() == "yes":
                           decoded_result["action"] = "fill_and_search"

                # decoded_result["description"]增加thought和description
                if "description" not in decoded_result.keys():
                    decoded_result["description"] = add_description(decoded_result)
                dict = {}
                if len(future_if_finish_result) > 0:
                    dict["thought"] = future_if_finish_result # result_thought
                else:
                    dict["thought"] = result_thought
                dict["action"] = decoded_result["description"]
                decoded_result["description"] = dict


                for element in ["element_id", "action", "action_input"]:
                    if element not in decoded_result.keys():
                        decoded_result[element] = ""
                dict_to_write = {}
                dict_to_write['uuid'] = uuid
                dict_to_write['id'] = decoded_result['element_id']
                dict_to_write['action_type'] = decoded_result['action']
                dict_to_write['value'] = decoded_result['action_input']
                dict_to_write['description'] = decoded_result['description']
                dict_to_write['execute_time'] = execute_time
                dict_to_write['error_message'] = error_message
                dict_to_write['openai_response'] = openai_response
                # dict_to_write['refine'] = refine_flag
        else:
            dict_to_write = {}
            dict_to_write['uuid'] = uuid
            dict_to_write['id'] = ''
            dict_to_write['action_type'] = ''
            dict_to_write['value'] = ''
            dict_to_write['description'] = ''
            dict_to_write['execute_time'] = execute_time
            dict_to_write['error_message'] = error_message
            dict_to_write['openai_response'] = openai_response
            # dict_to_write['refine'] = refine_flag
        # logger.info(dict_to_write)
        return dict_to_write
    for i in range(3):
        try:
            dict_to_write = await planning_(request)
            if dict_to_write is not None:
                break
        except Exception as e:
            traceback.print_exc()
            continue
    logger.info('process success!!!')
    return response.json(dict_to_write)



if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8000)
