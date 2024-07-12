import os
import asyncio
from anthropic import AsyncAnthropic
from functools import partial
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import asyncio
import concurrent
from logs import logger


class ClaudeGenerator:

    def __init__(self, model=None):
        self.model = model
        
        self.client = AsyncAnthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY')
        )
        self.pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=multiprocessing.cpu_count() * 2)

    async def request(self, messages: list = None, max_tokens: int = 500, temperature: float = 0.7) -> tuple[str, str]:
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(self.pool, partial(self.chat, messages, max_tokens, temperature))
            return await response, ""
        except Exception as e:
            logger.error(f"Error in ClaudeGenerator.request: {e}")
            return "", str(e)

    async def chat(self, message, max_tokens=1024, temperature=0.7):

        messages = [{"role": "user", "content": "Please follow the instructions"}, {"role": "assistant", "content": message[0].get("content")}, {
            "role": "user", "content": message[1].get("content")}]
        data = {
            'model': self.model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': messages,
        }
        response = await self.client.messages.create(**data)
        return response.content[0].text

