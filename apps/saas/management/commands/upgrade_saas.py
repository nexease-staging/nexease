from datetime import datetime,timedelta
from django.core.management.base import BaseCommand,CommandError
from django.core.management import call_command
from apps.saas.models import Membership,Plan
from apps.saas.entitlements import seed
from apps.organizations.models import Organization
class Command(BaseCommand):
 help='Prepare plans; optionally explicitly grant legacy organizations a Pro trial. No financial data reset.'
 def add_arguments(self,p):p.add_argument('--legacy-trial-days',type=int,default=0)
 def handle(self,*args,**options):
  days=options['legacy_trial_days']
  if not 0<=days<=90:raise CommandError('Use 0–90 days.')
  call_command('upgrade_professional');seed();count=0
  if days:
   p=Plan.objects.get(code='pro')
   for o in Organization.objects:
    if Membership.objects(organization_id=str(o.id)).first():continue
    Membership(organization_id=str(o.id),plan='pro',status='trial',start=datetime.utcnow(),end=datetime.utcnow()+timedelta(days=days),limits=p.limits,features=p.features).save();count+=1
  self.stdout.write(self.style.SUCCESS(f'Plans ready. Granted {count} explicit legacy Pro trials. New signups need checkout or an owner-granted trial.'))
