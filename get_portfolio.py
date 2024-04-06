import os
from pprint import pprint

from tinkoff.invest import Client, Quotation
from tinkoff.invest.utils import money_to_decimal

TOKEN = os.environ["INVEST_TOKEN"]


def main():
    with Client(TOKEN) as client:
        accounts_response = client.users.get_accounts()
        account = accounts_response.accounts[0]
        main_account = account.id

        portfolio = client.operations.get_portfolio(account_id=main_account)
        pprint(portfolio)
        current_yield = Quotation(units=0, nano=0)
        for position in portfolio.positions:
            current_yield += position.expected_yield

        yield_precent = money_to_decimal(current_yield) / money_to_decimal(
            current_yield + portfolio.total_amount_portfolio
        )
        print(
            money_to_decimal(portfolio.total_amount_portfolio),
            money_to_decimal(current_yield),
            yield_precent,
        )


if __name__ == "__main__":
    main()
