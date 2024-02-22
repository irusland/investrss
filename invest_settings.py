from pydantic.v1 import BaseSettings


class InvestSettings(BaseSettings):
    token: str

    class Config:
        env_prefix = 'INVEST_'
