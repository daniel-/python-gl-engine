from feed import Feed
from re import findall
from operator import add

from Levenshtein import ratio

# eztv torrent search
EZTV_SEARCH = "http://www.ezrss.it/search/index.php?simple&show_name=%s&mode=rss"

# list of series to download torrent files for
WANTED_SERIES = [
  ("American Dad",  10, 2) \
, ("Family Guy",    10, 2) \
, ("Simpsons",      10, 2) \
, ("South Park",    10, 2) \
, ("Lost",          10, 2) \
, ("Heroes",        10, 2) \
, ("Futurama",      10, 2) \
, ("Robot Chicken", 10, 2) \
, ("Doctor Who",    10, 2)
]

# keywords you like in the rss metadata.
# if multiple episodes are downloadable,
# the one with most matches will be choosen.
LIKING = [
    "x264", "hdtv", "repack", "proper"
]

class SeriesFeed(Feed):
    """
    SeriesFeed is doing some additional pattern matching on
    season and episode number to avoid downloading the same
    episode twice.
    """

    # separates series name from other data in the id rss field
    ID_SEPARATORS = [
        "_", ";"
    ]
    
    def __init__(self, id_file, name, url, n_weeks, n_items):
        self.series_name = name
        self.item_ids = {}
        
        Feed.__init__(self, id_file, url, n_weeks, n_items)
    
    def parse_episode(self, metadata):
        """
        parses season and episode number from rss metadata.
        metadata must be lowercase.
        """
        for s in metadata:
            for format in [r'(\d+)x(\d+)', r's(\d+)e(\d+)', \
                           r'season: (\d+); episode: (\d+)']:
                match = findall(format, s)
                if len(match)>0:
                    return tuple(map(int, list(match[0])))
        return None
    
    def parse_series(self, metadata):
        """
        parses series name from rss metadata.
        metadata must be lowercase.
        """
        for s in metadata:
            match = findall(r'show name: (.+);', s)
            if match != []:
                return match[0]
            match = findall(r'/(\d+)/(.+)-s(\d+)e(\d+)-', s)
            if match != []:
                return match[0][1]
        return ""
    
    def format_episode(self, season, episode):
        """
        formats id for an episode.
        """
        def format_int(i):
            if i < 10: return "0" + str(i)
            else: return str(i);
        return self.series_name + "_S" + format_int(season) + "E" + format_int(episode)
    
    def get_item_id(self, item):
        """
        formats item id from rss metadata.
        """
        
        if self.item_ids.has_key(item['id']):
            # id parsed before
            return self.item_ids[item['id']]
        
        title    = item['title'].lower()
        summary  = item['summary'].lower()
        id       = item['id'].lower()
        ep = self.parse_episode([id, title, summary])
        if ep == None:
            # parse failed ... using rss id
            self.item_ids[item['id']] = item['id']
        else:
            # parse succeeded ... using custom id format
            self.item_ids[item['id']] = \
                self.format_episode(ep[0], ep[1])
        # return the id
        return self.item_ids[item['id']]
    
    def isWanted(self, item):
        item_id = self.get_item_id(item)
        
        def chooseMax( (x,xv), (y,yv) ):
            if yv>xv: return (y,yv)
            else:     return (x,xv)
        def isWantedSep(sep):
            series_name =  str(item_id.split(sep)[0])
            wanted_series = map(lambda x: x.lower(),
                    map(lambda x: x[0], WANTED_SERIES))
            data = reduce(chooseMax,
                map(lambda x: (x, ratio(series_name, x)), wanted_series))
            return data[1]>0.5

        for sep in self.ID_SEPARATORS:
            if isWantedSep(sep):
                return True
        return False
    
    def filter(self, items):
        """
        filter out equal episodes, choosing the one
        with most matching words in LIKING.
        TODO: would be nice to compare by filesize/seeders/leechers
        """
        
        items = filter(self.isWanted, items)
        
        # fill episodes hashtable
        episodes = {}
        for item in items:
            item_id = self.get_item_id(item)
            if episodes.has_key(item_id):
                episodes[item_id].append(item)
            else:
                episodes[item_id] = [item]
        
        # convert to list of tuples
        episodes = zip(episodes.keys(),episodes.values())
        for j in range(len(episodes)):
            (epid,items) = episodes[j]
            
            if len(items)==0:
                # just one download possible for this episode
                continue
            
            # multiple downloads for this episode
            buf = zip(items,[0]*len(items))
            # check if a episode has more keywords the user likes
            for i in range(len(buf)):
                (item, num) = buf[i]
                title    = item['title'].lower()
                summary  = item['summary'].lower()
                id       = item['id'].lower()
                for l in LIKING:                        
                    # count matches
                    for s in [title, summary, id]:
                        if s.find(l.lower()) != -1:
                            num += 1
                            break
                buf[i] = (item, num)
            
            # get the best item
            best = []
            for b in buf:
                if best == []:
                    best = [b]
                elif b[1]>best[0][1]:
                    # item has better score
                    best = [b]
                elif b[1]==best[0][1]:
                    # download both on equal score
                    best.append(b)
            # use most likely one
            episodes[j] = (epid, map(lambda x: x[0], best))
        # return list of tuple with id
        # and downloadable torrents of a rss item
        return map(lambda (id,items): (id, \
            reduce(lambda t1,t2: t1+t2, \
                map(self.get_torrents, items))), episodes)


# series feeds with torrent enclosures
SERIES = map(lambda (name, n, m):
             (name, EZTV_SEARCH % name.replace(" ", "+"), n, m),
             WANTED_SERIES)

