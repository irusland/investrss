import asyncio

import aiohttp
from dotenv import load_dotenv

from telegram_notifier_settings import TelegramNotifierSettings


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
    # loop.run_until_complete(
    #     notifier.send_message(
    #         dedent(
    #             '''\
    #                 A message with a
    #                 link: <a href="http://localhost:8000/html_render?raw_html=%3Ch1%3E%3Ca%20href%3D%22tinkoffbank%3A%2F%2F%22%3ETINKOFF%3C%2Fa%3E%3C%2Fh1%3E">Link to a link</a>
    #                 https://localhost:8000
    #                 <b>bold</b>, <strong>bold</strong>
    #                 <i>italic</i>, <em>italic</em>
    #                 <u>underline</u>, <ins>underline</ins>
    #                 <s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
    #                 <b>bold <i>italic bold <s>italic bold strikethrough</s> <u>underline italic bold</u></i> bold</b>
    #                 <a href="http://www.example.com/">inline URL</a>
    #                 <a href="tg://user?id=123456789">inline mention of a user</a>
    #                 <code>inline fixed-width code</code>
    #                 <pre>pre-formatted fixed-width code block</pre>
    #                 <pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language</code></pre>
    #             '''
    #         )
    #     )
    # )
    # loop.run_until_complete(
    #     notifier.send_message(
    #         dedent(
    #             '''\
    #                 <pre>
    #                 | Tables   |      Are      |  Cool |
    #                 |----------|:-------------:|------:|
    #                 | col 1 is |  left-aligned | $1600 |
    #                 | col 2 is |    centered   |   $12 |
    #                 | col 3 is | right-aligned |    $1 |
    #                 </pre>
    #             '''
    #         ), parse_mode='MarkdownV2',
    #     )
    # )
    loop.run_until_complete(notifier.send_mini_app())
