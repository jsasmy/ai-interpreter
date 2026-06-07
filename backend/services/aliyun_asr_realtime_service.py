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
from services.aliyun_livetranslate_service import normalize_lang

logger = logging.getLogger(__name__)


class AliyunAsrRealtimeSession:
    def __init__(self, send_to_client: Callable[[dict], Awaitable[None]]):
        self.send_to_client = send_to_client
        self.ws = None
        self.receiver_task: Optional[asyncio.Task] = None
        self.source_lang = "auto"
        self.completed_transcripts: set[str] = set()

    @property
    def url(self) -> str:
        query = urlencode({"model": settings.DASHSCOPE_ASR_MODEL})
        return f"{settings.DASHSCOPE_REALTIME_URL}?{query}"

    async def connect(self, source_lang: str = "auto"):
        if not settings.DASHSCOPE_API_KEY:
            raise RuntimeError("未配置 DASHSCOPE_API_KEY")

        self.source_lang = normalize_lang(source_lang)
        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "X-DashScope-DataInspection": "enable",
        }
        self.ws = await websockets.connect(self.url, extra_headers=headers, ping_interval=20)
        self.receiver_task = asyncio.create_task(self._receive_loop())
        await self._send_session_update()

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
        if self.ws:
            try:
                await self.ws.close()
            finally:
                self.ws = None

    async def _send_session_update(self):
        transcription = {"model": settings.DASHSCOPE_ASR_MODEL}
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
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.10,
                    "prefix_padding_ms": 380,
                    "silence_duration_ms": 430,
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
            logger.error("阿里 ASR 旁路连接错误: %s", exc)
            await self.send_to_client({
                "type": "asr_error",
                "content": {"message": f"阿里 ASR 旁路连接错误: {exc}"},
            })

    async def _handle_server_event(self, event: dict):
        event_type = event.get("type", "")
        item_id = event.get("item_id") or self._extract_response_done_item_id(event)

        transcript = ""
        if event_type == "conversation.item.input_audio_transcription.completed":
            transcript = self._extract_text(event, ("transcript", "text", "content"))
        elif event_type == "response.done":
            transcript = self._extract_response_done_text(event)

        transcript = (transcript or "").strip()
        if not transcript:
            return

        dedupe_key = transcript.lower()
        if dedupe_key in self.completed_transcripts:
            return
        self.completed_transcripts.add(dedupe_key)
        if len(self.completed_transcripts) > 100:
            self.completed_transcripts = set(list(self.completed_transcripts)[-50:])

        await self.send_to_client({
            "type": "asr_final",
            "content": {
                "item_id": item_id,
                "original": transcript,
                "translated": "",
                "timestamp": datetime.now().isoformat(),
                "source": "asr_fallback",
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
