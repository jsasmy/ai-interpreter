from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional
import json
import asyncio
import logging
from collections import deque
from time import perf_counter
from datetime import datetime

from services.asr_service import asr_service
from services.translate_service import translate_service
from services.correction_service import correction_service
from services.aliyun_asr_realtime_service import AliyunAsrRealtimeSession
from services.aliyun_livetranslate_service import AliyunLiveTranslateSession
from services.dashscope_text_service import dashscope_text_translator
from services.xiaomi_api import xiaomi_client
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def detect_text_language(text: str) -> str:
    cjk_count = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    ascii_letter_count = sum(1 for char in text if char.isascii() and char.isalpha())
    if cjk_count >= max(2, ascii_letter_count // 3):
        return "zh"
    return "en"


def resolve_translation_direction(original_text: str, source_lang: str, target_lang: str) -> tuple[str, str]:
    detected_source = detect_text_language(original_text) if source_lang == "auto" else source_lang
    if target_lang == "auto" or target_lang == detected_source:
        resolved_target = "en" if detected_source == "zh" else "zh"
    else:
        resolved_target = target_lang
    return detected_source, resolved_target


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_settings: Dict[WebSocket, Dict] = {}
        self.audio_locks: Dict[WebSocket, asyncio.Lock] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_settings[websocket] = {
            "source_lang": settings.SOURCE_LANG,
            "target_lang": settings.TARGET_LANG,
            "enable_correction": settings.ENABLE_CORRECTION,
            "enable_tts": False
        }
        self.audio_locks[websocket] = asyncio.Lock()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_settings:
            del self.connection_settings[websocket]
        if websocket in self.audio_locks:
            del self.audio_locks[websocket]

    def get_settings(self, websocket: WebSocket) -> Dict:
        return self.connection_settings.get(websocket, {})

    def update_settings(self, websocket: WebSocket, new_settings: Dict):
        if websocket in self.connection_settings:
            normalized = {
                "source_lang": new_settings.get("source_lang", new_settings.get("sourceLang")),
                "target_lang": new_settings.get("target_lang", new_settings.get("targetLang")),
                "enable_correction": new_settings.get("enable_correction", new_settings.get("enableCorrection")),
                "enable_tts": new_settings.get("enable_tts", new_settings.get("enableTTS")),
            }
            self.connection_settings[websocket].update(
                {key: value for key, value in normalized.items() if value is not None}
            )

    def get_audio_lock(self, websocket: WebSocket) -> asyncio.Lock:
        return self.audio_locks.setdefault(websocket, asyncio.Lock())


manager = ConnectionManager()


@router.post("/api/tts")
async def text_to_speech(text: str, voice: str = "default"):
    try:
        audio_data = await xiaomi_client.text_to_speech(text, voice)
        if not audio_data:
            raise HTTPException(500, "语音合成失败")

        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS错误: {e}")
        raise HTTPException(500, str(e))


@router.get("/api/models")
async def get_models():
    if settings.TRANSLATION_PROVIDER == "aliyun_livetranslate":
        return {
            "provider": settings.TRANSLATION_PROVIDER,
            "livetranslate": settings.DASHSCOPE_LIVETRANSLATE_MODEL,
            "asr": settings.DASHSCOPE_ASR_MODEL,
        }

    return {
        "provider": settings.TRANSLATION_PROVIDER,
        "asr": settings.XIAOMI_ASR_MODEL,
        "llm": settings.XIAOMI_LLM_MODEL,
        "tts": settings.XIAOMI_TTS_MODEL
    }


@router.get("/api/status")
async def get_status():
    if settings.TRANSLATION_PROVIDER == "aliyun_livetranslate":
        return {
            "status": "running",
            "version": settings.APP_VERSION,
            "provider": settings.TRANSLATION_PROVIDER,
            "api_configured": bool(settings.DASHSCOPE_API_KEY),
            "models": {
                "livetranslate": settings.DASHSCOPE_LIVETRANSLATE_MODEL,
                "second_livetranslate": settings.DASHSCOPE_SECOND_LIVETRANSLATE_MODEL,
                "asr": settings.DASHSCOPE_ASR_MODEL,
                "fallback_text": settings.DASHSCOPE_TEXT_MODEL,
            },
            "fallback": {
                "second_e2e_enabled": settings.ENABLE_SECOND_E2E,
                "asr_enabled": settings.ENABLE_ASR_FALLBACK,
                "translate_enabled": settings.ASR_FALLBACK_TRANSLATE,
                "audio_replay_seconds": settings.AUDIO_REPLAY_SECONDS,
            }
        }

    return {
        "status": "running",
        "version": settings.APP_VERSION,
        "provider": settings.TRANSLATION_PROVIDER,
        "api_configured": bool(settings.XIAOMI_API_KEY),
        "models": {
            "asr": settings.XIAOMI_ASR_MODEL,
            "llm": settings.XIAOMI_LLM_MODEL,
            "tts": settings.XIAOMI_TTS_MODEL
        }
    }


@router.get("/api/xiaomi/check")
async def check_xiaomi_api():
    return await xiaomi_client.health_check()


@router.get("/api/xiaomi/check-asr")
async def check_xiaomi_asr():
    return await xiaomi_client.check_asr()


@router.websocket("/ws/translate")
async def translate_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    live_session = None
    second_live_session = None
    asr_session = None
    fallback_tasks: set[asyncio.Task] = set()
    send_lock = asyncio.Lock()
    audio_ring_buffer = deque()
    audio_ring_bytes = 0
    max_ring_bytes = max(32000, int(16000 * 2 * settings.AUDIO_REPLAY_SECONDS))

    def remember_audio(audio_data: bytes):
        nonlocal audio_ring_bytes
        audio_ring_buffer.append(audio_data)
        audio_ring_bytes += len(audio_data)
        while audio_ring_bytes > max_ring_bytes and audio_ring_buffer:
            audio_ring_bytes -= len(audio_ring_buffer.popleft())

    async def replay_recent_audio(*sessions):
        if not audio_ring_buffer:
            return
        chunks = list(audio_ring_buffer)
        for session in sessions:
            if not session:
                continue
            for chunk in chunks:
                await session.send_audio(chunk)

    def track_task(task: asyncio.Task):
        fallback_tasks.add(task)
        task.add_done_callback(fallback_tasks.discard)
        return task

    async def safe_send_json(message: dict):
        async with send_lock:
            await websocket.send_json(message)

    if settings.TRANSLATION_PROVIDER == "aliyun_livetranslate":
        async def send_to_client(message: dict):
            await safe_send_json(message)

        async def send_asr_fallback(message: dict):
            await safe_send_json(message)
            if (
                not settings.ASR_FALLBACK_TRANSLATE
                or message.get("type") != "asr_final"
                or not message.get("content", {}).get("original")
            ):
                return

            content = message["content"]

            async def translate_and_send():
                ws_settings = manager.get_settings(websocket)
                source_lang = ws_settings.get("source_lang", "auto")
                target_lang = ws_settings.get("target_lang", "zh")
                result = await dashscope_text_translator.translate(
                    content["original"],
                    source_lang,
                    target_lang,
                )
                if result.get("translated"):
                    await safe_send_json({
                        "type": "asr_translation",
                        "content": {
                            **content,
                            "translated": result["translated"],
                            "timestamp": datetime.now().isoformat(),
                        },
                    })

            track_task(asyncio.create_task(translate_and_send()))

        async def start_live_session(replay_audio: bool = False):
            nonlocal live_session
            if live_session:
                await live_session.close()
            live_session = AliyunLiveTranslateSession(
                send_to_client,
                model=settings.DASHSCOPE_LIVETRANSLATE_MODEL,
                source_name="livetranslate",
                silence_duration_ms=settings.LIVETRANSLATE_SILENCE_DURATION_MS,
            )
            ws_settings = manager.get_settings(websocket)
            await live_session.connect(
                ws_settings.get("source_lang", "auto"),
                ws_settings.get("target_lang", "zh"),
            )
            if replay_audio:
                await replay_recent_audio(live_session)

        async def start_second_live_session(replay_audio: bool = False):
            nonlocal second_live_session
            if not settings.ENABLE_SECOND_E2E:
                return
            if second_live_session:
                await second_live_session.close()
            second_live_session = AliyunLiveTranslateSession(
                send_to_client,
                model=settings.DASHSCOPE_SECOND_LIVETRANSLATE_MODEL,
                source_name="livetranslate_secondary",
                silence_duration_ms=settings.SECOND_E2E_SILENCE_DURATION_MS,
            )
            ws_settings = manager.get_settings(websocket)
            await second_live_session.connect(
                ws_settings.get("source_lang", "auto"),
                ws_settings.get("target_lang", "zh"),
            )
            if replay_audio:
                await replay_recent_audio(second_live_session)

        async def start_asr_session(replay_audio: bool = False):
            nonlocal asr_session
            if not settings.ENABLE_ASR_FALLBACK:
                return
            if asr_session:
                await asr_session.close()
            asr_session = AliyunAsrRealtimeSession(send_asr_fallback)
            ws_settings = manager.get_settings(websocket)
            await asr_session.connect(ws_settings.get("source_lang", "auto"))
            if replay_audio:
                await replay_recent_audio(asr_session)

        async def ensure_live_session():
            nonlocal live_session
            if live_session:
                return True
            try:
                await start_live_session(replay_audio=True)
                return True
            except Exception as e:
                logger.error("阿里同传启动失败: %s", e)
                if live_session:
                    await live_session.close()
                live_session = None
                await safe_send_json({
                    "type": "error",
                    "content": {"message": f"阿里同传启动失败: {e}"}
                })
                return False

        async def ensure_second_live_session():
            nonlocal second_live_session
            if not settings.ENABLE_SECOND_E2E:
                return False
            if second_live_session:
                return True
            try:
                await start_second_live_session(replay_audio=True)
                return True
            except Exception as e:
                logger.error("第二端到端同传启动失败: %s", e)
                if second_live_session:
                    await second_live_session.close()
                second_live_session = None
                return False

        async def ensure_asr_session():
            nonlocal asr_session
            if not settings.ENABLE_ASR_FALLBACK:
                return False
            if asr_session:
                return True
            try:
                await start_asr_session(replay_audio=True)
                return True
            except Exception as e:
                logger.error("阿里 ASR 旁路启动失败: %s", e)
                if asr_session:
                    await asr_session.close()
                asr_session = None
                return False

    else:
        start_live_session = None
        start_second_live_session = None
        start_asr_session = None
        ensure_live_session = None
        ensure_second_live_session = None
        ensure_asr_session = None

    try:
        while True:
            data = await websocket.receive()

            if data["type"] == "websocket.receive":
                if "bytes" in data:
                    remember_audio(data["bytes"])
                    if ensure_live_session and await ensure_live_session():
                        await live_session.send_audio(data["bytes"])
                        if ensure_second_live_session and await ensure_second_live_session():
                            await second_live_session.send_audio(data["bytes"])
                        if ensure_asr_session and await ensure_asr_session():
                            await asr_session.send_audio(data["bytes"])
                    elif not ensure_live_session:
                        asyncio.create_task(handle_audio_data(websocket, data["bytes"]))
                elif "text" in data:
                    await handle_text_message(
                        websocket,
                        data["text"],
                        live_session,
                        start_live_session,
                        start_asr_session,
                        start_second_live_session,
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if live_session:
            await live_session.close()
        if second_live_session:
            await second_live_session.close()
        if asr_session:
            await asr_session.close()
        for task in list(fallback_tasks):
            task.cancel()
        logger.info("客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)
        if live_session:
            await live_session.close()
        if second_live_session:
            await second_live_session.close()
        if asr_session:
            await asr_session.close()
        for task in list(fallback_tasks):
            task.cancel()


async def handle_audio_data(websocket: WebSocket, audio_data: bytes):
    audio_lock = manager.get_audio_lock(websocket)
    if audio_lock.locked():
        logger.info("跳过过期音频片段：上一段仍在识别")
        return

    async with audio_lock:
        await _handle_audio_data(websocket, audio_data)


async def _handle_audio_data(websocket: WebSocket, audio_data: bytes):
    started_at = perf_counter()
    ws_settings = manager.get_settings(websocket)
    source_lang = ws_settings.get("source_lang", "en").lower()
    target_lang = ws_settings.get("target_lang", "zh").lower()

    asr_started_at = perf_counter()
    asr_result = await asr_service.recognize(audio_data, source_lang)
    asr_ms = int((perf_counter() - asr_started_at) * 1000)

    if "error" in asr_result:
        await websocket.send_json({
            "type": "error",
            "content": {"message": asr_result["error"]}
        })
        return

    original_text = asr_result.get("text", "").strip()
    if not original_text or len(original_text) < 3:
        return

    source_lang, target_lang = resolve_translation_direction(original_text, source_lang, target_lang)

    context = correction_service.get_buffer_context()

    translate_started_at = perf_counter()
    translate_result = await translate_service.translate(
        original_text,
        source_lang,
        target_lang,
        context
    )
    translate_ms = int((perf_counter() - translate_started_at) * 1000)

    if "error" in translate_result:
        await websocket.send_json({
            "type": "error",
            "content": {"message": translate_result["error"]}
        })
        return

    translated_text = translate_result.get("translated", "").strip()
    if not translated_text:
        return

    total_ms = int((perf_counter() - started_at) * 1000)
    logger.info(
        "音频片段处理完成: bytes=%s asr=%sms translate=%sms total=%sms",
        len(audio_data),
        asr_ms,
        translate_ms,
        total_ms,
    )

    if ws_settings.get("enable_correction", True):
        correction_result = await correction_service.correct(
            original_text,
            translated_text,
            source_lang
        )

        if correction_result.get("corrected"):
            await websocket.send_json({
                "type": "correction",
                "content": {
                    "index": len(correction_service.buffer) - 1,
                    "original": correction_result["original"],
                    "translated": correction_result["translated"]
                }
            })

    await websocket.send_json({
        "type": "final",
        "content": {
            "original": original_text,
            "translated": translated_text,
            "timestamp": datetime.now().isoformat(),
            "confidence": asr_result.get("confidence", 0)
        }
    })


async def handle_text_message(
    websocket: WebSocket,
    message: str,
    live_session: AliyunLiveTranslateSession | None = None,
    restart_live_session=None,
    restart_asr_session=None,
    restart_second_live_session=None,
):
    try:
        data = json.loads(message)

        if data.get("type") in {"settings", "start"}:
            payload = data.get("data", {}) if data.get("type") == "settings" else data
            manager.update_settings(websocket, payload)
            if restart_live_session:
                await restart_live_session(replay_audio=False)
            if restart_second_live_session:
                await restart_second_live_session(replay_audio=False)
            if restart_asr_session:
                await restart_asr_session(replay_audio=False)
            await websocket.send_json({
                "type": "settings_updated",
                "content": {"status": "ok"}
            })
        elif data.get("type") == "translate_text":
            text = data.get("text", "")
            source_lang = data.get("source_lang", "en")
            target_lang = data.get("target_lang", "zh")

            result = await translate_service.translate(text, source_lang, target_lang)

            await websocket.send_json({
                "type": "text_translated",
                "content": result
            })

    except json.JSONDecodeError:
        logger.error(f"无效的JSON消息: {message}")
