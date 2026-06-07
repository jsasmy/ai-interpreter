from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "AI 同声传译助手"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 9000

    XIAOMI_API_KEY: str = ""
    XIAOMI_API_BASE: str = "https://token-plan-cn.xiaomimimo.com/v1"
    XIAOMI_API_ENDPOINT: str = "tp-cssf9gh45m7axddhvpj2j5rnfyo3uaf63g0jmqfpzja3crsm"

    XIAOMI_ASR_MODEL: str = "mimo-v2.5-asr"
    XIAOMI_LLM_MODEL: str = "mimo-v2.5"
    XIAOMI_TTS_MODEL: str = "mimo-v2.5-tts"

    TRANSLATION_PROVIDER: str = "xiaomi"

    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_REALTIME_URL: str = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
    DASHSCOPE_COMPATIBLE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DASHSCOPE_LIVETRANSLATE_MODEL: str = "qwen3.5-livetranslate-flash-realtime"
    DASHSCOPE_SECOND_LIVETRANSLATE_MODEL: str = "qwen3.5-livetranslate-flash-realtime"
    DASHSCOPE_ASR_MODEL: str = "qwen3-asr-flash-realtime"
    DASHSCOPE_TEXT_MODEL: str = "qwen-flash"
    DASHSCOPE_REPAIR_MODEL: str = "qwen-plus-latest"
    DASHSCOPE_TTS_URL: str = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
    DASHSCOPE_TTS_MODEL: str = "cosyvoice-v2"
    DASHSCOPE_TTS_VOICE: str = "longfeifei_v2"
    ENABLE_SECOND_E2E: bool = False
    LIVETRANSLATE_SILENCE_DURATION_MS: int = 480
    SECOND_E2E_SILENCE_DURATION_MS: int = 300
    ENABLE_ASR_FALLBACK: bool = False
    ASR_FALLBACK_TRANSLATE: bool = False
    AUDIO_REPLAY_SECONDS: float = 2.0
    DEBUG_REALTIME_EVENTS: bool = False
    ENABLE_CONTEXTUAL_REPAIR: bool = True
    CONTEXTUAL_REPAIR_MAX_CHARS: int = 260
    CONTEXTUAL_REPAIR_WINDOW_SIZE: int = 3

    SOURCE_LANG: str = "en"
    TARGET_LANG: str = "zh"

    ENABLE_CORRECTION: bool = True
    CORRECTION_BUFFER_SIZE: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
