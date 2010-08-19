# -*- coding: utf-8 -*-

import datetime
from os import path

import re
import pickle

from feed import Feed
from imdb import IMDb
from Levenshtein import ratio

from book import BOOK

# list of movie feeds with torrent enclosures
MOVIES = [
  # (uri, items, weeks)
  ("http://saugstube-torrent.to/pub/xml/FeedGroup-Video.rss",  10, 2)
]

# list of user rated movies
KNOWLEDGE_BASE = [
      (u"Twelve Monkeys",                 0.95)
    , (u"Pulp Fiction",                   0.95)
    , (u"23",                             0.88)
    , (u"Animatrix",                      0.97)
    , (u"Waking Life",                    0.70)
    , (u"V for Vendetta",                 0.85)
    , (u"Bender's Big Score",             0.95)
    , (u"The Lord of The Rings",          0.95)
    , (u"The Butterfly Effect",           0.85)
    , (u"Cube",                           0.70)
    , (u"The Fifth Element",              0.79)
    , (u"Fear and Loathing in Las Vegas", 0.97)
    , (u"The Matrix",                     0.85)
    , (u"Star Wars: Clone Wars",          0.82)
    , (u"A Clockwork Orange",             0.92)
    , (u"Trainspotting",                  0.87)
    , (u"Snatch",                         0.85)
    , (u"Crank",                          0.75)
    , (u"Fight Club",                     0.85)
    , (u"American History X",             0.20)
    , (u"Forrest Gump",                   0.30)
    , (u"WALL·E",                         0.40)
    , (u"Reservoir Dogs",                 0.83)
    , (u"Sin City",                       0.95)
    , (u"Donnie Darko",                   0.85)
    , (u"Memento",                        0.8)
    , (u"Pretty Woman",                   0.2)
    , (u"Van Helsing",                    0.7)
    , (u"Underworld",                     0.65)
    , (u"300",                            0.85)
    , (u"The Illusionist",                0.8)
    , (u"Godzilla",                       0.3)
    , (u"Fantastic Four",                 0.6)
    , (u"Brothers Grimm",                 0.75)
    , (u"True Romance",                   0.75)
    , (u"Chocolat",                       0.2)
    , (u"Dirty Dancing",                  0.2)
]
# maximal number of book matches for a keyword
MAX_BOOK_MATCHES = 2
# movies must have at least this fitness to be downloaded
MINIMUM_MOVIE_FITNESS = 0.6


class HashFile(dict):
    """
    A dict that can be written/read from a file.
    """
    
    def __init__(self, path):
        dict.__init__(self)
        self.path = path
        self.read_dict()
    
    def read_dict(self):
        """
        read dict from file.
        """
        
        if not path.isfile(self.path):
            #create file
            f = open(self.path, "w")
            f.write(pickle.dumps({}))
            f.close()
            return self
        # open file for reading
        f = open(self.path, "r")
        # convert str to dict
        d = pickle.loads(f.read())
        f.close()
        
        # load parsed dict
        for k in d.keys():
            self[k] = d[k]
    
    def write_dict(self):
        """
        write dict from file.
        """
        
        # open file for writing
        f = open(self.path, "w")
        # convert dict to str
        f.write(pickle.dumps(self) + "\n")
        f.close()


class MovieFeed(Feed):
    """
    a feed that uses a knowledge base and imdb for rating videos in the feed.
    """
    
    # initialled flag
    initialled = False
    
    def __init__(self, id_file, url, n_weeks, n_items):
        if not MovieFeed.initialled:
            MovieFeed.read_book()
            MovieFeed.known_movies = HashFile(\
                path.expanduser("~") + "/.torrent_downloader_movies")
            MovieFeed.loaded_movies = {}
            MovieFeed.load_rated_movies()
            MovieFeed.initialled = True
        Feed.__init__(self, id_file, url, n_weeks, n_items)
    
    @staticmethod
    def alphanum_words(string):
        """
        replaces all no alpha-numerical chars with ' '
        """
        def match(c):
            if c.isalnum() : return c
            else           : return ' '
        return ("".join(map(match, string))).split() 
    
    @staticmethod
    def read_book():
        """
        read some english literature, counting words.
        """
        
        book_str = BOOK
        
        MovieFeed.book_words = {}
        book_words = {}
        for word in MovieFeed.alphanum_words(book_str):
            if book_words.has_key(word):
                book_words[word] += 1
            else:
                book_words[word]  = 1
        book_words = filter(lambda (key,val): val>1,
            zip(book_words.keys(), book_words.values()))
        for (word,val) in book_words:
            MovieFeed.book_words[word] = val
    
    @staticmethod
    def load_rated_movies():
        """
        load data of rated videos.
        """
        fileChanged = False
        loaded_movies = {}
        
        # Create the object that will be used to access the IMDb's database.
        MovieFeed.ia = IMDb() # by default access the web.
        MovieFeed.genre_ranking = {}
        
        for (movie,rating) in KNOWLEDGE_BASE:
            if MovieFeed.known_movies.has_key(movie):
                # retrieved data before
                known_movie = MovieFeed.known_movies[movie]
                known_movie['rating'] = rating
            else:
                print "Loading data about '" + movie + "' from imdb..."
                
                # load imdb_movie
                imdb_movie = MovieFeed.get_imdb_movie(movie)
                if imdb_movie == None:
                    print "movie not found, skipping."
                    continue
                try:
                    MovieFeed.ia.update(imdb_movie)
                except:
                    print "Failed to load imdb movie for " + movie
                    continue
                loaded_movies[imdb_movie.movieID] = imdb_movie
                
                known_movie = {'rating': rating, 'id': imdb_movie.movieID}
                
                # load keys
                for key in ['genres', 'writer', 'cast', 'producer', 'plot']:
                    if imdb_movie.has_key(key):
                        known_movie[key] = imdb_movie[key]
                    else:
                        known_movie[key] = []
                
                # load recommend movies
                print "Loading recommend movies (this may take a while) ..."
                try:
                    recommend = MovieFeed.ia.get_movie_recommendations(imdb_movie.movieID)
                    recommend = recommend['data']['recommendations']['database'][:4]
                except:
                    recommend = []
                for key in ['recommend_writer', 'recommend_cast', 'recommend_producer', 'recommend_plot']:
                    known_movie[key] = []
                for movieID in recommend:
                    movieID = str(movieID)
                    if loaded_movies.has_key(movieID):
                        recommend_movie = loaded_movies[movieID]
                    else:
                        recommend_movie = MovieFeed.ia.search_movie(movieID)[0]
                        try:
                            MovieFeed.ia.update(recommend_movie)
                        except:
                            print "Failed to load imdb movie for " + movieID
                            continue
                        loaded_movies[movieID] = recommend_movie
                    for key in ['writer', 'cast', 'producer', 'plot']:
                        if recommend_movie.has_key(key):
                            known_movie["recommend_" + key] += recommend_movie[key][:2]
                
                # format data
                for key in ['recommend_writer', 'recommend_cast', 'recommend_producer',
                            'writer', 'cast', 'producer']:
                    known_movie[key] = map(lambda x: x['name'], known_movie[key])
                for key in ['recommend_plot', 'plot']:
                    if known_movie[key] != []:
                        plotStr = ""
                        for i in range(len(known_movie[key])):
                            trunc = re.findall(r'(.+)::(?=.+)', known_movie[key][i])
                            if trunc != []:
                                plotStr += " " + trunc[0]
                            else:
                                plotStr += " " + known_movie[key][i]
                        known_movie[key] = [plotStr]
                print "movie loaded."
                
                # remember movie
                MovieFeed.known_movies[movie] = known_movie
                fileChanged = True
            
            # remember genre ranking
            genres = known_movie['genres']
            for genre in genres:
                if not MovieFeed.genre_ranking.has_key(genre):
                    MovieFeed.genre_ranking[genre] = [rating]
                else:
                    MovieFeed.genre_ranking[genre].append(rating)
        
        if fileChanged:
            # save the movie file if needed
            MovieFeed.known_movies.write_dict()
        
        # calculate genre fitness by calculating the average value
        for key in MovieFeed.genre_ranking.keys():
            ranking = MovieFeed.genre_ranking[key]
            MovieFeed.genre_ranking[key] = sum(ranking)/float(len(ranking))
        
        # calculate keyword fitness
        MovieFeed.keyword_ranking = {}
        word_ranking = {}
        for movie_key in MovieFeed.known_movies.keys():
            known_movie = MovieFeed.known_movies[movie_key]
            if known_movie['plot'] == []:
                continue
            plot_words = filter(lambda word: word[0].islower(),
                                MovieFeed.alphanum_words(known_movie['plot'][0]))
            recommend_plot_words = filter(lambda word: word[0].islower(),
                                MovieFeed.alphanum_words(known_movie['recommend_plot'][0]))
            for word in plot_words:
                if MovieFeed.book_words.has_key(word) and MovieFeed.book_words[word]>=MAX_BOOK_MATCHES:
                    continue
                if word_ranking.has_key(word):
                    word_ranking[word].append(known_movie['rating'])
                else:
                    word_ranking[word] = [known_movie['rating']]
            for word in recommend_plot_words:
                if MovieFeed.book_words.has_key(word) and MovieFeed.book_words[word]>=MAX_BOOK_MATCHES:
                    continue
                if word_ranking.has_key(word):
                    word_ranking[word].append(known_movie['rating']*0.95)
                else:
                    word_ranking[word] = [known_movie['rating']*0.95]
        word_ranking = filter(lambda (key,val): len(val)>1,
            zip(word_ranking.keys(), word_ranking.values()))
        word_ranking.sort(lambda x,y: len(y[1])-len(x[1]))
        for (word,vals) in word_ranking:
            MovieFeed.keyword_ranking[word] = sum(vals)/float(len(vals))
    
    @staticmethod
    def get_imdb_movie(title):
        """
        retrieve movie data from imdb.
        """
        
        if MovieFeed.known_movies.has_key(title):
            return MovieFeed.known_movies[title]
        if MovieFeed.loaded_movies.has_key(title):
            return MovieFeed.loaded_movies[title]
        
        try:
            matches = MovieFeed.ia.search_movie(title)
        except:
            return None
        if matches == []:
            # no entry found!
            return None
        
        # using levenshtein for getting the most similar result
        levenshtein_best = None
        for match in matches:
            lev = ratio(title, match['title'])
            if levenshtein_best == None:
                levenshtein_best = (match, lev)
            elif lev>levenshtein_best[1]:
                levenshtein_best = (match, lev)
        
        if levenshtein_best == None:
            print "No imdb entry found for: '" + title + "'"
            return None
        elif levenshtein_best[1] < 0.7:
            print "Skipping best imdb hit for '" + title + "' ('"\
                + str(levenshtein_best[0]) + "') with fitness " + str(levenshtein_best[1])
            return None
        
        print "'" + title + \
            "' might be imdb movie '" + \
            levenshtein_best[0]['title'] + "'"
        
        MovieFeed.loaded_movies[title] = levenshtein_best[0]
        
        return levenshtein_best[0]
    
    @staticmethod
    def get_imdb_persons(imdb_movie, key):
        """
        returns list of names from imdb person list at key.
        """
        return map(lambda x: x['name'], imdb_movie[key])
    
    @staticmethod
    def get_known_imdb_persons(key, person_limit=6):
        """
        returns list of known persons with rating.
        """
        known_persons = []
        for movie in MovieFeed.known_movies.keys():
            if not MovieFeed.known_movies[movie].has_key(key):
                continue
            
            rating = MovieFeed.known_movies[movie]['rating']
            known_persons.append(\
                (MovieFeed.known_movies[movie][key][:person_limit], rating))
            known_persons.append(\
                (MovieFeed.known_movies[movie]["recommend_" + key], rating*0.95))
            
        return known_persons
    
    def parse_title(self, item):
        """
        parses movie title from rss item.
        """
        if item.has_key('title'):
            if item['title'] != '':
                return item['title']
        return None
    
    def get_keyword_fitness(self, imdb_movie, movie_name):
        """
        returns fitness regarding frequently used words
        in favorite movie descriptions.
        """
        if not imdb_movie.has_key('plot') or imdb_movie['plot'] == []:
            return 0.1
        plot_words = filter(lambda word: word[0].islower(),
                            MovieFeed.alphanum_words(imdb_movie['plot'][0]))
        vals = []
        for word in plot_words:
            if MovieFeed.keyword_ranking.has_key(word):
                vals.append(MovieFeed.keyword_ranking[word])
        
        if vals == []:
            return MINIMUM_MOVIE_FITNESS
        else:
            return sum(vals)/float(len(vals))
    
    def get_imdb_fitness(self, imdb_movie):
        """
        returns fitness regarding the imdb rating
        in favorite movie descriptions.
        """
        try:
            votes = self.ia.get_movie_vote_details(imdb_movie.movieID)['data']
        except:
            return MINIMUM_MOVIE_FITNESS
        if not votes.has_key('rating'):
            return 0.3
        else:
            return votes['rating']/10.0
    
    def get_year_fitness(self, imdb_movie, min_year_diff=20.0):
        """
        returns a firness value for the year of the movie.
        """
        if imdb_movie.has_key('year'):
            movie_year = int(imdb_movie['year'])
        else:
            return 0.2
        d = (datetime.datetime.now().year-movie_year)/min_year_diff
        if d < 0.0: d = 0.7
        if d > 1.0: d = 1.0
        return 1.0-d
    
    def get_genre_fitness(self, imdb_movie):
        """
        returns fitness for movie genre.
        only returns!=0.3 if a genre is known
        from a favorite movie.
        """
        if not imdb_movie.has_key('genres'):
            return 0.1
        
        vals = []
        for genre in imdb_movie['genres']:
            if not MovieFeed.genre_ranking.has_key(genre):
                vals.append(0.3)
            else:
                vals.append(MovieFeed.genre_ranking[genre])
        if vals != []:
            return sum(vals)/float(len(vals))
        else:
            # no genre specified
            return 0.2
    
    def get_person_fitness(self, persons, known_persons, (movie, key)):
        """
        returns fitness for some persons.
        from a rated movie.
        """
        vals = []
        for p in persons:
            for (known,rating) in known_persons:
                if known.count(p)>0:
                    vals.append(rating)
        if vals != []:
            fitness = sum(vals)/float(len(vals))
            return fitness
        else:
            return 0.2
    
    def get_production_fitness(self, imdb_movie, movie_name):
        """
        returns fitness for movie production.
        from a rated movie.
        """
        if imdb_movie.has_key('producer'):
            producer = MovieFeed.get_imdb_persons(imdb_movie, 'producer')
        else:
            return 0.1
        known_producer = MovieFeed.get_known_imdb_persons('producer', 2)
        return self.get_person_fitness(producer, known_producer, (movie_name, 'producer'))
    
    def get_actor_fitness(self, imdb_movie, movie_name):
        """
        returns fitness for movie cast.
        from a rated movie.
        """
        if imdb_movie.has_key('cast'):
            actors = MovieFeed.get_imdb_persons(imdb_movie, 'cast')
        else:
            return 0.1
        known_actors = MovieFeed.get_known_imdb_persons('cast', 6)
        return self.get_person_fitness(actors, known_actors, (movie_name, 'cast'))
    
    def get_writer_fitness(self, imdb_movie, movie_name):
        """
        returns fitness for movie cast.
        only returns!=0.3 if a writer is known
        from a rated movie.
        """
        if imdb_movie.has_key('writer'):
            writer = MovieFeed.get_imdb_persons(imdb_movie, 'writer')
        else:
            return 0.1
        known_writer = MovieFeed.get_known_imdb_persons('writer', 2)
        return self.get_person_fitness(writer, known_writer, (movie_name, 'writer'))
    
    def get_item_id(self, item):
        title = self.parse_title(item)
        if title == None: return None
        try:
            imdb_movie = self.get_imdb_movie(title)
        except:
            return None
        if imdb_movie == None: return None
        self.ia.update(imdb_movie)
        # get movie name
        if imdb_movie.has_key('long imdb canonical title'):
            return imdb_movie['long imdb canonical title']
        else:
            return str(imdb_movie)
    
    def filter(self, items):
        """
        filter out movies with bad user rating.
        rating is calculated by set of user rated movies.
        FIXME: multiple matches with same name, wich to use?
        """
        
        rss_data = map(lambda i: (self.parse_title(i),\
                                  self.get_torrents(i)), items)
        imdb_data = []

        # get imdb data
        for (title,torrents) in rss_data:
            if title == None:
                # no title parsed
                continue
            imdb_movie = self.get_imdb_movie(title)
            if imdb_movie == None:
                continue
            else:
                try:
                    self.ia.update(imdb_movie)
                except:
                    continue
                # skip none movies
                if not imdb_movie.has_key('kind') or imdb_movie['kind'] != 'movie':
                    continue
                # get movie name
                if imdb_movie.has_key('long imdb canonical title'):
                    movie_name = imdb_movie['long imdb canonical title']
                else:
                    movie_name = str(imdb_movie)
                # get movie fitness
                fitness = (0.25*self.get_year_fitness(imdb_movie)
                         + 1.50*self.get_keyword_fitness(imdb_movie, movie_name)
                         + 1.75*self.get_genre_fitness(imdb_movie)
                         + 2.00*self.get_production_fitness(imdb_movie, movie_name)
                         + 2.00*self.get_actor_fitness(imdb_movie, movie_name)
                         + 4.00*self.get_imdb_fitness(imdb_movie)
                         + 2.25*self.get_writer_fitness(imdb_movie, movie_name))/13.75
                print title + " = " + str(fitness)
                
                # only download movies with good fitness
                if fitness >= MINIMUM_MOVIE_FITNESS:
                    imdb_data.append((movie_name, torrents))
        
        return imdb_data
