from .stream import FFMPEG_STREAMER
from threading import Thread
import time
import os
import logging
logger = logging.getLogger(__name__)

FFMPEG_EXE  = os.getenv("FFMPEG_PATH", r"F:\\ffmpeg-4.4-full_build\\bin\\ffmpeg.exe")

class Player:
    playlist = None

    def __init__(self, stream, streamer: FFMPEG_STREAMER = None) -> None:
        if streamer:
            self.streamer = streamer
        else:
            self.streamer = FFMPEG_STREAMER(FFMPEG_EXE, stream.url)
            
        self.stream = stream
        self.worker = Thread(target=self.threadloop)
        self.worker.daemon = True
        self.worker.start()

    def threadloop(self):
        while True:
            if not self.streamer.is_playing():
                if self.playlist:
                    next = self.playlist.next()
                    if next:
                        logger.info("Got next: %s" % next.video)
                        self.streamer.stream_file(next)
            time.sleep(0.5)

    def play_playlist(self, playlist):
        self.playlist = playlist
        try:
            self.streamer.stop()
        except Exception as e:
            logger.warning("Exception", e)


