import dataclasses

from marketdata.share_info.info import ShareInfo
from marketdata.share_info.statist import ShareInfoStatist


@dataclasses.dataclass(init=True)
class ShareInfoContainer:
    share_info: ShareInfo
    share_info_statist: ShareInfoStatist
