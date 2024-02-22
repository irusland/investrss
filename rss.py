import datetime

from pydantic.v1 import BaseSettings
from rfeed import *

from portfolio_informer import PortfolioInformer


class RSSFeederSettings(BaseSettings):
    total_amount_format: str = "   {total_amount:,.0f} P"
    current_yield_format: str = "   {current_yield:,.0f} P"
    yield_percent_format: str = "   {yield_percent:.2%}"


class RSSFeeder:
    def __init__(
        self, portfolio_informer: PortfolioInformer, settings: RSSFeederSettings
    ):
        self._portfolio_informer = portfolio_informer
        self._settings = settings

    async def get_feed(self) -> Feed:
        info = await self._portfolio_informer.get_info()

        total = Item(
            title=self._settings.total_amount_format.format(
                total_amount=info.total_amount,
            ),
            link="https://github.com/irusland/investrss",
            description="Some change happened in the market.",
            author="Ruslan Sirazhetdinov",
            guid=Guid(
                "https://github.com/irusland/investrss"
            ),
            pubDate=datetime.datetime.now()
        )
        current_yield = Item(
            title=self._settings.current_yield_format.format(
                current_yield=info.current_yield,
            ),
            link="https://github.com/irusland/investrss",
            description="Some change happened in the market.",
            author="Ruslan Sirazhetdinov",
            guid=Guid(
                "https://github.com/irusland/investrss"
            ),
            pubDate=datetime.datetime.now()
        )
        yield_percentage = Item(
            title=self._settings.yield_percent_format.format(
                yield_percent=info.yield_percent,
            ),
            link="https://github.com/irusland/investrss",
            description="Some change happened in the market.",
            author="Ruslan Sirazhetdinov",
            guid=Guid(
                "https://github.com/irusland/investrss"
            ),
            pubDate=datetime.datetime.now()
        )

        feed = Feed(
            title="investrss",
            link="https://github.com/irusland/investrss",
            description="Live market feed",
            language="en-US",
            lastBuildDate=datetime.datetime.now(),
            items=[total, current_yield, yield_percentage]
        )

        return feed
