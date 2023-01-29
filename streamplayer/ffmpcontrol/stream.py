from typing import List
import subprocess
from typing import TYPE_CHECKING
from django.conf import settings


if TYPE_CHECKING:
    from player.models import Film, Stream

VIDEO_CODECS = ["libx264", "libx265", "libvpx-vp9"]
AUDIO_CODECS = ["aac", "libmp3lame", "libopus"]
VIDEO_PROFILES = ["baseline", "main", "high", "high10", "high422", "high444"]
VIDEO_TUNES = ["Off", "film", "animation", "grain", "stillimage", "psnr", "ssim", "fastdecode", "zerolatency"]
ENCODING_PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
OUTPUT_FORMATS = ["flv", "mp4", "webm"]

class FFMPEG_TOOLS:
    @staticmethod
    def get_file_info(path: str):
        cmd  = [settings.FFPROBE_PATH, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        outs, errs = proc.communicate()
        return outs.decode("utf-8")

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

    def __init__(self, stream: "Stream"):
        self.ffmpeg = settings.FFMPEG_PATH
        self.stream = stream

    def get_cmd(self, video: "Film"):

        def get_audiofilters():
            af = []

            # Normalize volume
            if (video.volume_normalization == "d" and self.stream.settings.normalize_volume) or video.volume_normalization == "on":
                af.append("loudnorm=I=-16:LRA=11:TP=-1.5")

            if af:
                return ["-af", ",".join(af)]
            return []


        def get_videofilters():
            vf = []

            # To suppport 10bit hevc : https://github.com/donmelton/other_video_transcoding/issues/73
            if video.workaround_for_10bit_hevc:
                vf.append("format=yuv420p")

            # Scale video to 1080p if larger
            if self.stream.settings.reduce_scale:
                vf.append("scale=min'(%s,iw)':-2" % self.stream.settings.reduce_scale)
            
            if video.get_subtitle_string():
                vf.append(f"{video.get_subtitle_string()}")

            if vf:
                return ["-vf", ",".join(vf)]
            return []

        def get_maps():
            maps = []
            
            # Audio
            if video.audio_stream:
                maps.extend(("-map", "0:v:0"))
                maps.extend((f"-map", f"0:a:{video.audio_stream.index}"))

            return maps

        def get_tune():
            if video.video_tune_override != "Off":
                return ("-tune", video.video_tune_override)
            if self.stream.settings.video_tune == "Off":
                return []
            else:
                return ("-tune", self.stream.settings.video_tune)

        args = [
            self.ffmpeg, 
            "-copyts", 
            "-re", # realtime playback
            "-i", video.get_path(), 
            "-crf", str(self.stream.settings.crf),
            "-preset", self.stream.settings.encoding_preset,
            "-maxrate", str(self.stream.settings.video_max_bitrate) + "k",
            "-bufsize", str(self.stream.settings.video_buffer_size) + "k",
            "-vcodec", self.stream.settings.video_codec,
            "-vprofile", self.stream.settings.video_profile, 
            "-g", str(self.stream.settings.keyframe_interaval), 
            "-acodec", self.stream.settings.audio_codec,
            *get_tune(),
            "-strict", "-2", 
            "-ac", str(self.stream.settings.audio_channels),
            "-b:a", str(self.stream.settings.audio_bitrate) + "k",
            "-f", self.stream.settings.output_format,
            *get_maps(),
            *get_videofilters(),
            *get_audiofilters(),
            self.stream.url
            ]
        return args

    def stream_file(self, video: "Film"):
        self.stop()
        cmd = self.get_cmd(video)
        print("FFMPEG command:", " ".join(cmd))
        self.process = subprocess.Popen(cmd)
        return self.process
    
    def is_playing(self):
        return self.process and self.process.poll() == None

    def stop(self):
        if self.is_playing():
            self.process.kill() # type: ignore
            outs, errs = self.process.communicate() # type: ignore
