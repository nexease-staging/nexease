from django.core.management.base import BaseCommand,CommandError
from apps.saas.models import Plan,OwnerAudit
from apps.saas.entitlements import seed,DEFAULTS
class Command(BaseCommand):
    help='Set launch catalogue prices to 749/999/1299. Existing paid subscriptions keep their contracted price.'
    def handle(self,*args,**options):
        seed()
        if Plan.objects(published=True).first():raise CommandError('Published payment plans exist. Reprice and republish them deliberately in /owner; no plans were changed.')
        for code,(_,price,_,_) in DEFAULTS.items():
            Plan.objects(code=code).update_one(set__price_paise=price*100,inc__revision=1)
        OwnerAudit(actor='management-command',action='set-launch-prices',reason='Launch price catalogue update; active subscriptions unchanged').save()
        self.stdout.write(self.style.SUCCESS('Catalogue set to 749 / 999 / 1299. Publish replacement payment plans in /owner when ready.'))
