import httpx
from typing import Optional
from config import settings
from services.xiaomi_api import xiaomi_client
import logging

logger = logging.getLogger(__name__)


class TranslateService:
    def __init__(self):
        self.use_mock = not settings.XIAOMI_API_KEY

    async def translate(
        self, 
        text: str, 
        source_lang: str = "en", 
        target_lang: str = "zh",
        context: Optional[str] = None
    ) -> dict:
        if self.use_mock:
            return self._mock_translate(text)

        result = await xiaomi_client.translate_text(text, source_lang, target_lang, context)
        if "error" in result:
            logger.warning("小米翻译调用失败，临时使用演示翻译: %s", result["error"])
            return self._mock_translate(text)
        return result

    async def close(self):
        return None

    def _mock_translate(self, text: str) -> dict:
        mock_translations = {
            "Hello, welcome to the conference.": "你好，欢迎参加会议。",
            "Today we will discuss the new features.": "今天我们将讨论新功能。",
            "The implementation looks good.": "实现看起来不错。",
            "Let me show you the demo.": "让我给你展示一下演示。",
            "Any questions about this topic?": "关于这个话题有什么问题吗？"
        }

        translated = mock_translations.get(text, f"[翻译] {text}")

        return {
            "original": text,
            "translated": translated,
            "confidence": 0.95
        }


translate_service = TranslateService()
