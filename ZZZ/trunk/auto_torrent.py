#!/usr/bin/env python

import time
import datetime
from os import path

import feedparser
from urllib import urlretrieve

# torrents will be donloaded in this dir
AUTO_DIR     = '/downloads/torrents'
# feeds with torrent enclosures
FEEDS        = ( \
		  "http://www.ezrss.it/search/index.php?simple&show_name=American+Dad&mode=rss" \
		, "http://www.ezrss.it/search/index.php?simple&show_name=Family+Guy&mode=rss" \
		, "http://www.ezrss.it/search/index.php?simple&show_name=Simpsons&mode=rss" \
		, "http://www.ezrss.it/search/index.php?simple&show_name=South+Park&mode=rss" \
		, "http://www.ezrss.it/search/index.php?simple&show_name=Lost&mode=rss" \
		, "http://www.ezrss.it/search/index.php?simple&show_name=Heroes&mode=rss" \
		, "http://www.ezrss.it/search/index.php?simple&show_name=Futurama&mode=rss" \
		, "http://www.ezrss.it/search/index.php?simple&show_name=Robot+Chicken&mode=rss" \
	)
# max n feed items will be processed
N_ITEMS      = 10
# max n weeks old items will be processed
N_WEEKS      = 2
# max n items will be cached as allready processed
N_CACHE      = 1000

# file where processed feeds are remembered.
ID_FILE_PATH = path.expanduser("~") + "/.feed_ids"

# date format of feeds (without %z)
DATE_FORMAT  = "%a, %d %b %Y %H:%M:%S"

class FeedIdFile:
	def __init__ (self, file_path):
		if not path.isfile(file_path):
			buf = open(file_path, "w")
			buf.close()
		
		# read in processed ids
		self.file_path = file_path
		f = open(file_path, "r")
		self.ids = map (lambda x: x[:-1], f.readlines()[0:N_CACHE])
		f.close()
	
	def addId (self, feedId):
		# add a new feed id
		self.ids += [feedId]
		# last n items
		self.ids = self.ids[-N_CACHE:]
		f = open(self.file_path, "w")
		f.writelines(map (lambda x: x+"\n", self.ids))
		f.close()
	
	def getIds (self):
		return self.ids

def download_torrent(item, id_file):
	for attachment in item['enclosures']:
		torrent_uri = attachment['href']
		# must be correct extension
		if torrent_uri[-8:] != ".torrent": return
		# download the torrent
		urlretrieve(torrent_uri, AUTO_DIR + "/" + path.basename(torrent_uri))
	# remember feed id
	id_file.addId(item.id)

def item_is_new(item, id_file):
	return id_file.getIds().count(item.id) == 0

def parse_feeds(id_file):
	# local time
	now = time.localtime()
	# time of oldest feed to process
	n_weeks_ago = (datetime.date(now.tm_year, now.tm_mon, now.tm_mday) \
		- datetime.timedelta(days=0, weeks=N_WEEKS)).timetuple()
	
	# parse feeds
	for feed in FEEDS:
		parse = feedparser.parse(feed)
		
		# filter out some items
		latest_items = [item \
			for item in parse['items'][0:N_ITEMS] \
			if time.strptime(item['date'][:-6], DATE_FORMAT) > n_weeks_ago]
		
		for item in [item for item in latest_items if item_is_new(item, id_file)]:
			# add file to auto download dir
			download_torrent(item, id_file)

if __name__ == "__main__":
	parse_feeds(FeedIdFile(ID_FILE_PATH))

