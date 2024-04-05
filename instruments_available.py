import asyncio
import dataclasses
import os
from collections import deque
from datetime import timedelta, datetime
from decimal import Decimal
from statistics import mean
from textwrap import dedent
from threading import Event

from dotenv import load_dotenv
from pydantic.v1 import BaseSettings
from tinkoff.invest import (
    InstrumentType, MarketDataRequest,
    SubscribeCandlesRequest, SubscriptionAction, CandleInstrument, SubscriptionInterval,
    SubscribeLastPriceRequest, LastPriceInstrument, Share, SubscribeTradesRequest,
    TradeInstrument, TradeDirection, Candle, Trade, AsyncClient, InstrumentIdType,
)
from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest.utils import quotation_to_decimal, now

from invest_settings import InvestSettings
from telegram_notifier import TelegramNotifier

trade_direction_to_symbol = {
    TradeDirection.TRADE_DIRECTION_BUY: "🟢",
    TradeDirection.TRADE_DIRECTION_SELL: "🔻",
    TradeDirection.TRADE_DIRECTION_UNSPECIFIED: "❓",
}


class MarketDataSnifferSettings(BaseSettings):
    last_candles_count = 5
    last_trades_count = 50
    interval = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE
    change_percent_threshold = 0.5


@dataclasses.dataclass(init=True)
class ShareInfo:
    share: Share


class ShareInfoStatistFactory:
    def __init__(self, market_data_sniffer_settings: MarketDataSnifferSettings):
        self._settings = market_data_sniffer_settings

    def create(self):
        return ShareInfoStatist(self._settings)


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
                (candle.open, candle.close, candle.high, candle.low)
            )
        )
        self.last_candle_means.append(
            candle_mean
        )
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
            sum(trade.quantity for trade in trades) for trades in
            last_trades_in_second.values()
        )


@dataclasses.dataclass(init=True)
class ShareInfoContainer:
    share_info: ShareInfo
    share_info_statist: ShareInfoStatist


class MarketDataSniffer:
    def __init__(
        self,
        invest_settings: InvestSettings,
        market_data_sniffer_settings: MarketDataSnifferSettings,
        share_info_statist_factory: ShareInfoStatistFactory,
        telegram_notifier: TelegramNotifier,
    ):
        self._invest_settings = invest_settings
        self._settings = market_data_sniffer_settings
        self._share_info_statist_factory = share_info_statist_factory
        self._telegram_notifier = telegram_notifier

        self._share_info_containers: dict[str, ShareInfoContainer] = {}

        self._is_running = Event()

    def stop(self):
        self._is_running.clear()

    async def run(self):
        try:
            await self._run()
        except BaseException as e:
            self.stop()
            raise e

    async def _run(self):
        self._is_running.set()

        async with AsyncClient(self._invest_settings.token) as client:
            s = await client.instruments.get_favorites()
            share_to_watch = []
            for i in s.favorite_instruments:
                if i.api_trade_available_flag and i.instrument_kind == InstrumentType.INSTRUMENT_TYPE_SHARE:
                    share_response = await client.instruments.share_by(
                        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID,
                        id=i.uid,
                    )
                    share_to_watch.append(share_response.instrument)

            self._share_info_containers = {
                share.uid: ShareInfoContainer(
                    share_info=ShareInfo(share=share),
                    share_info_statist=self._share_info_statist_factory.create()
                )
                for share in share_to_watch
            }

            await self._init_historic_candles(client)
            asyncio.create_task(self._run_volume_per_second_monitor())

            await self._notify_about_start()

            requests = [
                MarketDataRequest(
                    subscribe_candles_request=SubscribeCandlesRequest(
                        waiting_close=True,
                        subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                        instruments=[
                            CandleInstrument(
                                instrument_id=share.uid,
                                interval=self._settings.interval,
                            ) for share in share_to_watch
                        ],
                    ),
                ),
                MarketDataRequest(
                    subscribe_last_price_request=SubscribeLastPriceRequest(
                        subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                        instruments=[
                            LastPriceInstrument(
                                instrument_id=share.uid,
                            ) for share in share_to_watch
                        ],
                    ),
                ),
                MarketDataRequest(
                    subscribe_trades_request=SubscribeTradesRequest(
                        subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                        instruments=[
                            TradeInstrument(
                                instrument_id=share.uid,
                            ) for share in share_to_watch
                        ],
                    )
                ),
            ]

            async def request_iterator():
                for request in requests:
                    yield request
                while True:
                    await asyncio.sleep(1)

            while self._is_running.is_set():
                try:
                    async for marketdata in client.market_data_stream.market_data_stream(
                            request_iterator()
                    ):
                        candle = marketdata.candle
                        last_price = marketdata.last_price
                        trade = marketdata.trade

                        if candle or last_price or trade:
                            response = (candle or last_price or trade)
                            container = self._share_info_containers[
                                response.instrument_uid]
                            share_info = container.share_info
                            share_info_statist = container.share_info_statist
                            share = container.share_info.share

                        if candle:
                            candle_mean = share_info_statist.observe_candle_mean(candle)
                            # print(
                            #     'candle', share.name, candle_mean,
                            #     share_info.last_candles_mean
                            # )

                        if last_price:
                            last_candles_mean = share_info_statist.last_candles_mean
                            change_percent = (quotation_to_decimal(
                                last_price.price
                            ) - last_candles_mean) / last_candles_mean * 100
                            formatted_change_percent = f'{change_percent:.2f}%'
                            if abs(
                                    change_percent
                            ) > self._settings.change_percent_threshold:
                                print(
                                    'last change', '📉' if change_percent < 0 else '📈',
                                    formatted_change_percent, share.name
                                )

                        if trade:
                            share_info_statist.observe_trade(trade)
                            if trade.quantity > share_info_statist.last_trades_mean_volume:
                                print(
                                    'trade', trade.quantity,
                                    trade_direction_to_symbol[trade.direction],
                                    share.name,
                                    trade.quantity,
                                    share_info_statist.last_trades_mean_volume
                                )

                except Exception as e:
                    print('exception', e)

    async def _run_volume_per_second_monitor(self):
        while self._is_running.is_set():
            vpss = {}
            for container in self._share_info_containers.values():
                vps = container.share_info_statist.last_trades_mean_volume_per_second
                if vps > 0:
                    vpss[container.share_info.share] = vps
            for share, vps in sorted(
                    vpss.items(), key=lambda p: p[1], reverse=True
            ):
                print(
                    'volume per second', share.name, vps
                )
            await asyncio.sleep(1)

    async def _init_historic_candles(
        self, client: AsyncServices
    ):
        for container in self._share_info_containers.values():
            response = await client.market_data.get_candles(
                instrument_id=container.share_info.share.uid,
                from_=now() - timedelta(minutes=self._settings.last_candles_count),
                to=now(),
                interval=self._settings.interval,
            )
            for historic_candle in response.candles:
                candle = Candle(
                    figi=container.share_info.share.figi,
                    interval=self._settings.interval,
                    open=historic_candle.open,
                    high=historic_candle.high,
                    low=historic_candle.low,
                    close=historic_candle.close,
                    volume=historic_candle.volume,
                    time=historic_candle.time,
                    last_trade_ts=historic_candle.time,
                    instrument_uid=container.share_info.share.uid,
                )
                container.share_info_statist.observe_candle_mean(candle)

    async def _notify_about_start(self):
        shares_to_watch = '\n'.join(
            # f'<a style="color: {container.share_info.share.brand.logo_base_color}">{container.share_info.share.name} {container.share_info.share.brand.logo_name}</a>'
            f'<pre>{container.share_info.share.name}</pre>'
            for container in self._share_info_containers.values()
        )
        html_message = dedent(
            f'''\
                Market data sniffer started {datetime.now()}
                shares to watch:
            '''
        ) + shares_to_watch + dedent(
            f'''\
            some shit
            '''
        )
        print(html_message)
        await self._telegram_notifier.send_message(html_message)


if __name__ == "__main__":
    load_dotenv()

    invest_settings = InvestSettings(os.environ["INVEST_TOKEN"])
    market_data_sniffer_settings = MarketDataSnifferSettings()
    share_info_statist_factory = ShareInfoStatistFactory(
        market_data_sniffer_settings=market_data_sniffer_settings
    )
    MarketDataSniffer(
        invest_settings=invest_settings,
        market_data_sniffer_settings=market_data_sniffer_settings,
        share_info_statist_factory=share_info_statist_factory
    ).run()
