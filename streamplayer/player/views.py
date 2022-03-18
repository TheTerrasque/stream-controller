from django.shortcuts import render
from django.views.generic import ListView
from player.models import Stream, Playlist, Film
from django.shortcuts import redirect
# Create your views here.

def streams(request):
    stream = Stream.objects.first()
    if stream:
        return redirect(stream)
    return render(request, 'streamplayer/nostream.html')

def stream(request, stream_id):
    stream = Stream.objects.get(pk=stream_id)
    streams = Stream.objects.all()
    playlists = Playlist.objects.all()
    return render(request, 'streamplayer/stream.html', {'activestream': stream, 'playlists': playlists, 'streams': streams})

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