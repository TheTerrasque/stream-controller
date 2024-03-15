from typing import Optional
from django.contrib import admin
from .models import Film, Playlist, Stream, PlaylistFilm, FilmStream, StreamSetting
from django import forms
# Register your models here.

class PlaylistFilmInline(admin.TabularInline):
    model = PlaylistFilm

class FilmForm(forms.ModelForm):
    class Meta:
        model = Film
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['audio_stream'].queryset = FilmStream.objects.filter(
                                        film_id=self.instance.id).filter(type='audio')
        self.fields['subtitle_stream'].queryset = FilmStream.objects.filter(
                                        film_id=self.instance.id).filter(type='subtitle').filter(name__in=["ass", "subrip"])
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    search_fields = ["video", "name"]
    list_filter = ["playlist_set__name"]
    list_display = ('__str__', 'video', 'subtitle')
    fieldsets  = (
        (None, {"fields": ('video', "name")}),
        ('Subtitle', {'fields': ('subtitle', 'subtitle_stream','audio_stream', 'font_size')}),
        ('Misc', {'fields': ('workaround_for_10bit_hevc', 'video_tune_override', "volume_normalization", "special")}),
    )
    form = FilmForm
                                     

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', "linked_to")
    inlines = [PlaylistFilmInline]

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')

@admin.register(StreamSetting)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name', 'video_codec')