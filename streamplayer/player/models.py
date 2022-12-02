from collections import defaultdict
import json
from typing import Union
from django.db import models
from ffmpcontrol.player import Player
from os.path import basename
from django.urls import reverse
# Create your models here.
import logging
import os

from ffmpcontrol.stream import FFMPEG_TOOLS
logger = logging.getLogger(__name__)

class FilmStream(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    film = models.ForeignKey('Film', on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    language = models.CharField(max_length=255, default="")
    title = models.CharField(max_length=255, default="")

    def __str__(self):
        return f"[{self.language}] {self.title} [{self.name}]"

class Film(models.Model):
    video = models.FileField(upload_to='videos')
    name = models.CharField(max_length=255, blank=True)
    subtitle = models.FileField(upload_to='subtitles', blank=True, null=True, help_text="External Subtitle file")
    font_size = models.PositiveIntegerField(default=30)
    videodata = models.JSONField(blank=True, null=True)

    audio_stream = models.ForeignKey('FilmStream', on_delete=models.CASCADE, blank=True, null=True, limit_choices_to={'type': 'audio'}, related_name="+", help_text="Audio Stream")
    subtitle_stream = models.ForeignKey('FilmStream', on_delete=models.CASCADE, blank=True, null=True, limit_choices_to={'type': 'subtitle'}, related_name="+", help_text="Embedded subtitle track")

    def delete(self, *args, **kwargs):
        if self.video:
            os.remove(self.video.path)
        if self.subtitle:
            os.remove(self.subtitle.path)
        super().delete(*args, **kwargs)

    def get_movie_data(self):
        vdraw = FFMPEG_TOOLS.get_file_info(self.get_path())
        data = json.loads(vdraw)
        self.videodata = data
        FilmStream.objects.filter(film=self).delete()
        streamindex = defaultdict(int)

        for stream in data['streams']:
            print(stream)
            FilmStream.objects.create(
                name=stream['codec_name'],
                type=stream['codec_type'],
                film=self,
                index=streamindex[stream['codec_type']],
                language=stream['tags']['language'] if 'language' in stream['tags'] else "",
                title=stream['tags']['title'] if 'title' in stream['tags'] else ""
            )
            streamindex[stream['codec_type']] += 1
        self.save()

    def get_path(self):
        return self.video.path

    def __str__(self):
        return self.name or basename(self.video.name)

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
    repeat = models.BooleanField(default=False)
    films = models.ManyToManyField(Film, through=PlaylistFilm)
    active = models.BooleanField(default=True)

    def is_active(self):
        return self.active and self.get_films().exists()

    def get_films(self):
        return self.films.all()

    def get_films_count(self):
        self.get_films().count()

    def __str__(self):
        return self.name

STREAMPLAYERS = {}

class Stream(models.Model):
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True)
    active_playlist = models.ForeignKey(Playlist, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=False)
    order = models.IntegerField(default=100)

    class Meta:
        ordering = ['order']

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
        return STREAMPLAYERS[self.id] # type: ignore


from django.db.models.signals import post_save
from django.dispatch import receiver
# method for updating
@receiver(post_save, sender=Film, dispatch_uid="update_stock_count")
def update_film_data(sender, instance: Film, **kwargs):
    if kwargs['created']:
        instance.get_movie_data()