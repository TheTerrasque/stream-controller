To run (docker):
    1. Follow instructions in "docker/get-ffmpeg.txt" for Docker
    2. Run "docker compose up"
    3. Visit http://localhost:8082

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