from _decimal import Decimal
from collections import deque
from statistics import mean

from tinkoff.invest import Candle, Trade
from tinkoff.invest.utils import quotation_to_decimal

from marketdata.settings import MarketDataSnifferSettings


class ShareInfoStatist:
    def __init__(self, marked_data_sniffer_settings: MarketDataSnifferSettings):
        self._settings = marked_data_sniffer_settings

        self.last_candle_means: deque[Decimal] = deque(
            maxlen=self._settings.last_candles_count
        )
        self.last_candles: deque[Candle] = deque(
            maxlen=self._settings.last_candles_count
        )
        self.last_trades: deque[Trade] = deque(maxlen=self._settings.last_trades_count)

    def observe_candle_mean(self, candle: Candle) -> Decimal:
        self.last_candles.append(candle)
        candle_mean = mean(
            map(
                quotation_to_decimal,
                (candle.open, candle.close, candle.high, candle.low),
            )
        )
        self.last_candle_means.append(candle_mean)
        return candle_mean

    @property
    def last_candles_mean(self) -> Decimal:
        return mean(self.last_candle_means)

    def observe_trade(self, trade: Trade):
        self.last_trades.append(trade)

    @property
    def last_trades_mean_volume(self) -> float:
        return mean([trade.quantity for trade in self.last_trades])

    @property
    def last_trades_mean_volume_per_second(self) -> float:
        if not self.last_trades:
            return 0
        last_trades_in_second = {}
        for trade in self.last_trades:
            rounded = trade.time.replace(microsecond=0)
            last_trades = last_trades_in_second.get(rounded, [])
            last_trades.append(trade)
            last_trades_in_second[rounded] = last_trades

        print(last_trades_in_second)
        return mean(
            sum(trade.quantity for trade in trades)
            for trades in last_trades_in_second.values()
        )
