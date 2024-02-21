from deps import get_container
from server import RSSServer

app = get_container().resolve(RSSServer)
