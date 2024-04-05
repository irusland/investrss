from pydantic.v1 import BaseSettings


class TelegramNotifierSettings(BaseSettings):
    token: str
    chat_id: str

    class Config:
        env_prefix = 'TELEGRAM_'
