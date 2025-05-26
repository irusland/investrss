import asyncio

import aiohttp
from dotenv import load_dotenv

from telegram_notifier.notifier_settings import TelegramNotifierSettings


class TelegramNotifier:
    def __init__(self, telegram_notifier_settings: TelegramNotifierSettings):
        self._settings = telegram_notifier_settings
        self._aiohttp_session = aiohttp.ClientSession()
        self._send_message_url = (
            f"https://api.telegram.org/bot{self._settings.token}/sendMessage"
        )

    async def send_message(self, message, parse_mode="HTML"):
        data = {
            "chat_id": self._settings.chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }
        async with self._aiohttp_session.post(
            self._send_message_url, data=data
        ) as response:
            print(await response.text())
            response.raise_for_status()

    async def send_mini_app(self):
        data = {
            "text": "Test web_app http://192.168.31.136:8000/get_file?filename=list.html",
            "chat_id": self._settings.chat_id,
            "web_app": {
                "url": "http://192.168.31.136:8000/get_file?filename=list.html"
            },
        }
        async with self._aiohttp_session.post(
            self._send_message_url, data=data
        ) as response:
            print(await response.text())
            response.raise_for_status()


if __name__ == "__main__":
    load_dotenv()
    settings = TelegramNotifierSettings()
    notifier = TelegramNotifier(settings)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(notifier.send_mini_app())
