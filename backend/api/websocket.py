from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional
import json
import asyncio
import logging
import tempfile
import os
import httpx
from time import perf_counter
from datetime import datetime

from services.asr_service import asr_service
from services.translate_service import translate_service
from services.correction_service import correction_service
from services.aliyun_livetranslate_service import AliyunLiveTranslateSession
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


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "未选择文件")

    allowed_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.mp4', '.avi', '.mov']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"不支持的文件格式: {ext}")

    try:
        content = await file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        asr_result = await asr_service.recognize(content, "en")

        if "error" in asr_result:
            raise HTTPException(500, asr_result["error"])

        original_text = asr_result.get("text", "")
        if not original_text:
            raise HTTPException(400, "无法识别音频内容")

        translate_result = await translate_service.translate(original_text, "en", "zh")

        if "error" in translate_result:
            raise HTTPException(500, translate_result["error"])

        return {
            "success": True,
            "filename": file.filename,
            "original": original_text,
            "translated": translate_result.get("translated", ""),
            "confidence": asr_result.get("confidence", 0),
            "duration": len(content) / 16000
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件处理错误: {e}")
        raise HTTPException(500, str(e))
    finally:
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass


@router.post("/api/translate-url")
async def translate_url(url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            content_type = response.headers.get("content-type", "")

            if "audio" in content_type or "video" in content_type:
                audio_data = response.content
                asr_result = await asr_service.recognize(audio_data, "en")

                if "error" in asr_result:
                    raise HTTPException(500, asr_result["error"])

                original_text = asr_result.get("text", "")
                translate_result = await translate_service.translate(original_text, "en", "zh")

                return {
                    "success": True,
                    "url": url,
                    "original": original_text,
                    "translated": translate_result.get("translated", ""),
                    "confidence": asr_result.get("confidence", 0)
                }
            else:
                raise HTTPException(400, "URL不是音频或视频文件")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL处理错误: {e}")
        raise HTTPException(500, str(e))


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
                "asr": settings.DASHSCOPE_ASR_MODEL,
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

    if settings.TRANSLATION_PROVIDER == "aliyun_livetranslate":
        async def send_to_client(message: dict):
            await websocket.send_json(message)

        live_session = AliyunLiveTranslateSession(send_to_client)
        ws_settings = manager.get_settings(websocket)
        try:
            await live_session.connect(
                ws_settings.get("source_lang", "auto"),
                ws_settings.get("target_lang", "zh"),
            )
        except Exception as e:
            logger.error("阿里同传启动失败: %s", e)
            await live_session.close()
            live_session = None
            await websocket.send_json({
                "type": "error",
                "content": {"message": f"阿里同传启动失败: {e}"}
            })

    try:
        while True:
            data = await websocket.receive()

            if data["type"] == "websocket.receive":
                if "bytes" in data:
                    if live_session:
                        await live_session.send_audio(data["bytes"])
                    else:
                        asyncio.create_task(handle_audio_data(websocket, data["bytes"]))
                elif "text" in data:
                    await handle_text_message(websocket, data["text"], live_session)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if live_session:
            await live_session.close()
        logger.info("客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)
        if live_session:
            await live_session.close()


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
    live_session: AliyunLiveTranslateSession | None = None
):
    try:
        data = json.loads(message)

        if data.get("type") == "settings":
            manager.update_settings(websocket, data.get("data", {}))
            if live_session:
                ws_settings = manager.get_settings(websocket)
                await live_session.update_settings(
                    ws_settings.get("source_lang", "auto"),
                    ws_settings.get("target_lang", "zh"),
                )
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
