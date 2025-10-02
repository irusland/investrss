import os

from dotenv import load_dotenv
from tinkoff.invest import Client

from invest.invest_settings import InvestSettings


def main():
    settings = InvestSettings()

    with Client(settings.token) as client:
        ticker = "DELI"
        r = client.instruments.find_instrument(query=ticker)
        for instrument in r.instruments:
            if instrument.api_trade_available_flag and instrument.ticker == ticker:
                print(instrument)


if __name__ == "__main__":
    load_dotenv()
    main()
