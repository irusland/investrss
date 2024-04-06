import os

from dotenv import load_dotenv
from tinkoff.invest import Client

load_dotenv()
TOKEN = os.environ["INVEST_TOKEN"]


def main():
    with Client(TOKEN) as client:
        r = client.instruments.find_instrument(query="DELI")
        for i in r.instruments:
            print(i)


if __name__ == "__main__":
    main()
