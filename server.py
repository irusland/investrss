from fastapi import FastAPI, Response
from starlette.requests import Request

from rss import RSSFeeder


class RSSServer(FastAPI):
    """Fast API server to serve RSS feed to the client."""

    def __init__(
        self, feeder: RSSFeeder
    ):
        super().__init__()
        self._feeder = feeder
        self.add_route("/feed", self.get_feed, methods=["GET"])

    async def get_feed(self, request) -> Response:
        feed = self._feeder.get_feed()
        return Response(content=feed.rss(), media_type="application/xml")
