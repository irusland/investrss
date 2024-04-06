import dataclasses

from invest.marketdata.share_info.info import ShareInfo
from invest.marketdata.share_info.statist import ShareInfoStatist


@dataclasses.dataclass(init=True)
class ShareInfoContainer:
    share_info: ShareInfo
    share_info_statist: ShareInfoStatist
