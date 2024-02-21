from punq import Container, Scope

from rss import RSSFeeder
from server import RSSServer


def get_container() -> Container:
    container = Container()
    container.register(RSSServer, RSSServer, scope=Scope.singleton)
    container.register(RSSFeeder, RSSFeeder, scope=Scope.singleton)

    return container
