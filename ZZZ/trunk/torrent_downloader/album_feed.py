from feed import Feed

ALBUMS = [
]

class AlbumFeed(Feed):
    def __init__(self, id_file, url, n_weeks, n_items):
        Feed.__init__(self, id_file, url, n_weeks, n_items)
    
    def filter_feed(self, torrents):
        # TODO: use local collection for decision, always download
        # artists from collection. dont download something already in collection.
        return torrents
