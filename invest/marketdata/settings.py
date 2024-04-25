from datetime import timedelta

from pydantic.v1 import BaseSettings
from tinkoff.invest import SubscriptionInterval


class MarketDataSnifferSettings(BaseSettings):
    last_candles_count = 5
    last_trades_count = 100
    last_trades_scrape_span = timedelta(minutes=1)
    interval = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE
    change_percent_threshold = 0.5

    on_error_sleep: timedelta = timedelta(seconds=10)

    class Config:
        env_prefix = "MARKETDATA_"
