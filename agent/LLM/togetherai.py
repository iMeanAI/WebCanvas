import os
import sys
import openai
from openai import AsyncOpenAI
from sanic.log import logger
from agent.Utils import *
import requests
from sanic.log import logger


class TogetherAIGenerator:
    def __init__(self, model=None):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=os.environ.get("TOGETHER_API_KEY"),
            base_url="https://api.together.xyz/v1"
        )

    async def request(self, messages: list = None, max_tokens: int = 500, temperature: float = 0.7
                      ) -> (str, str):
        try:
            openai_response = await self.chat(messages, max_tokens, temperature)
            return openai_response, ""
        except Exception as e:
            logger.error(f"Error in TogetherAIGenerator.request: {e}")
            return "", str(e)

    async def chat(self, messages, max_tokens=512, temperature=0.7):
        data = {
            'model': self.model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': messages,
        }

        response = await self.client.chat.completions.create(**data)
        try:
            message_content = response.choices[0].message.content
            return message_content
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"Invalid response format: {e}")
            return ""
