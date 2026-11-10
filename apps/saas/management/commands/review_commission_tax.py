from django.core.management.base import BaseCommand, CommandError
from apps.saas.commissions import record_tax


class Command(BaseCommand):
    help = 'Record GST from a reviewed subscription invoice/refund; amounts are integer paise.'

    def add_arguments(self, parser):
        parser.add_argument('--payment', required=True)
        parser.add_argument('--mode', choices=['test', 'live'], required=True)
        parser.add_argument('--gst-paise', type=int, required=True)
        parser.add_argument('--refund-gst-paise', type=int, required=True)
        parser.add_argument('--source', required=True)
        parser.add_argument('--reason', required=True)

    def handle(self, *args, **options):
        try:
            record_tax(options['payment'], options['mode'], options['gst_paise'],
                       options['refund_gst_paise'], options['source'],
                       'management:review_commission_tax', options['reason'])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS('GST evidence saved; commission review refreshed. No payout sent.'))
