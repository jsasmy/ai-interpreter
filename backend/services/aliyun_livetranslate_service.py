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
from services.dashscope_text_service import dashscope_text_translator

logger = logging.getLogger(__name__)

debug_logger = logging.getLogger("aliyun_livetranslate")
if settings.DEBUG_REALTIME_EVENTS and not debug_logger.handlers:
    handler = logging.FileHandler("aliyun_livetranslate.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    debug_logger.addHandler(handler)
    debug_logger.setLevel(logging.INFO)
    debug_logger.propagate = False
elif not settings.DEBUG_REALTIME_EVENTS:
    debug_logger.addHandler(logging.NullHandler())
    debug_logger.setLevel(logging.WARNING)
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


def normalize_lang(lang: str, *, is_target: bool = False) -> str:
    normalized = LANGUAGE_MAP.get((lang or "auto").lower(), "auto")
    if is_target and normalized == "auto":
        return "zh"
    return normalized


class AliyunLiveTranslateSession:
    def __init__(
        self,
        send_to_client: Callable[[dict], Awaitable[None]],
        *,
        model: str | None = None,
        source_name: str = "livetranslate",
        silence_duration_ms: int = 430,
    ):
        self.send_to_client = send_to_client
        self.model = model or settings.DASHSCOPE_LIVETRANSLATE_MODEL
        self.source_name = source_name
        self.silence_duration_ms = silence_duration_ms
        self.ws = None
        self.receiver_task: Optional[asyncio.Task] = None
        self.source_lang = "auto"
        self.target_lang = "zh"
        self.latest_original = ""
        self.latest_translated = ""
        self.original_by_item: dict[str, str] = {}
        self.translated_by_item: dict[str, str] = {}
        self.completed_items: set[str] = set()
        self.completed_segments: list[dict] = []
        self.repair_tasks: set[asyncio.Task] = set()
        self.latest_repair_task: Optional[asyncio.Task] = None
        self.synthetic_item_counter = 0
        self.started = False

    @property
    def url(self) -> str:
        query = urlencode({"model": self.model})
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
            "connected model=%s stream=%s source=%s target=%s",
            self.model,
            self.source_name,
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

        pcm_data = audio_data
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
        for task in list(self.repair_tasks):
            task.cancel()
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
                    "threshold": 0.10,
                    "prefix_padding_ms": 380,
                    "silence_duration_ms": self.silence_duration_ms,
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
        if settings.DEBUG_REALTIME_EVENTS:
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
            subtitle = await self._send_subtitle("final", response_item_id)
            if subtitle:
                self._schedule_contextual_repair(subtitle)
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
            return None
        if message_type == "final" and not item_id:
            self.synthetic_item_counter += 1
            item_id = f"synthetic_{self.synthetic_item_counter}"
        debug_logger.info(
            "send_subtitle type=%s item=%s original_len=%s translated_len=%s translated=%r",
            message_type,
            item_id,
            len(original or ""),
            len(translated or ""),
            translated[:80],
        )
        content = {
            "segment_id": item_id,
            "item_id": item_id,
            "original": original,
            "translated": translated,
            "timestamp": datetime.now().isoformat(),
            "source": self.source_name,
            "model": self.model,
        }
        await self.send_to_client({
            "type": "subtitle_delta" if message_type == "partial" else "subtitle",
            "content": content,
        })
        return content

    def _schedule_contextual_repair(self, current: dict):
        self.completed_segments.append(current)
        max_history = max(24, settings.CONTEXTUAL_REPAIR_WINDOW_SIZE * 3)
        if len(self.completed_segments) > max_history:
            self.completed_segments = self.completed_segments[-max_history:]

        if (
            not settings.ENABLE_CONTEXTUAL_REPAIR
            or self.source_name != "livetranslate"
        ):
            asyncio.create_task(self._send_repair_status(current, "skipped", "repair_disabled_or_non_primary_stream"))
            return

        window = self._build_repair_window()
        if not window:
            asyncio.create_task(self._send_repair_status(current, "skipped", "no_repair_window"))
            return

        asyncio.create_task(self._send_repair_status(current, "checking"))
        task = asyncio.create_task(self._repair_context_window(window))
        self.latest_repair_task = task
        self.repair_tasks.add(task)
        task.add_done_callback(self.repair_tasks.discard)

    def _build_repair_window(self) -> list[dict]:
        window: list[dict] = []
        total_chars = 0
        max_rows = max(2, settings.CONTEXTUAL_REPAIR_WINDOW_SIZE)

        for segment in reversed(self.completed_segments):
            original = (segment.get("original") or "").strip()
            translated = (segment.get("translated") or "").strip()
            if not original or not translated:
                continue
            next_total = total_chars + len(original)
            if window and next_total > settings.CONTEXTUAL_REPAIR_MAX_CHARS:
                break
            window.append(segment.copy())
            total_chars = next_total
            if len(window) >= max_rows:
                break

        window.reverse()
        return window

    async def _repair_context_window(self, window: list[dict]):
        target_segment_id = ""
        if window:
            target_segment_id = window[-1].get("segment_id") or window[-1].get("item_id") or ""
        try:
            result = await dashscope_text_translator.repair_context_window(
                window,
                self.source_lang,
                self.target_lang,
            )
        except asyncio.CancelledError:
            return
        replacements = []
        segment_by_id = {
            (segment.get("segment_id") or segment.get("item_id")): segment
            for segment in self.completed_segments
        }
        target_segment = segment_by_id.get(target_segment_id)
        if result.get("status") == "failed":
            if target_segment:
                await self._send_repair_status(target_segment, "failed", result.get("error", "repair_failed"))
            return
        for replacement in result.get("replacements") or []:
            segment_id = replacement.get("segment_id") or replacement.get("item_id")
            if segment_id != target_segment_id:
                continue
            translated = replacement.get("translated", "")
            segment = segment_by_id.get(segment_id)
            if not segment or not translated:
                continue
            if self._same_text(translated, segment.get("translated", "")):
                continue
            replacements.append({
                "segment_id": segment.get("segment_id"),
                "item_id": segment.get("item_id"),
                "original": segment.get("original", ""),
                "translated": translated,
            })
            segment["translated"] = translated

        if replacements:
            await self.send_to_client({
                "type": "correction",
                "content": {
                    "source": "contextual_window_repair",
                    "status": "corrected",
                    "replacements": replacements,
                    "timestamp": datetime.now().isoformat(),
                },
            })
        elif target_segment:
            await self._send_repair_status(target_segment, "checked")

    async def _send_repair_status(self, segment: dict, status: str, reason: str = ""):
        segment_id = segment.get("segment_id") or segment.get("item_id")
        if not segment_id:
            return
        await self.send_to_client({
            "type": "correction_status",
            "content": {
                "segment_id": segment_id,
                "item_id": segment_id,
                "status": status,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            },
        })

    def _can_repair_pair(self, previous: dict, current: dict) -> bool:
        previous_original = previous.get("original", "")
        current_original = current.get("original", "")
        previous_translated = previous.get("translated", "")
        current_translated = current.get("translated", "")
        total_chars = len(previous_original) + len(current_original)
        return (
            bool(previous_original.strip())
            and bool(current_original.strip())
            and bool(previous_translated.strip())
            and bool(current_translated.strip())
            and total_chars <= settings.CONTEXTUAL_REPAIR_MAX_CHARS
        )
        if (
            not previous_translated
            or not current_translated
            or total_chars > settings.CONTEXTUAL_REPAIR_MAX_CHARS
        ):
            return False

        current_start = current_original.strip().lower()
        previous_end = previous_original.strip()[-1:] if previous_original.strip() else ""
        link_prefixes = (
            "and ", "but ", "so ", "because ", "which ", "that ", "then ",
            "therefore ", "however ", "it ", "they ", "this ", "these ",
            "those ", "he ", "she ", "we ", "you ", "also ", "as ", "when ",
            "while ", "if ", "where ", "who ",
            "这", "那", "而", "但", "所以", "因为", "然后", "并且", "它", "他们",
            "他", "她", "我们", "你们", "也", "还", "如果", "当", "其中",
        )
        terminal_chars = ".?!;。！？；"
        if previous_end and previous_end not in terminal_chars:
            return True
        if any(current_start.startswith(prefix) for prefix in link_prefixes):
            return True
        if current_start[:1].islower():
            return True
        return len(current_original.strip()) <= 48

    async def _repair_context_pair(self, previous: dict, current: dict, context: list[dict] | None = None):
        result = await dashscope_text_translator.repair_context_pair(
            previous.get("original", ""),
            previous.get("translated", ""),
            current.get("original", ""),
            current.get("translated", ""),
            self.source_lang,
            self.target_lang,
            context_segments=context or [],
        )
        previous_fixed = result.get("previous_translated", "")
        current_fixed = result.get("current_translated", "")
        replacements = []
        if previous_fixed and not self._same_text(previous_fixed, previous.get("translated", "")):
            replacements.append({
                "segment_id": previous.get("segment_id"),
                "item_id": previous.get("item_id"),
                "original": previous.get("original", ""),
                "translated": previous_fixed,
            })
            previous["translated"] = previous_fixed
        if current_fixed and not self._same_text(current_fixed, current.get("translated", "")):
            replacements.append({
                "segment_id": current.get("segment_id"),
                "item_id": current.get("item_id"),
                "original": current.get("original", ""),
                "translated": current_fixed,
            })
            current["translated"] = current_fixed
        if replacements:
            await self.send_to_client({
                "type": "correction",
                "content": {
                    "source": "contextual_repair",
                    "replacements": replacements,
                    "timestamp": datetime.now().isoformat(),
                },
            })

    @staticmethod
    def _same_text(left: str, right: str) -> bool:
        return " ".join((left or "").split()) == " ".join((right or "").split())

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
