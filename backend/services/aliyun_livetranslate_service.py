import asyncio
import base64
import json
import logging
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Optional
from urllib.parse import urlencode

import websockets

from config import settings

logger = logging.getLogger(__name__)

debug_logger = logging.getLogger("aliyun_livetranslate")
if not debug_logger.handlers:
    handler = logging.FileHandler("aliyun_livetranslate.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    debug_logger.addHandler(handler)
    debug_logger.setLevel(logging.INFO)
    debug_logger.propagate = False


LANGUAGE_MAP = {
    "auto": "auto",
    "zh": "zh",
    "en": "en",
    "ja": "ja",
    "ko": "ko",
    "fr": "fr",
    "de": "de",
    "es": "es",
    "pt": "pt",
    "it": "it",
    "ru": "ru",
    "ar": "ar",
    "yue": "yue",
    "vi": "vi",
    "th": "th",
    "id": "id",
    "hi": "hi",
    "el": "el",
    "tr": "tr",
}


def wav_to_pcm_bytes(audio_data: bytes) -> bytes:
    if audio_data[:4] != b"RIFF" or audio_data[8:12] != b"WAVE":
        return audio_data

    offset = 12
    while offset + 8 <= len(audio_data):
        chunk_id = audio_data[offset:offset + 4]
        chunk_size = int.from_bytes(audio_data[offset + 4:offset + 8], "little")
        data_start = offset + 8
        data_end = data_start + chunk_size
        if chunk_id == b"data":
            return audio_data[data_start:data_end]
        offset = data_end + (chunk_size % 2)
    return audio_data


def normalize_lang(lang: str, *, is_target: bool = False) -> str:
    normalized = LANGUAGE_MAP.get((lang or "auto").lower(), "auto")
    if is_target and normalized == "auto":
        return "zh"
    return normalized


class AliyunLiveTranslateSession:
    def __init__(self, send_to_client: Callable[[dict], Awaitable[None]]):
        self.send_to_client = send_to_client
        self.ws = None
        self.receiver_task: Optional[asyncio.Task] = None
        self.source_lang = "auto"
        self.target_lang = "zh"
        self.latest_original = ""
        self.latest_translated = ""
        self.original_by_item: dict[str, str] = {}
        self.translated_by_item: dict[str, str] = {}
        self.completed_items: set[str] = set()
        self.started = False

    @property
    def url(self) -> str:
        query = urlencode({"model": settings.DASHSCOPE_LIVETRANSLATE_MODEL})
        return f"{settings.DASHSCOPE_REALTIME_URL}?{query}"

    async def connect(self, source_lang: str = "auto", target_lang: str = "zh"):
        if not settings.DASHSCOPE_API_KEY:
            raise RuntimeError("未配置 DASHSCOPE_API_KEY")

        self.source_lang = normalize_lang(source_lang)
        self.target_lang = normalize_lang(target_lang, is_target=True)
        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "X-DashScope-DataInspection": "enable",
        }
        self.ws = await websockets.connect(self.url, extra_headers=headers, ping_interval=20)
        self.receiver_task = asyncio.create_task(self._receive_loop())
        await self._send_session_update()
        debug_logger.info(
            "connected model=%s source=%s target=%s",
            settings.DASHSCOPE_LIVETRANSLATE_MODEL,
            self.source_lang,
            self.target_lang,
        )
        self.started = True

    async def update_settings(self, source_lang: str, target_lang: str):
        next_source_lang = normalize_lang(source_lang)
        next_target_lang = normalize_lang(target_lang, is_target=True)
        if next_source_lang == self.source_lang and next_target_lang == self.target_lang:
            return

        self.source_lang = next_source_lang
        self.target_lang = next_target_lang
        logger.warning("阿里同传会话已启动，语言设置变更将在下次重新连接后生效")

    async def send_audio(self, audio_data: bytes):
        if not self.ws:
            return

        pcm_data = wav_to_pcm_bytes(audio_data)
        if not pcm_data:
            return

        event = {
            "event_id": f"event_{uuid.uuid4().hex}",
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(pcm_data).decode("ascii"),
        }
        await self.ws.send(json.dumps(event, ensure_ascii=False))

    async def close(self):
        if self.receiver_task:
            self.receiver_task.cancel()
            try:
                await self.receiver_task
            except asyncio.CancelledError:
                pass
        if self.ws:
            try:
                await self.ws.close()
            finally:
                self.ws = None

    async def _send_session_update(self):
        transcription = {
            "model": settings.DASHSCOPE_ASR_MODEL,
        }
        if self.source_lang != "auto":
            transcription["language"] = self.source_lang

        event = {
            "event_id": f"event_{uuid.uuid4().hex}",
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "input_audio_format": "pcm",
                "sample_rate": 16000,
                "input_audio_transcription": transcription,
                "translation": {
                    "language": self.target_lang,
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.12,
                    "prefix_padding_ms": 420,
                    "silence_duration_ms": 520,
                },
            },
        }
        await self.ws.send(json.dumps(event, ensure_ascii=False))

    async def _receive_loop(self):
        try:
            async for raw_message in self.ws:
                await self._handle_server_event(json.loads(raw_message))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("阿里同传连接错误: %s", exc)
            await self.send_to_client({
                "type": "error",
                "content": {"message": f"阿里同传连接错误: {exc}"},
            })

    async def _handle_server_event(self, event: dict):
        event_type = event.get("type", "")
        debug_logger.info("server_event type=%s keys=%s", event_type, ",".join(event.keys()))
        if event_type == "error":
            error = event.get("error") or {}
            await self.send_to_client({
                "type": "error",
                "content": {
                    "message": error.get("message") or event.get("message") or json.dumps(event, ensure_ascii=False)
                },
            })
            return

        item_id = event.get("item_id") or ""

        if event_type == "conversation.item.input_audio_transcription.text":
            transcript = self._extract_text(event, ("text", "stash", "transcript", "content"))
            if transcript and item_id:
                self.original_by_item[item_id] = transcript
            return

        if event_type == "conversation.item.input_audio_transcription.completed":
            transcript = self._extract_text(event, ("transcript", "text", "content"))
            if transcript:
                self.latest_original = transcript
                if item_id:
                    self.original_by_item[item_id] = transcript
            return

        translated = ""
        if event_type == "response.text.text":
            translated = self._extract_text(event, ("text", "content"))
            if translated:
                previous = self.translated_by_item.get(item_id, "")
                if translated.startswith(previous):
                    current = translated
                elif previous.endswith(translated):
                    current = previous
                else:
                    current = previous + translated
                stash = event.get("stash") or ""
                self.latest_translated = current + stash
                if item_id:
                    self.translated_by_item[item_id] = current
                await self._send_subtitle("partial", item_id)
            return

        if event_type == "response.text.done":
            translated = self._extract_text(event, ("text", "transcript", "content"))
            debug_logger.info(
                "response_text_done item=%s len=%s text=%r",
                item_id,
                len(translated or ""),
                (translated or "")[:80],
            )
            if translated:
                self.latest_translated = translated
                if item_id:
                    self.translated_by_item[item_id] = translated
            return

        if event_type == "response.done":
            response_item_id = self._extract_response_done_item_id(event) or item_id
            if response_item_id and response_item_id in self.completed_items:
                debug_logger.info("skip_duplicate_response_done item=%s", response_item_id)
                return

            translated = (
                self._extract_response_done_text(event)
                or self.translated_by_item.get(response_item_id, "")
                or self.latest_translated
            )
            debug_logger.info(
                "response_done item=%s len=%s text=%r",
                response_item_id,
                len(translated or ""),
                (translated or "")[:80],
            )
            if translated:
                self.latest_translated = translated
                if response_item_id:
                    self.translated_by_item[response_item_id] = translated
            await self._send_subtitle("final", response_item_id)
            if response_item_id:
                self.completed_items.add(response_item_id)
                self.original_by_item.pop(response_item_id, None)
                self.translated_by_item.pop(response_item_id, None)
                if len(self.completed_items) > 100:
                    self.completed_items = set(list(self.completed_items)[-50:])
            self.latest_original = ""
            self.latest_translated = ""

    async def _send_subtitle(self, message_type: str, item_id: str = ""):
        translated = self.latest_translated
        original = self.original_by_item.get(item_id) or self.latest_original
        if not original and self.original_by_item:
            original = next(reversed(self.original_by_item.values()), "")
        if not translated:
            debug_logger.info(
                "skip_subtitle type=%s item=%s original_len=%s translated_len=0",
                message_type,
                item_id,
                len(original or ""),
            )
            return
        debug_logger.info(
            "send_subtitle type=%s item=%s original_len=%s translated_len=%s translated=%r",
            message_type,
            item_id,
            len(original or ""),
            len(translated or ""),
            translated[:80],
        )
        await self.send_to_client({
            "type": message_type,
            "content": {
                "original": original,
                "translated": translated,
                "timestamp": datetime.now().isoformat(),
            },
        })

    @staticmethod
    def _extract_text(event: dict, keys: tuple[str, ...]) -> str:
        for key in keys:
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    @staticmethod
    def _extract_response_done_text(event: dict) -> str:
        response = event.get("response") or {}
        for item in response.get("output") or []:
            for content in item.get("content") or []:
                for key in ("text", "transcript"):
                    value = content.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
        return ""

    @staticmethod
    def _extract_response_done_item_id(event: dict) -> str:
        response = event.get("response") or {}
        for item in response.get("output") or []:
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                return item_id
        return ""
