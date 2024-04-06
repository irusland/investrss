from marketdata.settings import MarketDataSnifferSettings
from marketdata.share_info.statist import ShareInfoStatist


class ShareInfoStatistFactory:
    def __init__(self, market_data_sniffer_settings: MarketDataSnifferSettings):
        self._settings = market_data_sniffer_settings

    def create(self):
        return ShareInfoStatist(self._settings)
