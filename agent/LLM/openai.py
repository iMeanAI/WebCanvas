import os
import sys
import openai
import asyncio
from functools import partial
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from sanic.log import logger
from agent.Utils import *
from .token_cal import truncate_messages_based_on_estimated_tokens
from .token_calculation import calculation_of_token, save_token_count_to_file


class GPTGenerator:
    def __init__(self, model=None):
        self.model = model
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def request(self, messages: list = None, max_tokens: int = 500, temperature: float = 0.7) -> (str, str):
        try:
            if "gpt-3.5" in self.model:
                messages = truncate_messages_based_on_estimated_tokens(messages, max_tokens=16385)
            if "o1" in self.model:
                messages = [
                    {**msg, "role": "user"} if msg["role"] == "system" else msg
                    for msg in messages
                ]
            cpu_count = multiprocessing.cpu_count()
            with ThreadPoolExecutor(max_workers=cpu_count * 2) as pool:
                if "o1" in self.model:
                    future_answer = pool.submit(self.chat, messages)
                else:
                    future_answer = pool.submit(self.chat, messages, max_tokens, temperature)
                future_answer_result = await future_answer.result()
                choice = future_answer_result.choices[0]
                if choice.finish_reason == 'length':
                    logger.warning("Response may be truncated due to length. Be cautious when parsing JSON.")
                openai_response = choice.message.content
                # output_token_count = future_answer_result.usage.completion_tokens
                # input_token_count = future_answer_result.usage.prompt_tokens
                return openai_response, ""
        except Exception as e:
            logger.error(f"Error in GPTGenerator.request: {e}")
            return "", str(e)

    async def chat(self, messages, max_tokens=500, temperature=0.7):
        loop = asyncio.get_event_loop()
        if "o1" in self.model:
            data = {
                'model': self.model,
                'messages': messages,
            }
        else:
            data = {
                'model': self.model,
                'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': messages,
        }
        if hasattr(self, 'response_format'):
            data['response_format'] = self.response_format

        func = partial(self.client.chat.completions.create, **data)
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


class GPTGeneratorWithJSON(JSONModeMixin):
    def __init__(self, model=None):
        super().__init__(model=model if model is not None else "gpt-4-turbo")
