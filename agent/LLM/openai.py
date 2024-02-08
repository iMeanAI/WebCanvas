from typing import Any
import openai
import asyncio
from functools import partial
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from sanic.log import logger
from agent.Utils import *


class GPTGenerator:
    def __init__(self):
        self.model = ""

    async def request(self, messages: list = None, max_tokens: int = 500, temperature: float = 0.7
                      ) -> (str, str):
        try:
            cpu_count = multiprocessing.cpu_count()
            with ThreadPoolExecutor(max_workers=cpu_count * 2) as pool:
                future_answer = pool.submit(
                    self.chat, messages, max_tokens, temperature)
                future_answer_result = await future_answer.result()
                openai_response = list(future_answer_result.choices)[
                    0].to_dict()['message']['content']
                pool.shutdown()
                return openai_response, ""
        except openai.error.APIError as e:
            # Handle API error here, e.g. retry or log
            logger.error(f"OpenAI API returned an API Error: {e}")
            error_message = f"OpenAI API returned an API Error: {e}"
            OpenAI_error_flag = True
            return "", error_message
        except openai.error.APIConnectionError as e:
            # Handle connection error here
            error_message = f"Failed to connect to OpenAI API: {e}"
            OpenAI_error_flag = True
            logger.error(f"Failed to connect to OpenAI API: {e}")
            return "", error_message
        except openai.error.RateLimitError as e:
            # Handle rate limit error (we recommend using exponential backoff)
            OpenAI_error_flag = True
            error_message = f"OpenAI API request exceeded rate limit: {e}"
            logger.error(f"OpenAI API request exceeded rate limit: {e}")
            return "", error_message

    async def chat(self, messages, max_tokens=500, temperature=0.7):
        loop = asyncio.get_event_loop()
        data = {
            'model': self.model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': messages,
            # 'stop': ["Observation:"]
        }
        func = partial(openai.ChatCompletion.create, **data)
        return await loop.run_in_executor(None, func)


class GPTGenerator35(GPTGenerator):
    def __init__(self):
        self.model = "gpt-3.5-turbo-1106"


class GPTGenerator4(GPTGenerator):
    def __init__(self):
        self.model = "gpt-4-turbo-preview"


class GPTGenerator4V(GPTGenerator):
    def __init__(self):
        self.model = "gpt-4-vision-preview"  # 指定模型为GPT-4 Vision