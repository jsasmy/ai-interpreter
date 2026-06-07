import asyncio
import json
import logging
import uuid

import websockets

from config import settings

logger = logging.getLogger(__name__)


class DashScopeTTSService:
    async def synthesize(self, text: str, voice: str = "") -> bytes:
        text = (text or "").strip()
        if not text:
            return b""
        if not settings.DASHSCOPE_API_KEY:
            raise RuntimeError("未配置 DASHSCOPE_API_KEY")

        task_id = uuid.uuid4().hex
        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "X-DashScope-DataInspection": "enable",
        }
        selected_voice = (voice or settings.DASHSCOPE_TTS_VOICE or "longfeifei_v2").strip()

        async with websockets.connect(
            settings.DASHSCOPE_TTS_URL,
            extra_headers=headers,
            ping_interval=20,
        ) as ws:
            await ws.send(json.dumps({
                "header": {
                    "action": "run-task",
                    "task_id": task_id,
                    "streaming": "duplex",
                },
                "payload": {
                    "task_group": "audio",
                    "task": "tts",
                    "function": "SpeechSynthesizer",
                    "model": settings.DASHSCOPE_TTS_MODEL,
                    "parameters": {
                        "text_type": "PlainText",
                        "voice": selected_voice,
                        "format": "mp3",
                        "sample_rate": 22050,
                        "volume": 50,
                        "rate": 1,
                        "pitch": 1,
                    },
                    "input": {},
                },
            }, ensure_ascii=False))

            await self._wait_for_event(ws, task_id, "task-started")
            await ws.send(json.dumps({
                "header": {
                    "action": "continue-task",
                    "task_id": task_id,
                    "streaming": "duplex",
                },
                "payload": {
                    "input": {
                        "text": text,
                    },
                },
            }, ensure_ascii=False))
            await ws.send(json.dumps({
                "header": {
                    "action": "finish-task",
                    "task_id": task_id,
                    "streaming": "duplex",
                },
                "payload": {
                    "input": {},
                },
            }, ensure_ascii=False))

            audio_chunks = []
            while True:
                message = await asyncio.wait_for(ws.recv(), timeout=30)
                if isinstance(message, bytes):
                    audio_chunks.append(message)
                    continue

                event = json.loads(message)
                header = event.get("header", {})
                event_name = header.get("event")
                if event_name == "task-finished":
                    break
                if event_name == "task-failed":
                    raise RuntimeError(header.get("error_message") or "DashScope TTS 合成失败")

            return b"".join(audio_chunks)

    async def _wait_for_event(self, ws, task_id: str, expected_event: str):
        while True:
            message = await asyncio.wait_for(ws.recv(), timeout=15)
            if isinstance(message, bytes):
                continue

            event = json.loads(message)
            header = event.get("header", {})
            event_name = header.get("event")
            if event_name == expected_event and header.get("task_id") == task_id:
                return
            if event_name == "task-failed":
                raise RuntimeError(header.get("error_message") or "DashScope TTS 任务启动失败")


dashscope_tts_service = DashScopeTTSService()
