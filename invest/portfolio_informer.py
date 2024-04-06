from decimal import Decimal

from pydantic import BaseModel
from tinkoff.invest import Quotation, AsyncClient
from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest.utils import money_to_decimal

from invest.invest_settings import InvestSettings


class PortfolioInfo(BaseModel):
    total_amount: Decimal
    current_yield: Decimal
    yield_percent: Decimal


class PortfolioInformer:
    def __init__(self, invest_settings: InvestSettings):
        self._invest_settings = invest_settings
        self._account_id: str | None = None

    async def get_info(self) -> PortfolioInfo:
        async with AsyncClient(self._invest_settings.token) as client:
            main_account = await self._get_account_id(client)

            portfolio = await client.operations.get_portfolio(account_id=main_account)
            current_yield = Quotation(units=0, nano=0)
            for position in portfolio.positions:
                current_yield += position.expected_yield

            yield_percent = money_to_decimal(current_yield) / money_to_decimal(
                current_yield + portfolio.total_amount_portfolio
            )
            return PortfolioInfo(
                total_amount=money_to_decimal(portfolio.total_amount_portfolio),
                current_yield=money_to_decimal(current_yield),
                yield_percent=yield_percent,
            )

    async def _get_account_id(self, client: AsyncServices) -> str:
        if self._account_id is not None:
            return self._account_id

        accounts_response = await client.users.get_accounts()
        account = accounts_response.accounts[0]
        self._account_id = account.id
        return self._account_id
