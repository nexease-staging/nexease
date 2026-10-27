import secrets,base64,getpass
from urllib.parse import quote
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from apps.saas.models import PlatformOwner
from apps.saas.security import cipher,log
class Command(BaseCommand):
 help='Create/recover the single platform owner. Run only in a trusted terminal.'
 def add_arguments(self,p):p.add_argument('--recover',action='store_true')
 def handle(self,*args,**options):
  c=cipher();existing=PlatformOwner.objects.first()
  if existing and not options['recover']:raise CommandError('Owner already exists. Use --recover only for account recovery.')
  email=(existing.email if existing else input('Owner email: ').strip().lower())
  from django.core.validators import validate_email
  validate_email(email)
  password=getpass.getpass('Owner password (not displayed): ')
  if password!=getpass.getpass('Repeat password: '):raise CommandError('Passwords differ.')
  validate_password(password)
  secret=base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')
  o=existing or PlatformOwner(email=email);o.password=make_password(password);o.totp_secret=c.encrypt(secret.encode()).decode();o.generation+=1;o.last_counter=-1;o.active=True;o.save();log(email,'terminal-owner-recovery' if existing else 'terminal-owner-created')
  self.stdout.write('Add a time-based account in your authenticator app (6 digits, 30 seconds). Keep this secret private:')
  self.stdout.write(secret)
  self.stdout.write('Account: NexEase Owner / '+email)
  self.stdout.write('Open /owner. Password plus a current authenticator code is required. Recovery uses this command on the server.')
