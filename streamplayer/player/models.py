from collections import defaultdict
import json
from typing import Union
from django.db import models
from ffmpcontrol.player import Player
from os.path import basename
from django.urls import reverse
from django.conf import settings
# Create your models here.
import logging
import os

SUBTITLE_DEFAULT_SIZE = getattr(settings, "SUBTITLE_DEFAULT_SIZE", 23)

from ffmpcontrol.stream import FFMPEG_TOOLS, \
    VIDEO_CODECS, AUDIO_CODECS, VIDEO_PROFILES, \
    ENCODING_PRESETS, VIDEO_TUNES, OUTPUT_FORMATS
logger = logging.getLogger(__name__)

SPECIAL_VIDEOS = ["before_mainmovie", "after_mainmovie"]

class FilmStream(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    film = models.ForeignKey('Film', on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    language = models.CharField(max_length=255, default="")
    title = models.CharField(max_length=255, default="")
    # optional special choice for before_mainmovie, after_mainmovie, before_trailer, after_trailer
     

    def __str__(self):
        return f"[{self.language}] {self.title} [{self.name}]"

class Film(models.Model):
    video = models.FileField(upload_to='videos', max_length=255, help_text="Video file")
    name = models.CharField(max_length=255, blank=True)
    subtitle = models.FileField(upload_to='subtitles', blank=True, null=True, help_text="External Subtitle file", max_length=255)
    font_size = models.PositiveIntegerField(default=SUBTITLE_DEFAULT_SIZE, help_text="Subtitle font size")
    videodata = models.JSONField(blank=True, null=True)

    audio_stream = models.ForeignKey('FilmStream', on_delete=models.CASCADE, blank=True, null=True, limit_choices_to={'type': 'audio'}, related_name="+", help_text="Audio Stream")
    subtitle_stream = models.ForeignKey('FilmStream', on_delete=models.CASCADE, blank=True, null=True, limit_choices_to={'type': 'subtitle'}, related_name="+", help_text="Embedded subtitle track")

    workaround_for_10bit_hevc = models.BooleanField(default=False, help_text="Workaround for 10bit HEVC streams. Handles playback of them but might impact video quality.")
    video_tune_override = models.CharField(max_length=255, default="Off", choices=[(x, x) for x in VIDEO_TUNES])
    volume_normalization = models.CharField(default="d", help_text="Normalize audio volume", choices=[("d", "Stream Default"), ("yes", "On"), ("no", "Off")], max_length=5)
    special = models.CharField(max_length=255, blank=True, null=True, choices=[(x, x) for x in SPECIAL_VIDEOS]) 

    status = models.CharField(max_length=255, default="new", choices = [(x, x.capitalize()) for x in ("new", "scanning", "processed")])

    def as_json(self):
        return dict(
            id=self.id,
            name=str(self),
            video=self.video.name,
            subtitle=self.subtitle.name if self.subtitle else None,
            font_size=self.font_size,
            audio_stream=self.audio_stream.id if self.audio_stream else None,
            subtitle_stream=self.subtitle_stream.id if self.subtitle_stream else None,
            workaround_for_10bit_hevc=self.workaround_for_10bit_hevc,
            video_tune_override=self.video_tune_override,
            volume_normalization=self.volume_normalization,
            special=self.special,
            videodata=self.videodata
        )

    def add_subtitle_file(self, filename, content):
        self.subtitle.save(filename, content)

    def delete(self, *args, **kwargs):
        if self.video:
            os.remove(self.video.path)
        if self.subtitle:
            os.remove(self.subtitle.path)
        super().delete(*args, **kwargs)

    def video_length(self):
        if self.videodata:
            return float(self.videodata['format']['duration'])
        return 0

    def get_streams(self, type=None):
        if type:
            return self.filmstream_set.filter(type=type)
        return self.filmstream_set.all()

    def set_as_guild_movie(self):
        for playlist in Playlist.objects.filter(for_guild_movie=True):
            playlist.clear()
            for afilm in Film.objects.filter(special = "before_mainmovie"):
                playlist.add_film(afilm)
            playlist.add_film(self)
            for afilm in Film.objects.filter(special = "after_mainmovie"):
                playlist.add_film(afilm)

    def get_movie_data(self):
        self.status = "scanning"
        self.save()
        
        vdraw = FFMPEG_TOOLS.get_file_info(self.get_path())
        data = json.loads(vdraw)
        self.videodata = data
        FilmStream.objects.filter(film=self).delete()
        streamindex = defaultdict(int)
        main10 = False

        for stream in data['streams']:
            if stream.get('profile') == "Main 10" and stream.get('codec_name') == "hevc":
                main10 = True
            FilmStream.objects.create(
                name=stream['codec_name'],
                type=stream['codec_type'],
                film=self,
                index=streamindex[stream['codec_type']],
                language=stream['tags']['language'] if "tags" in stream and 'language' in stream['tags'] else "<Unknown>",
                title=stream['tags']['title'] if  "tags" in stream and 'title' in stream['tags'] else "<Untitled>"
            )
            streamindex[stream['codec_type']] += 1
        if main10:
            self.workaround_for_10bit_hevc = True
        self.status = "processed"
        self.save()

    def get_path(self):
        return self.video.path

    def __str__(self):
        return self.name or basename(self.video.name)

    def get_absolute_url(self):
        return reverse('film_info_page', kwargs={'film_id' : self.pk})

    def set_active_stream(self, stream_id):
        stream = FilmStream.objects.get(pk=stream_id, film=self)
        if stream.type == "audio":
            self.audio_stream = stream
            self.save()
        elif stream.type == "subtitle":
            self.subtitle_stream = stream
            self.save()

    def get_subtitle_name(self):
        if self.subtitle:
            return basename(self.subtitle.name)
        if self.subtitle_stream:
            return "Stream: " + self.subtitle_stream.title
        return ""
    
    def get_subtitle_string(self):
        # subtitles='{subtitles}':force_style='FontName=ubuntu,Fontsize=30'
        if not self.subtitle and not self.subtitle_stream:
            return ""
        if self.subtitle_stream:
            subtitles = self.video.path.replace("\\", "/").replace(":", "\\:")
        else:
            subtitles = self.subtitle.path.replace("\\", "/").replace(":", "\\:")
        substream = ""
        if self.subtitle_stream:
            substream = f":si={self.subtitle_stream.index}"
        return f"subtitles='{subtitles}':force_style='FontName=ubuntu,Fontsize={self.font_size}'" + substream

class PlaylistFilm(models.Model):
    playlist = models.ForeignKey('Playlist', on_delete=models.CASCADE)
    film = models.ForeignKey('Film', on_delete=models.CASCADE)
    order = models.IntegerField(default=100)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.playlist} - {self.film}"

class Playlist(models.Model):
    name = models.CharField(max_length=255)
    films = models.ManyToManyField(Film, through=PlaylistFilm)
    active = models.BooleanField(default=True)
    linked_to = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name="linked_from", help_text="If set, start playing linked playlist after this")
    for_guild_movie = models.BooleanField(default=False)

    def clear(self):
        self.films.clear()

    def is_active(self):
        return self.active and self.get_films().exists()

    def get_films(self):
        return self.films.all()

    def get_films_count(self):
        self.get_films().count()

    def add_film(self, film: Film):
        PlaylistFilm.objects.create(playlist=self, film=film)

    def __str__(self):
        return self.name

STREAMPLAYERS = {}

class StreamSetting(models.Model):
    name = models.CharField(max_length=255)
    video_codec = models.CharField(max_length=255, choices=[(x, x) for x in VIDEO_CODECS], default="libx264")
    audio_codec = models.CharField(max_length=255, choices=[(x, x) for x in AUDIO_CODECS], default="aac")
    reduce_scale = models.IntegerField(default="1280", help_text = "Reduce scale to this value if video is larger. Set to 0 to disable.")
    video_profile = models.CharField(max_length=255, default="baseline", choices=[(x, x) for x in VIDEO_PROFILES])
    encoding_preset = models.CharField(max_length=255, default="medium", choices=[(x, x) for x in ENCODING_PRESETS])
    crf = models.IntegerField(default=23, help_text="Constant Rate Factor (0-51, lower is better quality but higher bitrate)")
    audio_bitrate = models.IntegerField(default=192)
    video_max_bitrate = models.IntegerField(default=5000, help_text="Maximum video bitrate in kbps")
    video_buffer_size = models.IntegerField(default=10000, help_text="Video buffer size in kbps")
    video_tune = models.CharField(max_length=255, default="Off", choices=[(x, x) for x in VIDEO_TUNES])
    zero_latency = models.BooleanField(default=True, help_text="Optimization for fast encoding and low latency streaming")
    fast_decode = models.BooleanField(default=False, help_text="disables CABAC and the in-loop deblocking filter to allow for faster decoding on devices with lower computational power.")    
    normalize_volume = models.BooleanField(default=True)
    keyframe_interaval = models.IntegerField(default=30)
    output_format = models.CharField(max_length=255, default="flv", choices=[(x, x) for x in OUTPUT_FORMATS])
    audio_channels = models.IntegerField(default=2)
    
    def get_tunes(self, video_tune = None):
        tunes = []
        if not video_tune or video_tune == "Off":
            video_tune = self.video_tune
        if self.zero_latency:
            tunes.append("zerolatency")
        if self.fast_decode:
            tunes.append("fastdecode")
        if video_tune != "Off":
            tunes.append(video_tune)
        return tunes

    def __str__(self):
        return f"{self.name}"

class Stream(models.Model):
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True)
    active_playlist = models.ForeignKey(Playlist, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_for_streams')
    autostart_playlist = models.ForeignKey(Playlist, on_delete=models.SET_NULL, null=True, blank=True, related_name='autostart_for_streams', help_text="Playlist to automatically start playing on server startup")
    active = models.BooleanField(default=False)
    order = models.IntegerField(default=100)
    settings = models.ForeignKey(StreamSetting, on_delete=models.PROTECT)

    class Meta:
        ordering = ['order']

    def get_json_info_url(self):
        return reverse('stream-json', kwargs={'stream_id' : self.pk})

    def __str__(self):
        return self.name

    def get_active_playlist(self):
        if self.id in STREAMPLAYERS:  # type: ignore
            return self.active_playlist

    def get_absolute_url(self):
        return reverse('stream', kwargs={'stream_id' : self.pk})

    def get_stop_url(self):
        return reverse('stop', kwargs={'stream_id' : self.pk})

    def get_play_url(self):
        return reverse('play', kwargs={'stream_id' : self.pk})

    def play_playlist(self, playlist, film):
        self.get_stream_player().play_playlist(playlist, film)       

    def stop_playing(self):
        self.get_stream_player().stop()

    def get_stream_player(self) -> Player:
        if not self.id in STREAMPLAYERS:  # type: ignore
            self.active_playlist = None
            self.save()
            logger.info("Creating new streamplayer for %s" % self.name)
            STREAMPLAYERS[self.id] = Player(self)  # type: ignore
        else:
            STREAMPLAYERS[self.id].update_streamer_info(self)  # type: ignore
        return STREAMPLAYERS[self.id] # type: ignore


from django.db.models.signals import post_save
from django.dispatch import receiver
# method for updating
# @receiver(post_save, sender=Film, dispatch_uid="update_stock_count")
# def update_film_data(sender, instance: Film, **kwargs):
#     if kwargs['created']:
#         instance.get_movie_data()