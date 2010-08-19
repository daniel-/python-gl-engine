import feedparser
import datetime
import time

# date format of feeds (without %z)
DATE_FORMAT  = "%a, %d %b %Y %H:%M:%S"

class Feed(object):
	def __init__(self, id_file, url, n_weeks, n_items):
		self.id_file = id_file
		self.url = url
		self.n_weeks = n_weeks
		self.n_items = n_items
		self.n_weeks_ago = 0
	
	def parse_feed(self):
		return feedparser.parse(self.url)
	
	def get_torrents(self, item):
		return map(lambda m: m['href'], [\
                i for i in item['enclosures'] if\
                i['type'] == 'application/x-bittorrent'])
	
	def get_item_id(self, item):
		return item.id
	
	def process(self):
		"""
		returns list of torrents to download.
		"""
		now = time.localtime()
		self.n_weeks_ago = (datetime.date(now.tm_year, now.tm_mon, now.tm_mday) \
				- datetime.timedelta(days=0, weeks=self.n_weeks)).timetuple()
		return self.filter(\
			self.filter_known(\
			self.filter_without_torrent(\
			self.filter_old(self.parse_feed()['items'][0:self.n_items]))))
	
	def filter(self, items):
		"""
		Filters some rss items, to be implemented by subclasses.
		"""
		return items
	
	def has_torrent(self, item):
		for attachment in item['enclosures']:
			if attachment['type'] == 'application/x-bittorrent':
				return True
		return False
	
	def matches_date(self, item):
		return time.strptime(item['date'][:-6], DATE_FORMAT) > self.n_weeks_ago
	
	def item_is_new(self, item):
		id = self.get_item_id(item)
		if id == None:
			return False
		else:
			return self.id_file.getIds().count(id) == 0
	
	def filter_without_torrent(self, items):
		"""
		filters rss entries withot torrent enclosures.
		"""
		return [item for item in items if self.has_torrent(item)]
	
	def filter_old(self, items):
		"""
		filters old rss entries.
		"""
		if self.n_weeks != None:
			return [item for item in items if self.matches_date(item)]
		else:
			return items
	
	def filter_known(self, items):
		"""
		filters known rss entries.
		"""
		return [item for item in items if self.item_is_new(item)]


