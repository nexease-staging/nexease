"""Read-only diagnostics; never prints credentials or sends a message."""
import os
from datetime import datetime,timedelta
from django.core.management.base import BaseCommand
from mongoengine.connection import get_db
from apps.core.background_job_models import BackgroundJob
class Command(BaseCommand):
 help='Show worker, email queue and quotation outbox status without exposing secrets.'
 def handle(self,*args,**kwargs):
  db=get_db();h=db.nexease_worker_health.find_one({'_id':'background'})
  active=bool(h and h['at']>datetime.utcnow()-timedelta(minutes=6))
  self.stdout.write('Worker heartbeat: '+('recent' if active else 'missing or stale'))
  self.stdout.write('System email mode: '+os.getenv('EMAIL_MODE','development'))
  for key in ('SMTP_HOST','SMTP_USERNAME','SMTP_PASSWORD','MAILBOX_ENCRYPTION_KEY'):
   self.stdout.write(key+': '+('configured' if os.getenv(key) else 'missing'))
  for status in ('PENDING','RUNNING','RETRYING','FAILED','SUCCEEDED'):
   self.stdout.write('Document emails '+status+': '+str(BackgroundJob.objects(job_type='DOCUMENT_EMAIL',status=status).count()))
  for status in ('pending','sending','retry','failed','sent'):
   self.stdout.write('Quotations '+status+': '+str(db.nexease_quotations.count_documents({'status':status})))
  self.stdout.write('A connected mailbox still needs a continuously running worker. Check Document Logs for a failed job; do not duplicate pending jobs.')
