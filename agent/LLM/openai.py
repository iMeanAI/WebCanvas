from typing import Any
import openai
import asyncio
from functools import partial
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from sanic.log import logger
from agent.Utils import *
from .token_cal import truncate_messages_based_on_estimated_tokens


class GPTGenerator:
    def __init__(self, model=None):
        self.model = model

    async def request(self, messages: list = None, max_tokens: int = 500, temperature: float = 0.7
                      ) -> (str, str):
        try:
            if "gpt-3.5" in self.model:
                messages = truncate_messages_based_on_estimated_tokens(messages, max_tokens=16385)
            cpu_count = multiprocessing.cpu_count()
            with ThreadPoolExecutor(max_workers=cpu_count * 2) as pool:
                future_answer = pool.submit(
                    self.chat, messages, max_tokens, temperature)
                future_answer_result = await future_answer.result()
                choice = future_answer_result.choices[0]  # 获取第一个选项
                # 检查生成结束的原因
                if choice.finish_reason == 'length':
                    logger.warning("Response may be truncated due to length. Be cautious when parsing JSON.")
                # openai_response = choice.message['content']
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
        # Check if response_format is defined and add it to the data if so
        if hasattr(self, 'response_format'):
            data['response_format'] = self.response_format

        func = partial(openai.ChatCompletion.create, **data)
        return await loop.run_in_executor(None, func)


class JSONModeMixin(GPTGenerator):
    """
    A mixin to add JSON mode support to GPTGenerator classes.
    """

    def __init__(self, model=None):
        super().__init__(model=model)  # Ensure initialization from base class
        self.response_format = {"type": "json_object"}  # Set response format to JSON object

    @staticmethod
    def prepare_messages_for_json_mode(messages):
        # Ensure there's a system message instructing the model to generate JSON
        if not any("json" in message.get('content', '').lower() for message in messages):
            messages.insert(0, {"role": "system", "content": "You are a helpful assistant designed to output json."})
        return messages

    async def request(self, messages: list = None, max_tokens: int = 500, temperature: float = 0.7) -> (str, str):
        messages = self.prepare_messages_for_json_mode(messages)  # Prepare messages for JSON mode
        return await super().request(messages, max_tokens, temperature)


# Example subclass with JSON mode support
class GPTGenerator35WithJSON(JSONModeMixin):
    def __init__(self, model=None):
        super().__init__(model=model if model is not None else "gpt-3.5-turbo")


class GPTGenerator4WithJSON(JSONModeMixin):
    def __init__(self, model=None):
        super().__init__(model=model if model is not None else "gpt-4-turbo")


class GPTGeneratorWithJSON(JSONModeMixin):
    def __init__(self, model=None):
        super().__init__(model=model if model is not None else "gpt-4-turbo")


# Subclass without JSON mode
class GPTGenerator35(GPTGenerator):
    def __init__(self, model=None):
        super().__init__(model=model if model is not None else "gpt-3.5-turbo")


class GPTGenerator4(GPTGenerator):
    def __init__(self, model=None):
        super().__init__(model=model if model is not None else "gpt-4-turbo")


class GPTGenerator4V(GPTGenerator):
    def __init__(self, model=None):
        super().__init__(model=model if model is not None else "gpt-4-turbo")
