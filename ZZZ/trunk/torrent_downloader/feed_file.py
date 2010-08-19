
from os import path

# max n items will be cached as allready processed
N_CACHE = 1000

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
