from typing import Any
import openai
import asyncio
from functools import partial
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from sanic.log import logger
from agent.Utils import *


# GPTGenerator类用于生成GPT模型的请求
class GPTGenerator:
    def __init__(self):
        self.model = ""  # 初始化时模型名称为空

    # 异步请求方法，用于发送请求到GPT模型
    async def request(self, messages: list = None, max_tokens: int = 500, temperature: float = 0.7
                      ) -> (str, str):  # image: str = None
        try:
            cpu_count = multiprocessing.cpu_count()  # 获取CPU核心数量
            # 使用线程池执行器，线程数为CPU核心数的两倍
            with ThreadPoolExecutor(max_workers=cpu_count * 2) as pool:
                # 提交chat方法到线程池
                future_answer = pool.submit(
                    self.chat, messages, max_tokens, temperature)  #, image
                # 等待future_answer的结果
                future_answer_result = await future_answer.result()
                # 提取OpenAI的响应
                openai_response = list(future_answer_result.choices)[
                    0].to_dict()['message']['content']
                pool.shutdown()  # 关闭线程池
                return openai_response, ""  # 返回OpenAI的响应和空字符串
        except openai.error.APIError as e:
            # 处理API错误
            logger.error(f"OpenAI API returned an API Error: {e}")
            error_message = f"OpenAI API returned an API Error: {e}"
            OpenAI_error_flag = True
            return "", error_message
        except openai.error.APIConnectionError as e:
            # 处理API连接错误
            error_message = f"Failed to connect to OpenAI API: {e}"
            OpenAI_error_flag = True
            logger.error(f"Failed to connect to OpenAI API: {e}")
            return "", error_message
        except openai.error.RateLimitError as e:
            # 处理API速率限制错误
            OpenAI_error_flag = True
            error_message = f"OpenAI API request exceeded rate limit: {e}"
            logger.error(f"OpenAI API request exceeded rate limit: {e}")
            return "", error_message

    # 异步的chat方法，用于处理与OpenAI模型的交互
    async def chat(self, messages, max_tokens=500, temperature=0.7):  # , image: str = None
        loop = asyncio.get_event_loop()  # 获取当前的事件循环
        data = {
            'model': self.model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': messages,
            # 'stop': ["Observation:"]
        }
        # if image:
        #     # 如果提供了图像内容，将其加入到消息中
        #     image_message = {
        #         'role': 'user',
        #         'image_url': {
        #             'type':"image_url",
        #              "image_url": {"url": f"data:image/jpeg;base64,{image}",
        #         }
        #     }
        #     messages.append(image_message)
        func = partial(openai.ChatCompletion.create, **data)
        return await loop.run_in_executor(None, func)  # 在执行器中运行func并等待结果


# GPTGenerator35类继承自GPTGenerator，用于GPT-3.5模型
class GPTGenerator35(GPTGenerator):
    def __init__(self):
        self.model = "gpt-3.5-turbo-1106"  # 指定模型为GPT-3.5


# GPTGenerator4类继承自GPTGenerator，用于GPT-4模型
class GPTGenerator4(GPTGenerator):
    def __init__(self):
        self.model = "gpt-4-1106-preview"  # 指定模型为GPT-4


# GPTGenerator4V类继承自GPTGenerator，用于GPT-4 Vision模型
class GPTGenerator4V(GPTGenerator):
    def __init__(self):
        self.model = "gpt-4-vision-preview"  # 指定模型为GPT-4 Vision


