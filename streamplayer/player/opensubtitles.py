import struct
import os
from dataclasses import dataclass
import requests

@dataclass
class HashResult:
    hash: str
    error: str

class OpenSubtitleApi:
    def __init__(self, apikey, language = "en"):
        self.base_url = "https://api.opensubtitles.com/api/v1/"
        self.language = language
        self.apikey = apikey
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'GuildMovieStreamer v1'})
        self.session.headers.update({'Api-Key': self.apikey})

    def get_hash_for_file(self, path):
        try: 
            longlongformat = '<q'  # little-endian long long
            bytesize = struct.calcsize(longlongformat) 
                
            f = open(path, "rb") 
                
            filesize = os.path.getsize(path) 
            hash = filesize 
                
            if filesize < 65536 * 2: 
                return HashResult("", "SizeError")
                
            for x in range(int(65536/bytesize)):
                buffer = f.read(bytesize) 
                (l_value,)= struct.unpack(longlongformat, buffer)  
                hash += l_value 
                hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number  
                    
            f.seek(max(0,filesize-65536),0) 
            for x in range(int(65536/bytesize)): 
                buffer = f.read(bytesize) 
                (l_value,)= struct.unpack(longlongformat, buffer)  
                hash += l_value 
                hash = hash & 0xFFFFFFFFFFFFFFFF 
                
            f.close() 
            returnedhash =  "%016x" % hash 
            return HashResult(returnedhash, "")
    
        except(IOError): 
            return HashResult("", "IOError")
    
    def search(self, hash, filename="", imdb=""):
        params = {"languages": self.language, "moviehash": hash}
        if filename:
            params["query"] = filename
        if imdb:
            params["imdb_id"] = imdb
        return self.session.get(self.base_url + "subtitles", params=params).json()
    
    def download(self, id):
        data = self.session.post(self.base_url + "download", json={"file_id": id}).json()
        url = data.get("link")
        if not url:
            print(data)
            return None
        data["content"] =  self.session.get(url).content
        return data