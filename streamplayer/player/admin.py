from django.contrib import admin
from .models import Film, Playlist, Stream, PlaylistFilm
# Register your models here.

class PlaylistFilmInline(admin.TabularInline):
    model = PlaylistFilm

@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'video', 'subtitle')

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', "repeat",'get_films_count')
    inlines = [PlaylistFilmInline]

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')