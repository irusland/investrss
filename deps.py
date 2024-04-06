from punq import Container, Scope

from invest.marketdata import (
    MarketDataSniffer,
)
from invest.marketdata import MarketDataSnifferSettings
from invest.marketdata import ShareInfoStatistFactory
from invest.invest_settings import InvestSettings
from invest.portfolio_informer import PortfolioInformer
from rss import RSSFeeder, RSSFeederSettings
from server import RSSServer
from telegram.notifier import TelegramNotifier
from telegram.notifier_settings import TelegramNotifierSettings


def get_container() -> Container:
    container = Container()
    container.register(RSSServer, RSSServer, scope=Scope.singleton)
    container.register(RSSFeeder, RSSFeeder, scope=Scope.singleton)
    container.register(InvestSettings, instance=InvestSettings(), scope=Scope.singleton)
    container.register(
        RSSFeederSettings, instance=RSSFeederSettings(), scope=Scope.singleton
    )
    container.register(PortfolioInformer, PortfolioInformer, scope=Scope.singleton)

    container.register(
        TelegramNotifierSettings,
        instance=TelegramNotifierSettings(),
        scope=Scope.singleton,
    )
    container.register(TelegramNotifier, TelegramNotifier, scope=Scope.singleton)

    container.register(
        ShareInfoStatistFactory, ShareInfoStatistFactory, scope=Scope.singleton
    )
    container.register(
        MarketDataSnifferSettings,
        instance=MarketDataSnifferSettings(),
        scope=Scope.singleton,
    )
    container.register(MarketDataSniffer, MarketDataSniffer, scope=Scope.singleton)

    return container
