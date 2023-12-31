"""streamplayer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from  . import views as V

urlpatterns = [
    path('', V.index, name='index'),
    path('nostream/', V.nostream, name='nostream'),
    path('new_account_setup', V.initial_account_setup, name='initial_account_setup'),
    path('stream/<int:stream_id>', V.stream, name='stream'),
    path('stream/<int:stream_id>.json', V.stream_info, name='stream-json'),
    path('stream/<int:stream_id>/play', V.play, name='play'),
    path('stream/<int:stream_id>/stop', V.stop, name='stop'),
    path('film/<int:film_id>.json', V.film_info, name='film_info'),
    path('film/<int:film_id>', V.film_info_page, name='film_info_page'),
    path('film/upload', V.upload_film, name='upload_film'),
    path('film/<int:film_id>/subtitle', V.opensubtitle_find, name='subtitle_find'),
]
