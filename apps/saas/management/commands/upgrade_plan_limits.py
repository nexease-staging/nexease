"""Explicit, auditable quota rollout; never rewrite existing plans silently."""
from django.core.management.base import BaseCommand
from apps.saas.entitlements import DEFAULTS, seed
from apps.saas.models import Plan, Membership, OwnerAudit

class Command(BaseCommand):
    help = 'Preview requested tier quotas; use --apply to update catalogue, optionally membership snapshots.'
    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--include-memberships', action='store_true')
        parser.add_argument('--gst-basic', type=int, default=0)
        parser.add_argument('--gst-plus', type=int, default=0)
        parser.add_argument('--gst-pro', type=int, default=0)
    def handle(self, *args, **options):
        if any(options['gst_'+p]<0 or options['gst_'+p]>1000000 for p in ('basic','plus','pro')):
            raise ValueError('GST quotas must be between 0 and 1000000.')
        if options['apply']:seed()
        for code, (_, _, limits, _) in DEFAULTS.items():
            limits={**limits,'gst_lookups':options.get('gst_'+code,0)}
            self.stdout.write(f'{code}: {limits}')
            if options['apply']:
                Plan.objects(code=code).update_one(set__limits=limits)
                if options['include_memberships']:
                    Membership.objects(plan=code).update(set__limits=limits)
        if options['apply']:
            OwnerAudit(actor='management:upgrade_plan_limits', action='quota_rollout',
                reason='Explicit operator command',details={'memberships':options['include_memberships'], 'gst':{k:options['gst_'+k] for k in ('basic','plus','pro')}}).save()
        else:self.stdout.write('Preview only; no records changed.')
