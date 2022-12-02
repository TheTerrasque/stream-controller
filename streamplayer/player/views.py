from django.http import JsonResponse
from django.shortcuts import render
from player.models import Stream, Playlist, Film
from django.shortcuts import redirect
# import django user model
from django.contrib.auth.models import User
from .forms import NewAdminAccountForm
# import login_required
from django.contrib.auth.decorators import login_required
# Create your views here.

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
        "stop_url": stream.get_stop_url}
    if (player.playlist):
        data['player'] = {
            'playlist': player.playlist.name,
            'active_movie': player.get_active_movie,
        }
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