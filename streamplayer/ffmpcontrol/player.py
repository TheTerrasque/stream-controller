from .stream import FFMPEG_STREAMER
from threading import Thread
import time
import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from player.models import Stream, Playlist

if TYPE_CHECKING:
    from player.models import Film

class Player:
    playlist: "Playlist" = None
    films = []
    active_film_index = 0
    next_film_index = 0
    current_film_start_time = 0

    # Queue for "play after current" feature
    queued_playlist: "Playlist" = None
    queued_start_film: "Film" = None

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
        self.queued_playlist = None
        self.queued_start_film = None

    def queue_playlist(self, playlist: "Playlist", startfilm: "Film" = None):
        """Queue a playlist to start after the current film finishes."""
        self.queued_playlist = playlist
        self.queued_start_film = startfilm
        logger.info("Queued playlist: %s (start film: %s)", playlist.name, startfilm)

    def clear_queue(self):
        """Clear the queued playlist."""
        self.queued_playlist = None
        self.queued_start_film = None

    def get_queued_info(self):
        """Return info about the queued playlist for API responses."""
        if not self.queued_playlist:
            return None
        return {
            "playlist": self.queued_playlist.name,
            "playlistId": self.queued_playlist.id,
            "startFilm": str(self.queued_start_film) if self.queued_start_film else None,
            "startFilmId": self.queued_start_film.id if self.queued_start_film else None,
        }

    def get_active_movie(self) -> Optional["Film"]:
        if not self.films:
            return None
        if not self.streamer.is_playing():
            return None
        return self.films[self.active_film_index]

    def get_active_movie_time(self):
        if not self.streamer.is_playing():
            return 0
        played = time.time() - self.current_film_start_time
        total = self.get_active_movie().video_length()
        return {"played": played, "total": total}

    def update_streamer_info(self, stream: "Stream"):
        self.stream = stream
        self.streamer.stream = stream

    def threadloop(self):
        while True:
            try:
                if not self.streamer.is_playing():
                    # Check if something is queued - takes priority
                    if self.queued_playlist:
                        logger.info("Starting queued playlist: %s", self.queued_playlist.name)
                        queued = self.queued_playlist
                        startfilm = self.queued_start_film
                        self.queued_playlist = None
                        self.queued_start_film = None
                        self.play_playlist(queued, startfilm)
                    elif self.playlist:
                        next = self.get_next()
                        if next:
                            logger.info("Got next: %s" % next.video)
                            self.streamer.stream_file(next)
                            self.current_film_start_time = time.time()
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
