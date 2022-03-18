FROM python:3.10-slim-buster

WORKDIR /app

RUN apt-get -y update && apt-get -y upgrade && apt-get install -y fontconfig ttf-dejavu && apt-get clean

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY streamplayer/ /app/
COPY docker/ffmpeg /app/ffmpeg
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh
ENV FFMPEG_PATH=/app/ffmpeg

EXPOSE 8000

CMD ["/app/start.sh"]