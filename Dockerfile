FROM python:3.10-slim
WORKDIR /app

RUN apt-get -y update && apt-get -y upgrade && apt-get install -y fontconfig fonts-dejavu nginx curl && apt-get clean

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml /app/pyproject.toml

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml
COPY docker/ffmpeg /app/ffmpeg
COPY docker/ffprobe /app/ffprobe
COPY streamplayer/ /app/

COPY docker/supervisord.conf.docker /app/supervisord.conf
COPY docker/gunicorn.conf.py /app/gunicorn.conf.py
COPY docker/nginx.conf /app/nginx.conf

COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

RUN python manage.py collectstatic

ENV FFMPEG_PATH=/app/ffmpeg
ENV FFPROBE_PATH=/app/ffprobe
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["/app/start.sh"]