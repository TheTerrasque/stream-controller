env vars:
    FFMPEG_PATH
    DJANGO_UPLOAD_FOLDER
    DJANGO_SQLITE_PATH
    DJANGO_SECRET
    DJANGO_ALLOWED_HOST
    SUBTITLE_DEFAULT_SIZE
    OPENSUBTITLES_API_KEY # https://www.opensubtitles.com/en/consumers

build:
    docker build . --push -t terrasque/streamcontrol:<ver>