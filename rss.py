import datetime
from rfeed import *


class RSSFeeder:
    def get_feed(self) -> Feed:
        # item1 = Item(
        #     title="Some change 1",
        #     link="https://github.com/irusland/investrss",
        #     description="Some change happened in the market.",
        #     author="Ruslan Sirazhetdinov",
        #     guid=Guid(
        #         "https://github.com/irusland/investrss"
        #     ),
        #     pubDate=datetime.datetime(2017, 8, 2, 4, 2)
        # )
        #
        # item2 = Item(
        #     title="Some change",
        #     link="https://github.com/irusland/investrss",
        #     description="Some change happened in the market.",
        #     author="Ruslan Sirazhetdinov",
        #     guid=Guid(
        #         "https://github.com/irusland/investrss"
        #     ),
        #     pubDate=datetime.datetime(2017, 8, 1, 4, 2)
        # )
        #
        # feed = Feed(
        #     title="investrss",
        #     link="https://github.com/irusland/investrss",
        #     description="Live market feed",
        #     language="en-US",
        #     lastBuildDate=datetime.datetime.now(),
        #     items=[
        #         # item1, item2
        #     ]
        # )
        itunes_item = iTunesItem(
            author="Santiago L. Valdarrama",
            image="http://www.example.com/artwork.jpg",
            duration="01:11:02",
            explicit="clean",
            subtitle="The subtitle of the podcast episode",
            summary="Here is the summary of this specific episode"
        )

        item = Item(
            title="Sample article",
            link="http://www.example.com/articles/1",
            description="This is the description of the first article",
            author="Santiago L. Valdarrama",
            guid=Guid("http://www.example.com/articles/1"),
            pubDate=datetime.datetime(2014, 12, 29, 10, 00),
            enclosure=Enclosure(
                url="http://www.example.com/articles/1.mp3", length=0, type='audio/mpeg'
            ),
            extensions=[itunes_item]
        )

        itunes = iTunes(
            author="Santiago L. Valdarrama",
            subtitle="A sample podcast that will never be produced",
            summary="This is just a fake description",
            image="http://www.example.com/artwork.jpg",
            explicit="clean",
            categories=iTunesCategory(name='Technology', subcategory='Software How-To'),
            owner=iTunesOwner(name='Santiago L. Valdarrama', email='svpino@gmail.com')
        )

        feed = Feed(
            title="Sample Podcast RSS Feed",
            link="http://www.example.com/rss",
            description="An example of how to generate an RSS 2.0 feed",
            language="en-US",
            lastBuildDate=datetime.datetime.now(),
            items=[item],
            extensions=[itunes]
        )

        print(feed.rss())

        return feed

