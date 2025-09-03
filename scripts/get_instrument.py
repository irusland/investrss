import os

from dotenv import load_dotenv
from tinkoff.invest import Client

from invest.invest_settings import InvestSettings


def main():
    settings = InvestSettings()

    with Client(settings.token) as client:
        r = client.instruments.find_instrument(query="DELI")
        for i in r.instruments:
            print(i)


if __name__ == "__main__":
    load_dotenv()
    main()
