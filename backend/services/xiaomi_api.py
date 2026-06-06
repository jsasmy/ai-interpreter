import httpx
import base64
import json
import re
from typing import Optional, AsyncGenerator
from config import settings
import logging

logger = logging.getLogger(__name__)


LANGUAGE_NAMES = {
    "auto": "the detected source language",
    "en": "English",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
}


CHATTER_PREFIXES = (
    "translation:",
    "translated:",
    "译文：",
    "翻译：",
    "结果：",
    "transcription:",
    "transcript:",
    "i hear:",
    "the transcript is:",
    "转写：",
    "识别结果：",
)


def _first_nonempty_line(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r", "\n").split("\n") if line.strip()]
    if not lines:
        return ""

    for line in lines:
        lowered = line.lower()
        if lowered.startswith(("sure", "ok", "好的", "可以", "以下是", "as an ai")):
            continue
        return line
    return lines[-1]


def _clean_model_text(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    text = _first_nonempty_line(text)
    text = text.strip("` \t\r\n")
    for prefix in CHATTER_PREFIXES:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    text = re.sub(r"^\s*[\-•]\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip("\"'“”‘’")


def _language_name(lang: str) -> str:
    return LANGUAGE_NAMES.get((lang or "").lower(), lang or "the target language")


def _looks_like_non_chinese(text: str) -> bool:
    cjk_count = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    latin_count = sum(1 for char in text if char.isascii() and char.isalpha())
    return latin_count > 0 and cjk_count == 0


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
    def auth_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}"
        }

    @property
    def base_url(self):
        if not self.endpoint:
            return self.api_base.rstrip("/")
        return f"{self.api_base}/{self.endpoint}"

    async def speech_to_text(self, audio_data: bytes, language: str = "en") -> dict:
        try:
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")
            audio_data_url = f"data:audio/wav;base64,{audio_b64}"
            payload = {
                "model": settings.XIAOMI_ASR_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a speech recognition engine. Transcribe the audio only. "
                            "Return plain transcript text, no explanations, no answers, no confidence, no markdown."
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": audio_data_url,
                                    "format": "wav"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Detect the spoken language and transcribe the audio. "
                                    "Output transcript text only."
                                ) if language == "auto" else (
                                    f"Transcribe this {_language_name(language)} audio. Output transcript text only."
                                )
                            }
                        ]
                    }
                ],
                "temperature": 0,
                "max_tokens": 96
            }
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if "text" in result:
                return result
            if "data" in result and isinstance(result["data"], dict) and "text" in result["data"]:
                return {"text": result["data"]["text"], "confidence": result["data"].get("confidence", 0)}
            try:
                text = result["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                text = ""
            text = _clean_model_text(text)
            if text:
                return {"text": text, "confidence": 0}
            return {"error": f"ASR响应中没有可用文本: {response.text[:500]}"}
        except Exception as e:
            logger.error(f"ASR错误: {e}")
            return {"error": str(e)}

    async def check_asr(self) -> dict:
        fake_audio = "data:audio/wav;base64," + base64.b64encode(b"test").decode("utf-8")
        payload = {
            "model": settings.XIAOMI_ASR_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": fake_audio,
                                "format": "wav"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 20
        }
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers
            )
            return {
                "ok": response.status_code < 500,
                "status_code": response.status_code,
                "url": f"{self.base_url}/chat/completions",
                "body": response.text[:1000]
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def translate_text(
        self, 
        text: str, 
        source_lang: str = "zh", 
        target_lang: str = "en",
        context: Optional[str] = None
    ) -> dict:
        source_name = _language_name(source_lang)
        target_name = _language_name(target_lang)
        system_prompt = f"""You are a real-time interpreter, not a chatbot.
Translate the user's {source_name} transcript into {target_name}.
Rules:
1. Output only the translated sentence in {target_name}.
2. Do not answer questions in the transcript. Translate the question instead.
3. Do not explain, summarize, apologize, add labels, or use markdown.
4. Preserve names, numbers, tone, and sentence meaning.
5. Never translate into Spanish unless the target language is Spanish.
6. If the input is noise or not speech, output an empty string."""

        if context:
            system_prompt += f"\nRecent transcript context for disambiguation only: {context}"

        payload = {
            "model": settings.XIAOMI_LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0,
            "max_tokens": min(192, max(32, len(text) * 2))
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            translated = _clean_model_text(result["choices"][0]["message"]["content"])
            if target_lang == "zh" and _looks_like_non_chinese(translated):
                logger.warning("丢弃疑似非中文译文: %r -> %r", text, translated)
                translated = ""
            return {
                "original": text,
                "translated": translated,
                "confidence": 0.95
            }
        except Exception as e:
            logger.error(f"翻译错误: {e}")
            return {"error": str(e)}

    async def health_check(self) -> dict:
        payload = {
            "model": settings.XIAOMI_LLM_MODEL,
            "messages": [
                {"role": "user", "content": "请只回复：ok"}
            ],
            "temperature": 0,
            "max_tokens": 10
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers
            )
            return {
                "ok": response.status_code < 400,
                "status_code": response.status_code,
                "url": f"{self.base_url}/chat/completions",
                "body": response.text[:1000]
            }
        except Exception as e:
            return {
                "ok": False,
                "url": f"{self.base_url}/chat/completions",
                "error": str(e)
            }

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
