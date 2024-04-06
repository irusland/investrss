from pydantic.v1 import BaseSettings
from tinkoff.invest import SubscriptionInterval


class MarketDataSnifferSettings(BaseSettings):
    last_candles_count = 5
    last_trades_count = 50
    interval = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE
    change_percent_threshold = 0.01
