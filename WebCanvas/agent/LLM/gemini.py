import os
import sys
import asyncio
from functools import partial
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from sanic.log import logger
import google.generativeai as genai


class GeminiGenerator:
    def __init__(self, model=None):
        self.model = model
        self.pool = ThreadPoolExecutor(max_workers=os.cpu_count() * 2)

    async def request(self, messages: list = None, max_tokens: int = 500, temperature: float = 0.7) -> (str, str):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(self.pool, partial(self.chat, messages, max_tokens, temperature))
            return response, ""
        except Exception as e:
            logger.error(f"Error in GeminiGenerator.request: {e}")
            return "", str(e)

    def chat(self, messages, max_tokens=500, temperature=0.7):
        chat_history = []
        for message in messages:
            chat_history.append({"role": "user", "parts": [{"text": message.get("content")}]})
            # chat_history.append({"role": "model", "parts": [{"text": message.get("content")}]})
        running_model = genai.GenerativeModel(self.model)
        chat = running_model.start_chat(history=chat_history)
        latest_user_message = messages[-1].get("content")
        response = chat.send_message(latest_user_message, generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature))
        return response.text
