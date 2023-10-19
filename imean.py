import traceback
import json5
from agent.Plan import *

from os import environ
from sanic import Request, Sanic, response
from sanic.log import logger

from agent.configs import Env_configs
from agent.Environment.environments import DomEnvironment
from agent.Memory.short_memory.history import HistoryMemory

app = Sanic("imean-context-gpt35")
SOLAR_APP_VERSION = environ.get("SOLAR_APP_VERSION", "dev")

@app.get("/")
async def health(request: Request):
    return response.text("version: " + SOLAR_APP_VERSION)


@app.post("/api/contextual_planning")
async def planning(request: Request):
    logger.info('process start!')


    uuid = request.json['uuid']
    user_request = request.json["request"]
    tab_name_list = request.json["tab_name_list"]
    current_tab_name = request.json["current_tab_name"]
    current_time = request.json['current_time']
    previous_trace = request.json['previous_trace'] #include previous traces and description of previous states
    # cached_data = request.json['cached_info'] # include previous cached information
    dom = request.json['dom']
    for _ in range(3):
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