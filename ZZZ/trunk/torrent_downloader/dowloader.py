#!/usr/bin/env python

from os import path
from urllib import urlretrieve

from feed_file import FeedIdFile

from series_feed import SERIES,SeriesFeed
#from movie_feed  import MOVIES,MovieFeed
#from album_feed  import ALBUMS,AlbumFeed

# torrents will be downloaded in this dir
AUTO_DIR     = '/downloads/torrents'
# file where processed feeds are remembered.
ID_FILE_PATH = path.expanduser("~") + "/.torrent_downloader_history"


def parse_feeds(id_file):
    series = map(lambda (name,uri,items,weeks): \
        SeriesFeed(id_file, name, uri, weeks, items), SERIES)
    #movies = map(lambda (uri,items,weeks): \
    #    MovieFeed(id_file, uri, weeks, items), MOVIES)
    #albums = map(lambda (uri,items,weeks): \
    #    AlbumFeed(id_file, uri, weeks, items), ALBUMS)
    for feed in series: #(series+movies+albums):
        for (id,torrents) in feed.process():
            for uri in torrents:
                urlretrieve(uri, AUTO_DIR + "/" + (id + ".torrent").replace("/", "_"))
            id_file.addId(id)

if __name__ == "__main__":
    parse_feeds(FeedIdFile(ID_FILE_PATH))
