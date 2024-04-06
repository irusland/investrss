import dataclasses

from tinkoff.invest import Share


@dataclasses.dataclass(init=True)
class ShareInfo:
    share: Share
