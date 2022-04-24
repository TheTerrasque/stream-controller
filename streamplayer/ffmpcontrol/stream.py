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

    def get_cmd(self, video: "Film"):

        def get_audiofilters():
            af = []

            # Normalize volume
            af.append("loudnorm=I=-16:LRA=11:TP=-1.5")

            return ",".join(af)


        def get_videofilters():
            vf = []

            # To suppport 10bit hevc : https://github.com/donmelton/other_video_transcoding/issues/73
            vf.append("format=yuv420p")

            # Scale video to 1080p if larger
            vf.append("scale=min'(1280,iw)':-2")
            
            if video.get_subtitle_string():
                vf.append(f"{video.get_subtitle_string()}")

            return ",".join(vf)

        args = [
            self.ffmpeg, 
            "-copyts", 
            "-re", # realtime playback
            "-i", video.get_path(), 
            "-vcodec", "libx264",
            "-vprofile", "baseline", 
            "-g", "30", 
            "-acodec", "aac",         
            "-strict", "-2", 
            "-ac", "2",
            "-f", "flv",            
            "-vf", get_videofilters(),
            "-af", get_audiofilters(),
            self.stream_path
            ]
        return args

    def stream_file(self, video):
        self.stop()
        cmd = self.get_cmd(video)
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