import base64

from openai import AsyncOpenAI


class ChatGptService:
    client: AsyncOpenAI = None
    message_list: list = None

    def __init__(self, token):
        token = "sk-proj-" + token[:3:-1] if token.startswith('gpt:') else token
        self.client = AsyncOpenAI(api_key=token)
        self.message_list = []

    async def send_message_list(self) -> str:
        completion = await self.client.chat.completions.create(
            model="gpt-4o",  # gpt-4o,  gpt-4-turbo,    gpt-3.5-turbo,  GPT-4o mini
            messages=self.message_list,
            max_tokens=3000,
            temperature=0.9
        )
        message = completion.choices[0].message
        self.message_list.append({"role": message.role, "content": message.content})
        return message.content or ""

    async def set_prompt(self, prompt_text: str) -> None:
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

    async def transcribe_audio(self, audio_file_path: str) -> str:
        with open(audio_file_path, "rb") as audio_file:
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text

    async def synthesize_speech(self, text: str, output_file_path: str) -> None:
        response = await self. client.chat.completions.create(
            messages= [{"role": "user","content": text}],
            model="gpt-audio-1.5",
            modalities=["text", "audio"],
            audio={"voice": "alloy", "format": "wav"}
        )
        wav_bytes = base64.b64decode(response.choices[0].message.audio.data)
        with open(output_file_path, "wb") as f:
            f.write(wav_bytes)
