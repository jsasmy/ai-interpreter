from typing import Optional
from config import settings
from services.xiaomi_api import xiaomi_client
import logging

logger = logging.getLogger(__name__)


class ASRService:
    def __init__(self):
        self.use_mock = False

    async def recognize(self, audio_data: bytes, language: str = "en") -> dict:
        if not settings.XIAOMI_API_KEY:
            return {"error": "未配置小米API密钥，无法进行真实语音识别"}

        return await xiaomi_client.speech_to_text(audio_data, language)

    async def close(self):
        return None


asr_service = ASRService()
