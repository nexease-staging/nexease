from django.core.management.base import BaseCommand,CommandError
from mongoengine.connection import get_db
from apps.saas.security import log
class Command(BaseCommand):
 help='Recover a lock ONLY after stopping ALL backend/worker instances. Never run against active writers.'
 def add_arguments(self,p):p.add_argument('organization_id')
 def handle(self,*args,**options):
  oid=options['organization_id'];row=get_db().saas_write_locks.find_one({'_id':oid})
  if not row:self.stdout.write('No SaaS write lock exists.');return
  self.stdout.write('Lock time: '+str(row.get('at')))
  if input('Stop ALL backend/worker instances. Type STOPPED to confirm: ')!='STOPPED':raise CommandError('Cancelled.')
  get_db().saas_write_locks.delete_one({'_id':oid,'token':row.get('token')});log('terminal','recover-write-lock',oid,'Operator confirmed all writers stopped.');self.stdout.write('Lock removed. Restart application.')
