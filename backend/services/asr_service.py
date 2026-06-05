from typing import Optional
from config import settings
from services.xiaomi_api import xiaomi_client
import logging

logger = logging.getLogger(__name__)


class ASRService:
    def __init__(self):
        self.use_mock = not settings.XIAOMI_API_KEY

    async def recognize(self, audio_data: bytes, language: str = "en") -> dict:
        if self.use_mock:
            return self._mock_recognize(audio_data)

        result = await xiaomi_client.speech_to_text(audio_data, language)
        if "error" in result:
            logger.warning("小米ASR调用失败，临时使用演示字幕: %s", result["error"])
            return self._mock_recognize(audio_data)
        return result

    async def close(self):
        return None

    def _mock_recognize(self, audio_data: bytes) -> dict:
        import random
        import time
        mock_texts = [
            "Hello, welcome to the conference.",
            "Today we will discuss the new features.",
            "The implementation looks good.",
            "Let me show you the demo.",
            "Any questions about this topic?",
            "This is a real-time translation system.",
            "We are using advanced AI models.",
            "The audio quality is very clear.",
            "Let's continue with the next topic.",
            "Thank you for your attention."
        ]
        return {
            "text": random.choice(mock_texts),
            "confidence": random.uniform(0.85, 0.99),
            "timestamp": time.time()
        }


asr_service = ASRService()
