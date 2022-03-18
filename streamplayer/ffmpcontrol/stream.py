from typing import List
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player.models import Film

class FFMPEG_STREAMER:
    ARGS_OUTPUT = ["-vcodec", "libx264",
            "-vprofile", "baseline", 
            "-g", "30", 
            "-acodec", "aac",         
            "-strict", "-2", 
            "-ac","2",
            # To suppport 10bit hevc : https://github.com/donmelton/other_video_transcoding/issues/73
            "-vf", "format=yuv420p,scale=min'(1280,iw)':-2",
            "-f", "flv",
            # Normalize volume
            "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
            #"-af", "loudnorm"
            ]

    process = None

    def __init__(self, ffmpeg_path: str, stream_path: str):
        self.ffmpeg = ffmpeg_path
        self.stream_path = stream_path

    def stream_file(self, video):
        self.stop()
        args = self.ARGS_OUTPUT.copy()

        if video.get_subtitle_string():
            args[13] = args[13] +  f",{video.get_subtitle_string()}"
            
        url = self.stream_path
        cmd = [
            self.ffmpeg, 
            "-copyts", 
            "-re", 
            "-i", 
            video.get_path(), 
        ]
        cmd.extend(args)
        cmd.append(url)
        self.process = subprocess.Popen(cmd)
        return self.process
    
    def is_playing(self):
        return self.process and self.process.poll() == None

    def stop(self):
        if self.is_playing():
            self.process.kill()
            outs, errs = self.process.communicate()

    def wait(self):
        return self.process.communicate()