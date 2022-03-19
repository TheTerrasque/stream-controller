from django.shortcuts import render
from player.models import Stream, Playlist, Film
from django.shortcuts import redirect
# import django user model
from django.contrib.auth.models import User
from .forms import NewAdminAccountForm
# Create your views here.

def initial_account_setup(request):
    if User.objects.exists():
        return redirect("streams")
        
    if request.method == "POST":
        form = NewAdminAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("streams")
    else:
        form = NewAdminAccountForm()
    return render(request, 'streamplayer/initial_account_setup.html', {'form': form})

def streams(request):
    if not User.objects.exists():
        return redirect("initial_account_setup")

    stream = Stream.objects.first()
    if stream:
        return redirect(stream)

    return render(request, 'streamplayer/nostream.html')

def stream(request, stream_id):
    stream = Stream.objects.get(pk=stream_id)
    streams = Stream.objects.all()
    playlists = Playlist.objects.all()
    return render(request, 'streamplayer/stream.html', {'activestream': stream, 'playlists': playlists, 'streams': streams})

def stop(request, stream_id):
    stream: Stream = Stream.objects.get(pk=stream_id)
    stream.get_stream_player().stop()
    return redirect("stream", stream_id=stream_id)

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
            playlist.set_next(film)
            stream.play_playlist(playlist)
    return redirect("stream", stream_id=stream_id)