from typing import List, Dict, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class CorrectionService:
    def __init__(self):
        self.buffer: List[Dict] = []
        self.max_buffer_size = settings.CORRECTION_BUFFER_SIZE
        self.terminology_cache: Dict[str, str] = {}

    def add_to_buffer(self, item: Dict):
        self.buffer.append(item)
        if len(self.buffer) > self.max_buffer_size:
            self.buffer.pop(0)

    def get_buffer_context(self, window_size: int = 3) -> str:
        recent = self.buffer[-window_size:]
        return " ".join([item.get("original", "") for item in recent])

    async def correct(
        self, 
        original: str, 
        translated: str, 
        source_lang: str = "en"
    ) -> Dict:
        if not settings.ENABLE_CORRECTION:
            return {"original": original, "translated": translated, "corrected": False}

        corrected_original = self._apply_terminology(original)
        corrected_translated = self._fix_common_errors(translated, source_lang)

        is_corrected = (
            corrected_original != original or 
            corrected_translated != translated
        )

        result = {
            "original": corrected_original,
            "translated": corrected_translated,
            "corrected": is_corrected
        }

        self.add_to_buffer(result)

        return result

    def _apply_terminology(self, text: str) -> str:
        corrected = text
        for term, replacement in self.terminology_cache.items():
            corrected = corrected.replace(term, replacement)
        return corrected

    def _fix_common_errors(self, text: str, source_lang: str) -> str:
        if source_lang == "en":
            replacements = {
                "。": "。",
                "，": "，",
                "  ": " ",
            }
            for old, new in replacements.items():
                text = text.replace(old, new)

        return text.strip()

    def add_terminology(self, term: str, replacement: str):
        self.terminology_cache[term] = replacement

    def clear_buffer(self):
        self.buffer.clear()


correction_service = CorrectionService()
