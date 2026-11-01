import time
from django.core.management.base import BaseCommand, CommandError
from apps.core.services.device_notification_service import dispatch_once
import os
class Command(BaseCommand):
    help = 'Deliver Android push alerts and six-hour business reminders. Run one instance.'
    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')
    def handle(self, *args, **options):
        if os.getenv('NEXEASE_PUSH_ENABLED', '').lower() != 'true':
            raise CommandError('Set NEXEASE_PUSH_ENABLED=true and configure Firebase credentials first.')
        self.stdout.write('NexEase notification worker started.')
        while True:
            try:
                dispatch_once()
            except Exception:
                self.stderr.write('Notification cycle failed. Check Firebase installation, credentials and database connectivity.')
                if options['once']:
                    raise CommandError('Notification delivery check failed.')
            if options['once']:
                return
            time.sleep(30)
