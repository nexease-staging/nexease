"""Operator interface until the full partner portal is implemented."""
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from apps.saas import commissions
from apps.saas.models import OwnerAudit


class Command(BaseCommand):
    help = 'Approve a referral partner or assign an organization before its first checkout.'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['approve', 'assign', 'statement'])
        parser.add_argument('--partner', required=True)
        parser.add_argument('--name', default='')
        parser.add_argument('--email', default='')
        parser.add_argument('--organization', default='')
        parser.add_argument('--reason', default='')
        parser.add_argument('--mode', choices=['test', 'live'], default='test')

    def handle(self, *args, **options):
        if options['action'] == 'statement':
            import json
            from mongoengine.connection import get_db
            rows = list(get_db().saas_commissions.find({'partner_id': options['partner'], 'mode': options['mode']}, {'_id': 0}).sort('paid_at', 1))
            self.stdout.write(json.dumps({'mode': options['mode'], 'status': 'review_only', 'total_paise': sum(r['amount_paise'] or 0 for r in rows), 'held_entries': sum(r['amount_paise'] is None for r in rows), 'entries': rows}, default=str, indent=2))
            return
        if len(options['reason'].strip()) < 5:
            raise CommandError('Enter an audit reason of at least five characters.')
        actor = 'management:manage_partner'
        try:
            if options['action'] == 'approve':
                commissions.approve_partner(options['partner'], options['name'], options['email'], actor)
            else:
                commissions.attach_referral(options['organization'], options['partner'], actor)
        except (ValueError, ValidationError) as exc:
            raise CommandError(str(exc)) from exc
        OwnerAudit(actor=actor, action='partner:' + options['action'], organization_id=options['organization'],
                   reason=options['reason'], details={'partner': options['partner']}).save()
        self.stdout.write(self.style.SUCCESS('Partner record saved. Commissions remain review-only; no payout sent.'))
