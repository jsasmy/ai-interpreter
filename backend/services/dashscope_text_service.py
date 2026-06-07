import json
import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


LANGUAGE_NAMES = {
    "auto": "the detected source language",
    "en": "English",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese",
    "it": "Italian",
    "ru": "Russian",
    "ar": "Arabic",
    "yue": "Cantonese",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "hi": "Hindi",
    "el": "Greek",
    "tr": "Turkish",
}


def language_name(lang: str) -> str:
    return LANGUAGE_NAMES.get((lang or "").lower(), lang or "the target language")


class DashScopeTextTranslator:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20.0)

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        }

    async def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
        context: Optional[str] = None,
    ) -> dict:
        if not settings.DASHSCOPE_API_KEY:
            return {"error": "未配置 DASHSCOPE_API_KEY"}

        text = (text or "").strip()
        if not text:
            return {"translated": ""}

        source_name = language_name(source_lang)
        target_name = language_name(target_lang)
        system_prompt = (
            "You are a real-time interpreter. Translate the user's transcript only. "
            f"Source language: {source_name}. Target language: {target_name}. "
            "Output only the translated sentence, with no explanations, labels, markdown, or answers."
        )
        if context:
            system_prompt += f"\nRecent context for disambiguation only: {context}"

        payload = {
            "model": settings.DASHSCOPE_TEXT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0,
            "max_tokens": min(256, max(32, len(text) * 2)),
        }

        try:
            response = await self.client.post(
                f"{settings.DASHSCOPE_COMPATIBLE_BASE_URL.rstrip('/')}/chat/completions",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            result = response.json()
            translated = result["choices"][0]["message"]["content"].strip()
            return {
                "original": text,
                "translated": translated,
                "provider": "dashscope",
                "model": settings.DASHSCOPE_TEXT_MODEL,
            }
        except Exception as exc:
            logger.error("DashScope 兜底翻译失败: %s", exc)
            return {"error": str(exc)}

    async def repair_context_pair(
        self,
        previous_original: str,
        previous_translated: str,
        current_original: str,
        current_translated: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
        context_segments: Optional[list[dict]] = None,
    ) -> dict:
        if not settings.DASHSCOPE_API_KEY:
            return {}

        previous_original = (previous_original or "").strip()
        previous_translated = (previous_translated or "").strip()
        current_original = (current_original or "").strip()
        current_translated = (current_translated or "").strip()
        if not previous_original or not current_original:
            return {}

        source_name = language_name(source_lang)
        target_name = language_name(target_lang)
        system_prompt = (
            "You revise real-time subtitle translations using only neighboring context. "
            f"Source language: {source_name}. Target language: {target_name}. "
            "Keep exactly two subtitle rows: previous and current. "
            "Use the prior context to infer omitted subjects, objects, references, topic terms, and discourse links. "
            "Fix boundary leakage, pronoun/reference ambiguity, inconsistent terminology, and context-dependent wording. "
            "Do not merge the two rows, do not add explanations, and do not change the meaning. "
            "Return strict JSON with keys previous_translated and current_translated only."
        )
        user_payload = {
            "prior_context": [
                {
                    "original": (segment.get("original") or "").strip(),
                    "translated": (segment.get("translated") or "").strip(),
                }
                for segment in (context_segments or [])
                if (segment.get("original") or segment.get("translated"))
            ],
            "previous": {
                "original": previous_original,
                "translated": previous_translated,
            },
            "current": {
                "original": current_original,
                "translated": current_translated,
            },
        }
        payload = {
            "model": settings.DASHSCOPE_REPAIR_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "temperature": 0,
            "max_tokens": min(
                384,
                max(96, (len(previous_original) + len(current_original)) * 2),
            ),
        }

        try:
            response = await self.client.post(
                f"{settings.DASHSCOPE_COMPATIBLE_BASE_URL.rstrip('/')}/chat/completions",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.strip("`").strip()
                if content.lower().startswith("json"):
                    content = content[4:].strip()
            repaired = json.loads(content)
            return {
                "previous_translated": str(repaired.get("previous_translated") or "").strip(),
                "current_translated": str(repaired.get("current_translated") or "").strip(),
                "provider": "dashscope",
                "model": settings.DASHSCOPE_REPAIR_MODEL,
            }
        except Exception as exc:
            logger.warning("DashScope contextual repair skipped: %s", exc)
            return {}

    async def repair_context_window(
        self,
        segments: list[dict],
        source_lang: str = "auto",
        target_lang: str = "zh",
    ) -> dict:
        if not settings.DASHSCOPE_API_KEY:
            return {}

        clean_segments = []
        for segment in segments:
            segment_id = segment.get("segment_id") or segment.get("item_id") or ""
            original = (segment.get("original") or "").strip()
            translated = (segment.get("translated") or "").strip()
            if not segment_id or not original or not translated:
                continue
            clean_segments.append({
                "segment_id": segment_id,
                "original": original,
                "translated": translated,
            })

        if not clean_segments:
            return {}

        source_name = language_name(source_lang)
        target_name = language_name(target_lang)
        target_segment_id = clean_segments[-1]["segment_id"]
        system_prompt = (
            "You revise a rolling window of real-time subtitle translations. "
            f"Source language: {source_name}. Target language: {target_name}. "
            "Use locked context rows to preserve topic continuity, references, terminology, tense, and discourse links. "
            "Only the final row in the window is editable; all previous rows are locked context and must not be changed. "
            f"The only editable segment_id is {target_segment_id}. "
            "Keep each subtitle row separate and in the same order. "
            "Do not merge rows, add explanations, answer the speaker, or invent missing content. "
            "Preserve the existing final translation unless there is a clear mistranslation, missing reference, wrong term, or broken sentence boundary. "
            "If the final row is already correct and natural, return an empty replacements array. "
            "Return strict JSON only: {\"replacements\":[{\"segment_id\":\"...\",\"translated\":\"...\"}]}."
        )
        payload = {
            "model": settings.DASHSCOPE_REPAIR_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"segments": clean_segments}, ensure_ascii=False)},
            ],
            "temperature": 0,
            "max_tokens": min(
                384,
                max(96, sum(len(segment["original"]) for segment in clean_segments) * 2),
            ),
        }

        try:
            response = await self.client.post(
                f"{settings.DASHSCOPE_COMPATIBLE_BASE_URL.rstrip('/')}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.strip("`").strip()
                if content.lower().startswith("json"):
                    content = content[4:].strip()
            repaired = json.loads(content)
            replacements = []
            for replacement in repaired.get("replacements") or []:
                segment_id = str(replacement.get("segment_id") or "").strip()
                translated = str(replacement.get("translated") or "").strip()
                if segment_id == target_segment_id and translated:
                    replacements.append({
                        "segment_id": segment_id,
                        "translated": translated,
                    })
            return {
                "replacements": replacements,
                "provider": "dashscope",
                "model": settings.DASHSCOPE_REPAIR_MODEL,
                "status": "corrected" if replacements else "checked",
            }
        except Exception as exc:
            logger.warning("DashScope contextual window repair skipped: %s", exc)
            return {"status": "failed", "error": str(exc)}

    async def close(self):
        await self.client.aclose()


dashscope_text_translator = DashScopeTextTranslator()
