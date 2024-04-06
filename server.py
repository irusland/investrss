import asyncio

from fastapi import FastAPI, Response, Query
from starlette.requests import Request
from starlette.responses import HTMLResponse, FileResponse

from marketdata.sniffer import MarketDataSniffer
from rss import RSSFeeder
from static.path import STATIC_PATH


class RSSServer(FastAPI):
    """Fast API server to serve RSS feed to the client."""

    def __init__(self, feeder: RSSFeeder, market_data_sniffer: MarketDataSniffer):
        super().__init__()
        self._feeder = feeder
        self._market_data_sniffer = market_data_sniffer
        self.add_api_route("/feed", endpoint=self.get_feed, methods=["GET"])
        self.add_api_route("/html_render", endpoint=self.html_render, methods=["GET"])
        self.add_api_route("/get_file", endpoint=self.get_file, methods=["GET"])
        self.on_event("startup")(self.on_startup)
        self.on_event("shutdown")(self.on_shutdown)

    async def on_startup(self):
        asyncio.create_task(self._market_data_sniffer.run())

    async def on_shutdown(self):
        self._market_data_sniffer.stop()

    async def get_feed(self, request: Request) -> Response:
        feed = await self._feeder.get_feed()
        return Response(content=feed.rss(), media_type="application/xml")

    async def html_render(self, raw_html: str = Query(...)) -> Response:
        return HTMLResponse(content=raw_html)

    async def get_file(self, filename: str = Query(...)) -> Response:
        return FileResponse(STATIC_PATH / filename)
