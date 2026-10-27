from django.core.management.base import BaseCommand
from apps.saas.models import Checkout
from apps.saas.gateway import reconcile,mode
class Command(BaseCommand):
 help='Recover missed payment webhooks using provider-verified subscription invoices.'
 def handle(self,*args,**kwargs):
  for c in Checkout.objects(mode=mode(),status__nin=['expired','completed']):
   try:r=reconcile(c.subscription_id);self.stdout.write(c.subscription_id+' '+r['status'])
   except Exception as e:self.stderr.write(c.subscription_id+': '+str(e))
