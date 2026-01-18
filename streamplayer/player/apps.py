from django.apps import AppConfig
import sys
import logging

logger = logging.getLogger(__name__)


class PlayerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'player'

    def ready(self):
        # Only run autostart for actual server processes, not migrations/shell/etc.
        if not self._is_server_process():
            return

        from .models import Stream
        for stream in Stream.objects.filter(autostart_playlist__isnull=False):
            if stream.autostart_playlist.is_active():
                logger.info(f"Autostarting playlist '{stream.autostart_playlist}' on stream '{stream.name}'")
                stream.play_playlist(stream.autostart_playlist, None)

    def _is_server_process(self):
        """Check if we're running as a web server (runserver or gunicorn)."""
        if 'runserver' in sys.argv:
            return True
        # Check for gunicorn
        if sys.argv and 'gunicorn' in sys.argv[0]:
            return True
        return False
