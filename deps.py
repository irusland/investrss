from punq import Container, Scope

from instruments_available import (
    MarketDataSniffer, MarketDataSnifferSettings,
    ShareInfoStatistFactory,
)
from invest_settings import InvestSettings
from portfolio_informer import PortfolioInformer
from rss import RSSFeeder, RSSFeederSettings
from server import RSSServer
from telegram_notifier import TelegramNotifier
from telegram_notifier_settings import TelegramNotifierSettings


def get_container() -> Container:
    container = Container()
    container.register(RSSServer, RSSServer, scope=Scope.singleton)
    container.register(RSSFeeder, RSSFeeder, scope=Scope.singleton)
    container.register(InvestSettings, instance=InvestSettings(), scope=Scope.singleton)
    container.register(RSSFeederSettings, instance=RSSFeederSettings(), scope=Scope.singleton)
    container.register(PortfolioInformer, PortfolioInformer, scope=Scope.singleton)

    container.register(TelegramNotifierSettings, instance=TelegramNotifierSettings(), scope=Scope.singleton)
    container.register(TelegramNotifier, TelegramNotifier, scope=Scope.singleton)

    container.register(ShareInfoStatistFactory, ShareInfoStatistFactory, scope=Scope.singleton)
    container.register(MarketDataSnifferSettings, instance=MarketDataSnifferSettings(), scope=Scope.singleton)
    container.register(MarketDataSniffer, MarketDataSniffer, scope=Scope.singleton)

    return container
