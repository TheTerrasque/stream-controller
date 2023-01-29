from .stream import FFMPEG_STREAMER
from threading import Thread
import time
import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from player.models import Stream, Playlist

class Player:
    playlist: "Playlist" = None
    films = []
    active_film_index = 0
    next_film_index = 0

    def __init__(self, stream: "Stream", streamer: FFMPEG_STREAMER = None) -> None:  # type: ignore
        if streamer:
            self.streamer = streamer
        else:
            self.streamer = FFMPEG_STREAMER(stream)
            
        self.stream = stream
        self.worker = Thread(target=self.threadloop)
        self.worker.daemon = True
        self.worker.start()

    def get_next(self):
        if not self.playlist:
            return None
        if self.next_film_index == None:
            if self.playlist.linked_to:
                self.play_playlist(self.playlist.linked_to)
                return self.get_next()
            return None
        self.active_film_index = self.next_film_index
        if self.next_film_index + 1 < len(self.films):
            self.next_film_index += 1
        else:
            self.next_film_index = None
        return self.films[self.active_film_index]

    def stop(self):
        self.streamer.stop()
        self.playlist = None
        self.films = []
        self.active_film_index = 0
        self.next_film_index = 0

    def get_active_movie(self):
        if not self.films:
            return None
        if not self.streamer.is_playing():
            return None
        return self.films[self.active_film_index]

    def update_streamer_info(self, stream: "Stream"):
        self.stream = stream
        self.streamer.stream = stream

    def threadloop(self):
        while True:
            try:
                if not self.streamer.is_playing():
                    if self.playlist:
                        next = self.get_next()
                        if next:
                            logger.info("Got next: %s" % next.video)
                            self.streamer.stream_file(next)
                time.sleep(0.5)
            except Exception as e:
                logger.warning("Player thread exception", e)
                time.sleep(5)

    def play_playlist(self, playlist, startfilm=None):
        self.playlist = playlist
        print("Playing playlist", playlist.name)
        self.films = list(playlist.get_films())
        print("Got films", self.films)
        
        if startfilm:
            self.active_film_index = self.films.index(startfilm)
            self.next_film_index = self.films.index(startfilm)
        else:
            self.active_film_index = 0
            self.next_film_index = 0
        try:
            self.streamer.stop()
        
        except Exception as e:
            logger.warning("Exception", e)
