from django.core.management.base import BaseCommand, CommandError
from player.models import Film
import time

class Command(BaseCommand):
    help = "Find a movie without file info and scan it"

    def handle(self, *args, **options):
        print("Starting scanning...")
        while True:
            film = Film.objects.filter(status="new").first()
            if film:
                print("Processing film: ", film)
                film.get_movie_data()
            time.sleep(5)