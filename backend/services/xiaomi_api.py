import httpx
import base64
import json
from typing import Optional, AsyncGenerator
from config import settings
import logging

logger = logging.getLogger(__name__)


class XiaomiAPIClient:
    def __init__(self):
        self.api_key = settings.XIAOMI_API_KEY
        self.api_base = settings.XIAOMI_API_BASE
        self.endpoint = settings.XIAOMI_API_ENDPOINT
        self.client = httpx.AsyncClient(timeout=60.0)

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    @property
    def base_url(self):
        if not self.endpoint:
            return self.api_base.rstrip("/")
        return f"{self.api_base}/{self.endpoint}"

    async def speech_to_text(self, audio_data: bytes, language: str = "en") -> dict:
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        payload = {
            "model": settings.XIAOMI_ASR_MODEL,
            "audio": audio_b64,
            "language": language,
            "response_format": "json"
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/audio/transcriptions",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ASR错误: {e}")
            return {"error": str(e)}

    async def translate_text(
        self, 
        text: str, 
        source_lang: str = "en", 
        target_lang: str = "zh",
        context: Optional[str] = None
    ) -> dict:
        system_prompt = f"""你是一个专业的同声传译翻译员。
将{source_lang}翻译成{target_lang}。
要求：
1. 翻译准确、自然、流畅
2. 保持原文的语气和风格
3. 专业术语要准确
4. 只返回翻译结果，不要解释"""

        if context:
            system_prompt += f"\n上下文参考：{context}"

        payload = {
            "model": settings.XIAOMI_LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            translated = result["choices"][0]["message"]["content"]
            return {
                "original": text,
                "translated": translated,
                "confidence": 0.95
            }
        except Exception as e:
            logger.error(f"翻译错误: {e}")
            return {"error": str(e)}

    async def translate_stream(
        self, 
        text: str, 
        source_lang: str = "en", 
        target_lang: str = "zh"
    ) -> AsyncGenerator[str, None]:
        system_prompt = f"将以下{source_lang}文本翻译成{target_lang}，只返回翻译结果："

        payload = {
            "model": settings.XIAOMI_LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3,
            "stream": True
        }

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except:
                            pass
        except Exception as e:
            logger.error(f"流式翻译错误: {e}")

    async def text_to_speech(self, text: str, voice: str = "default") -> bytes:
        payload = {
            "model": settings.XIAOMI_TTS_MODEL,
            "input": text,
            "voice": voice,
            "response_format": "mp3"
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/audio/speech",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"TTS错误: {e}")
            return b""

    async def close(self):
        await self.client.aclose()


xiaomi_client = XiaomiAPIClient()
