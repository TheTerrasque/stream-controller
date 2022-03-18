from typing import Union
from django.db import models
from ffmpcontrol.player import Player
from os.path import basename
from django.urls import reverse
# Create your models here.
import logging
import os
logger = logging.getLogger(__name__)

class Film(models.Model):
    video = models.FileField(upload_to='videos')
    subtitle = models.FileField(upload_to='subtitles', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True)
    use_subtitle_in_video = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        if self.video:
            os.remove(self.video.path)
        if self.subtitle:
            os.remove(self.subtitle.path)
        super().delete(*args, **kwargs)

    def get_path(self):
        return self.video.path

    def __str__(self):
        return self.name or basename(self.video.name)

    def get_subtitle_string(self):
        # subtitles='{subtitles}':force_style='FontName=ubuntu,Fontsize=30'
        if not self.subtitle and not self.use_subtitle_in_video:
            return ""
        if self.use_subtitle_in_video:
            subtitles = self.video.path.replace("\\", "/").replace(":", "\\:")
        else:
            subtitles = self.subtitle.path.replace("\\", "/").replace(":", "\\:")
        return f"subtitles='{subtitles}'"

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
    active_film = models.ForeignKey(Film, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    next_film = models.ForeignKey(Film, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    def get_films(self):
        return self.films.all()

    def get_films_count(self):
        self.get_films().count()

    def set_active_film(self, film):
        if self.active_film != film:
            self.active_film = film
            self.save()
        return film

    def find_next(self, film):
        films = list(self.get_films())

        if not film:
            return films[0]

        prev_film = None
        for f in films:
            if prev_film and prev_film.id == film.id:
                return f
            prev_film = f

        if self.repeat:
            return films[0]

        return None

    def set_next(self, film):
        self.next_film = film
        self.active_film = film
        self.save()

    def next(self) -> Union[Film, None]:
        film = self.next_film
        self.active_film = film
        self.next_film = self.find_next(film)
        self.save()
        return self.active_film

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
        if self.id in STREAMPLAYERS:
            return self.active_playlist

    def get_absolute_url(self):
        return reverse('stream', kwargs={'stream_id' : self.pk})

    def get_play_url(self):
        return reverse('play', kwargs={'stream_id' : self.pk})

    def play_playlist(self, playlist):
        self.get_stream_player().play_playlist(playlist)
        self.active_playlist = playlist
        self.save()

    def get_stream_player(self) -> Player:
        if not self.id in STREAMPLAYERS:
            self.active_playlist = None
            self.save()
            logger.info("Creating new streamplayer for %s" % self.name)
            STREAMPLAYERS[self.id] = Player(self)
        return STREAMPLAYERS[self.id]