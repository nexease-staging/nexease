from django.core.management.base import BaseCommand,CommandError
from mongoengine.connection import get_db
from bson import ObjectId
class Command(BaseCommand):
    help='Recover a workforce lock after a stopped/crashed process. Stop all app and worker processes first.'
    def add_arguments(self,parser):
        parser.add_argument('--organization',required=True)
        parser.add_argument('--confirm-workers-stopped',action='store_true')
    def handle(self,*args,**options):
        if not options['confirm_workers_stopped']:raise CommandError('Stop every backend and background worker first, then pass --confirm-workers-stopped.')
        if not ObjectId.is_valid(options['organization']):raise CommandError('Invalid organization ID.')
        result=get_db().nexease_workforce_locks.delete_one({'_id':options['organization']})
        self.stdout.write('Removed abandoned lock.' if result.deleted_count else 'No workforce lock exists.')
