from typing import Optional
from django.contrib import admin
from .models import Film, Playlist, Stream, PlaylistFilm, FilmStream, StreamSetting
from django import forms
from django.utils.translation import gettext_lazy as _
# Register your models here.

class PlaylistFilter(admin.SimpleListFilter):
    title = _('Playlist')
    parameter_name = 'playlist'

    def lookups(self, request, model_admin):
        playlists = Playlist.objects.filter(films__isnull=False).distinct()
        return [(p.id, p.name) for p in playlists]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(playlist__id=self.value())
        return queryset

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
    list_filter = [PlaylistFilter]
    list_display = ('__str__', 'video', 'subtitle')
    fieldsets  = (
        (None, {"fields": ('video', "name")}),
        ('Subtitle', {'fields': ('subtitle', 'subtitle_stream','audio_stream', 'font_size')}),
        ('Misc', {'fields': ('workaround_for_10bit_hevc', 'video_tune_override', "volume_normalization", "special", "status")}),
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