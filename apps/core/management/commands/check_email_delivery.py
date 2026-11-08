"""Read-only diagnostics for backend/worker configuration; never prints secrets or sends mail."""
import hashlib, os, json
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from mongoengine.connection import get_db

class Command(BaseCommand):
    help = 'Check email queue, worker heartbeat and safe configuration fingerprints. Does not send mail.'
    def handle(self, *args, **options):
        db=get_db(); now=datetime.utcnow()
        heartbeat=db.nexease_worker_health.find_one({'_id':'background'}) or {}
        recent=bool(heartbeat.get('at') and heartbeat['at']>now-timedelta(minutes=6))
        counts={r['_id']:r['count'] for r in db.background_jobs.aggregate([{'$match':{'job_type':'DOCUMENT_EMAIL'}},{'$group':{'_id':'$status','count':{'$sum':1}}}])}
        def fingerprint(name):
            value=os.getenv(name,'')
            return hashlib.sha256(value.encode()).hexdigest()[:12] if value else 'MISSING'
        decryptable=0;unreadable=0
        try:
            from apps.core.services.user_mailbox_service import cipher
            from cryptography.fernet import InvalidToken
            key=cipher()
            for mailbox in db.user_mailboxes.find({}, {'secret':1}):
                try:key.decrypt(str(mailbox.get('secret','')).encode());decryptable+=1
                except (InvalidToken,ValueError,TypeError):unreadable+=1
        except ValueError:unreadable=db.user_mailboxes.count_documents({})
        report={
            'database':db.name,'email_mode':getattr(settings,'EMAIL_MODE',None),
            'smtp_host':getattr(settings,'EMAIL_HOST',''),'smtp_port':getattr(settings,'EMAIL_PORT',None),
            'smtp_username_set':bool(getattr(settings,'EMAIL_HOST_USER','')),
            'smtp_password_set':bool(getattr(settings,'EMAIL_HOST_PASSWORD','')),
            'smtp_tls':getattr(settings,'EMAIL_USE_TLS',False),'smtp_ssl':getattr(settings,'EMAIL_USE_SSL',False),
            'worker_recent':recent,'worker_last_seen':heartbeat.get('at').isoformat() if heartbeat.get('at') else None,
            'document_email_queue':counts,'connected_mailboxes':db.user_mailboxes.count_documents({}),
            'decryptable_mailboxes':decryptable,'unreadable_mailboxes':unreadable,
            'mailbox_key_fingerprint':fingerprint('MAILBOX_ENCRYPTION_KEY'),
            'owner_key_fingerprint':fingerprint('OWNER_ENCRYPTION_KEY'),
            'frontend_base_url':getattr(settings,'FRONTEND_BASE_URL',''),
        }
        self.stdout.write(json.dumps(report,indent=2))
        if unreadable:self.stdout.write('ACTION: Mailbox credentials cannot be decrypted here. Restore the original MAILBOX_ENCRYPTION_KEY on backend and worker, or reconnect affected mailboxes. Do not generate another key.')
        if not recent:self.stdout.write('ACTION: Start or repair the Render background worker using this same database and encryption keys. Do not resend pending documents.')
        self.stdout.write('Run this command on BOTH backend and worker. Database and key fingerprints must match. No mailbox password, recipient, email body or reset token was printed.')
