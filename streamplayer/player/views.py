from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from player.models import Stream, Playlist, Film
from .opensubtitles import OpenSubtitleApi
from .forms import FilmForm, NewAdminAccountForm
from django.conf import settings
from io import BytesIO

# Create your views here.

OPENSUBTITLES_API_KEY = getattr(settings, "OPENSUBTITLES_API_KEY", None)

def initial_account_setup(request):
    if User.objects.exists():
        return redirect("index")

    if request.method == "POST":
        form = NewAdminAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("index")
    else:
        form = NewAdminAccountForm()
    return render(request, 'streamplayer/initial_account_setup.html', {'form': form})

def index(request):
    if not User.objects.exists():
        return redirect("initial_account_setup")
    stream = Stream.objects.first()
    if stream:
        return redirect(stream)
    return redirect("nostream") 

@login_required
def nostream(request):
    return render(request, 'streamplayer/nostream.html')

@login_required
def stream(request, stream_id):
    stream = Stream.objects.get(pk=stream_id)
    streams = Stream.objects.all()
    playlists = Playlist.objects.all()
    return render(request, 'streamplayer/stream.html', {'activestream': stream, 'playlists': playlists, 'streams': streams})

@login_required
def stream_info(request, stream_id):
    stream: Stream = Stream.objects.get(pk=stream_id)
    player = stream.get_stream_player()
    data = {'name': stream.name, 
        'url': stream.url, 
        'link': stream.link,
        "player": None,
        "stopUrl": stream.get_stop_url()}
    if (player.playlist):
        data['player'] = {
            'activePlaylist': player.playlist.name,
            'activePlaylistId': player.playlist.id,
            'activeMovieTime': player.get_active_movie_time(),
        }
        if player.get_active_movie():
            data["player"]["activeMovie"] = player.get_active_movie().as_json()
    return JsonResponse(data)

@login_required
def stop(request, stream_id):
    stream: Stream = Stream.objects.get(pk=stream_id)
    stream.get_stream_player().stop()
    return redirect("stream", stream_id=stream_id)

@login_required
def play(request, stream_id):
    if request.method == "POST":
        stream: Stream = Stream.objects.get(pk=stream_id)
        playlist_id = request.POST.get('playlist')
        if playlist_id:
            playlist: Playlist = Playlist.objects.get(pk=playlist_id)
            fileid = request.POST.get('fileid')
            film = None
            if fileid:
                film = Film.objects.get(pk=fileid)
            stream.play_playlist(playlist, film)
    return redirect("stream", stream_id=stream_id)


@login_required
def upload_film(request):
    if request.method == "POST":
        form = FilmForm(request.POST, request.FILES)
        if form.is_valid():
            film = form.save()

            print("Film length: ", film.video_length())

            playlist = request.GET.get('playlist')
            if playlist:
                playlist = Playlist.objects.get(pk=playlist)
                playlist.add_film(film)

            if form.cleaned_data['guild_movie']:
                for playlist in Playlist.objects.filter(for_guild_movie=True):
                    playlist.clear()
                    for afilm in Film.objects.filter(special = "before_mainmovie"):
                        playlist.add_film(afilm)
                    playlist.add_film(film)
                    for afilm in Film.objects.filter(special = "after_mainmovie"):
                        playlist.add_film(afilm)
            return JsonResponse({'id': film.id, 
                                 "url": film.get_absolute_url(), 
                                 "name": str(film)})
    else:
        form = FilmForm()
    playlists = Playlist.objects.filter(active=True)
    return render(request, 'streamplayer/upload.html', {'form': form, "playlists": playlists})

@login_required
def film_info(request, film_id):
    film: Film = Film.objects.get(pk=film_id)
    return JsonResponse({'name': str(film), 'info': film.get_movie_data(), "subtitle": film.get_subtitle_string()}) 

@login_required
def film_info_page(request, film_id):
    film: Film = Film.objects.get(pk=film_id)
    return render(request, 'streamplayer/film_info.html', {'film': film, "subtitles_search": bool(OPENSUBTITLES_API_KEY)})

@login_required
def opensubtitle_find(request, film_id):
    film: Film = Film.objects.get(pk=film_id)
    if OPENSUBTITLES_API_KEY:
        opensubtitles = OpenSubtitleApi(OPENSUBTITLES_API_KEY)

        if request.GET.get("subtitleid"):
            subtitleid = request.GET.get("subtitleid")
            data = opensubtitles.download(subtitleid)
            if not data:
                return JsonResponse({"error": "No download link", "data" : data})
            film.add_subtitle_file(f"{subtitleid}_{data['file_name']}", BytesIO(data["content"]))
            return redirect(film.get_absolute_url())
        
        hash = opensubtitles.get_hash_for_file(film.video.path)
        if hash.error:
            return JsonResponse({"error": hash.error})
        data = opensubtitles.search(hash.hash, str(film), request.GET.get("imdb"))
        return JsonResponse(data)
    return JsonResponse({"error": "No api key"})