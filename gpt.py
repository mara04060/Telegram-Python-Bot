from openai import AsyncOpenAI
import httpx as httpx

import credentials


class ChatGptService:
    client: AsyncOpenAI = None
    message_list: list = None

    def __init__(self, token):
        token = "sk-proj-" + token[:3:-1] if token.startswith('gpt:') else token
        self.client = AsyncOpenAI(
            http_client=httpx.Client(proxy=credentials.PROXY),
            api_key=token)
        self.message_list = []

    async def send_message_list(self) -> str:
        completion = await self.client.chat.completions.create(
            model="gpt-4o",  # gpt-4o,  gpt-4-turbo,    gpt-3.5-turbo,  GPT-4o mini
            messages=self.message_list,
            max_tokens=3000,
            temperature=0.9
        )
        message = completion.choices[0].message
        self.message_list.append(message)
        return message.content or ""

    def set_prompt(self, prompt_text: str) -> None:
        self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})

    async def add_message(self, message_text: str) -> str:
        self.message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()

    async def send_question(self, prompt_text: str, message_text: str) -> str:
        self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})
        self.message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()
