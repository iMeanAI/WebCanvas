import traceback
import json5
from agent.Plan import *

from os import environ
from sanic import Request, Sanic, response
from sanic.log import logger

from agent.configs import Env_configs
from agent.Environment.Environments import DomEnvironment
from agent.Memory.short_memory.history import HistoryMemory

app = Sanic("imean-context-gpt35")
SOLAR_APP_VERSION = environ.get("SOLAR_APP_VERSION", "dev")

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
        previous_trace = request.json['previous_trace'] #include previous traces and description of previous states
        cached_data = request.json['cached_info'] # include previous cached information
        dom = request.json['dom']

        Prompt_user = ""
        Prompt_system = ""

        if len(previous_trace) > 0:
            
            # add thought and action prompt base on previous trace 
            thought_and_action_output = HistoryMemory(previous_trace).construct_previous_trace_prompt()
            Prompt_user += thought_and_action_output

            # if finish
            prompt_user_if_finish = Prompt_user + ""
            messages_if_finish = ""

            # construct Env prompt
            env = DomEnvironment(configs=Env_configs,dom=dom,tab_name_list=tab_name_list,current_tab_name=current_tab_name)
            Prompt_user += env.construct_user_prompt()

        messages = [{"role":"system","content":Prompt_system},{"role": "user", "content": Prompt_user}]

        decoded_result = {'element_id':'','action':'','action_input':'','description':''}

        dict_to_write = {}
        dict_to_write['uuid'] = uuid
        dict_to_write['id'] = decoded_result['element_id']
        dict_to_write['action_type'] = decoded_result['action']
        dict_to_write['value'] = decoded_result['action_input']
        dict_to_write['description'] = decoded_result['description']

        # dict_to_write['execute_time'] = execute_time
        # dict_to_write['error_message'] = error_message
        # dict_to_write['openai_response'] = openai_response

        return dict_to_write

    uuid = request.json['uuid']
    user_request = request.json["request"]
    tab_name_list = request.json["tab_name_list"]
    current_tab_name = request.json["current_tab_name"]
    current_time = request.json['current_time']
    previous_trace = request.json['previous_trace'] #include previous traces and description of previous states
    # cached_data = request.json['cached_info'] # include previous cached information
    dom = request.json['dom']
    for i in range(3):
        try:
            dict_to_write = await Planning.plan(uuid=uuid, user_request=user_request, tab_name_list=tab_name_list, current_tab_name=current_tab_name, current_time=current_time, previous_trace=previous_trace, dom=dom)
            if dict_to_write is not None:
                break
        except Exception as e:
            traceback.print_exc()
            continue
    logger.info('process success!!!')
    return response.text("version: " + SOLAR_APP_VERSION)



if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8000)