from pydantic.v1 import BaseSettings


class OpenAISettings(BaseSettings):
    api_key: str
    whisper_model: str = "whisper-1"
    chat_model: str = "gpt-4o-mini"
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "shimmer"
    response_format: str = "wav"
    max_tokens: int = 500
    temperature: float = 0.7
    system_prompt: str = (
        "Ты голосовой помощник. Отвечай кратко и по делу на русском языке."
    )

    class Config:
        env_prefix = "OPENAI_"


class AudioSettings(BaseSettings):
    upload_dir: str = "uploaded_audio"
    filename_prefix: str = "audio"
    tts_filename_prefix: str = "tts"
    timestamp_format: str = "%Y%m%d_%H%M%S"

    class Config:
        env_prefix = "AUDIO_"
