import socket
import traceback
from datetime import datetime
from textwrap import dedent

from pydantic.v1 import BaseSettings
from tinkoff.invest import Share
from tinkoff.invest.schemas import BrandData

from invest.marketdata.share_info.container import ShareInfoContainer
from telegram.notifier import TelegramNotifier


class MarketDataNotifierSettings(BaseSettings):
    send_list_of_shares_on_start: bool = False


class MarketDataNotifier:
    def __init__(
        self, telegram_notifier: TelegramNotifier, settings: MarketDataNotifierSettings
    ):
        self._telegram_notifier = telegram_notifier
        self._settings = settings

    async def notify_about_start(
        self, share_info_containers: dict[str, ShareInfoContainer]
    ):
        # f'<li><a style="color: {container.share_info.share_info.brand.logo_base_color}">{container.share_info.share_info.name}</a> <img src="{self._get_brand_url(container.share_info.share_info.brand)}" alt="{container.share_info.share_info.brand.logo_name}">'

        html_message = dedent(
            f"""\
                Market data sniffer started {datetime.now()} on {socket.gethostname()}🛜 
                shares to watch:
            """
        )
        await self._telegram_notifier.send_message(html_message)
        if self._settings.send_list_of_shares_on_start:
            for container in share_info_containers.values():
                message = f'<pre>{container.share_info.share.name}</pre><a href="{self._get_brand_url(container.share_info.share.brand)}">link</a>'
                await self._telegram_notifier.send_message(message)
        else:
            await self._telegram_notifier.send_message(
                "\n".join(
                    container.share_info.share.name
                    for container in share_info_containers.values()
                )
            )

    async def notify_high_change(self, change_percent: float, share: Share):
        formatted_change_percent = f"{change_percent:.2f}%"
        await self._telegram_notifier.send_message(
            dedent(
                f"""\
                {"📉" if change_percent < 0 else "📈"} {formatted_change_percent} <pre>{share.name}</pre>
                """
            )
        )

    def _get_brand_url(self, brand: BrandData, size=160):
        name, png = brand.logo_name.split(".")
        return f"https://invest-brands.cdn-tinkoff.ru/{name}x{size}.{png}"

    async def notify_error(self, e):
        try:
            error = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            await self._telegram_notifier.send_message(
                dedent(
                    f"""\
                Error occurred:
                ```python
                """
                )
                + error
                + dedent(
                    """\
                    ```
                    """
                ),
                parse_mode="MarkdownV2",
            )
        except Exception as e:
            print("Cannot notify about error", e)
