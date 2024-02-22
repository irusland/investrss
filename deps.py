from punq import Container, Scope

from invest_settings import InvestSettings
from portfolio_informer import PortfolioInformer
from rss import RSSFeeder, RSSFeederSettings
from server import RSSServer


def get_container() -> Container:
    container = Container()
    container.register(RSSServer, RSSServer, scope=Scope.singleton)
    container.register(RSSFeeder, RSSFeeder, scope=Scope.singleton)
    container.register(InvestSettings, instance=InvestSettings(), scope=Scope.singleton)
    container.register(RSSFeederSettings, instance=RSSFeederSettings(), scope=Scope.singleton)
    container.register(PortfolioInformer, PortfolioInformer, scope=Scope.singleton)

    return container
