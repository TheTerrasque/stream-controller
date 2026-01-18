To run (docker):
    1. Follow instructions in "docker/get-ffmpeg.txt" for Docker
    2. Run "docker compose up"
    3. Visit http://localhost:8082

To run locally (using uv):
    1. Install uv: https://docs.astral.sh/uv/getting-started/installation/
    2. Install dependencies: uv sync
    3. cd streamplayer
    4. Run migrations: uv run python manage.py migrate
    5. Run server: uv run python manage.py runserver
    6. Visit http://localhost:8000

In dev container (using uv + supervisord):
    1. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh
    2. Install dependencies: uv sync
    3. cd streamplayer
    4. supervisord -c ../docker/supervisord.conf.dev
    5. Alternatively, run the programs in supervisord.conf.dev manually in folder streamplayer

env vars:
    FFMPEG_PATH
    DJANGO_UPLOAD_FOLDER
    DJANGO_SQLITE_PATH
    DJANGO_SECRET
    DJANGO_ALLOWED_HOST
    SUBTITLE_DEFAULT_SIZE
    OPENSUBTITLES_API_KEY # https://www.opensubtitles.com/en/consumers

Adding an OIDC provider (e.g. Authentik, Keycloak):
    1. Go to Django Admin -> Social Applications -> Add
    2. Provider: OpenID Connect
    3. Provider ID: unique slug (e.g. "my-authentik")
    4. Name: Display name shown to users
    5. Client ID: from your OIDC provider
    6. Secret: from your OIDC provider
    7. Settings (JSON):
       {"server_url": "https://your-provider.com/application/o/your-app/"}
    8. Save

    For more settings, see: https://docs.allauth.org/en/latest/socialaccount/configuration.html

Local settings:
    Create streamplayer/streamplayer/local_settings.py to override Django settings.
    This file is imported at the end of settings.py and is gitignored.

build:
    docker build . --push -t terrasque/streamcontrol:<ver>