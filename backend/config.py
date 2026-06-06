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
    DASHSCOPE_LIVETRANSLATE_MODEL: str = "qwen3.5-livetranslate-flash-realtime-2026-05-19"
    DASHSCOPE_ASR_MODEL: str = "qwen3-asr-flash-realtime"

    SOURCE_LANG: str = "en"
    TARGET_LANG: str = "zh"

    ENABLE_CORRECTION: bool = True
    CORRECTION_BUFFER_SIZE: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
