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

# future_answer = pool.submit(
#     self.chat, messages, max_tokens, temperature, image)
# 这行代码使用了Python的 `concurrent.futures.ThreadPoolExecutor` 来并行执行任务。具体来说：
#
# 1. **ThreadPoolExecutor**: `pool` 是一个 `ThreadPoolExecutor`
# 实例，它是一种线程池执行器。在这个上下文中，它被用来管理和调度线程。线程池允许我们并行地执行多个任务，这可以提高程序的效率，尤其是在执行多个独立且可能耗时的任务时。
#
# 2. **pool.submit**: `submit` 方法用于将一个函数提交给线程池执行。这个方法立即返回，不会等待函数执行完成。它返回一个 `Future` 对象，该对象代表了异步执行的操作。
#
# 3. **函数及其参数**: 在这个例子中，提交给线程池执行的函数是 `self.chat`，这是 `GPTGenerator` 类的一个方法。随后的参数 `messages, max_tokens, temperature,
# image` 是传递给 `self.chat` 方法的参数。
#
#     - `self.chat`: 这是一个异步方法，用于处理与OpenAI GPT模型的交互。它可能是一个进行网络请求的函数，用于向OpenAI发送数据并接收回复。
#     - `messages`: 这个参数代表要发送给GPT模型的消息列表。
#     - `max_tokens`: 指定生成回复的最大令牌数。
#     - `temperature`: 控制回复的变异性或创造性。
#     - `image`: 如果有，表示要处理的图像数据。
#
# 4. **Future对象（future_answer）**: `future_answer` 是 `pool.submit` 返回的 `Future` 对象。
# 这个对象代表了 `self.chat` 方法的异步执行和其结果。通过这个 `Future` 对象，你可以在未来某个时间点获取 `self.chat` 方法的执行结果，比如通过调用 `future_answer.result()` 方法。
#
# 总的来说，这行代码的目的是异步地在一个线程池中执行 `self.chat` 方法，而不会阻塞当前线程。这允许程序在等待 `self.chat` 的响应时继续执行其他任务。
