import httpx
from typing import Optional
from config import settings
from services.xiaomi_api import xiaomi_client
import logging

logger = logging.getLogger(__name__)


class TranslateService:
    def __init__(self):
        self.use_mock = False

    async def translate(
        self, 
        text: str, 
        source_lang: str = "en", 
        target_lang: str = "zh",
        context: Optional[str] = None
    ) -> dict:
        if not settings.XIAOMI_API_KEY:
            return {"error": "未配置小米API密钥，无法进行真实翻译"}

        return await xiaomi_client.translate_text(text, source_lang, target_lang, context)

    async def close(self):
        return None


translate_service = TranslateService()
