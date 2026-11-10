"""Install non-destructive indexes for outbox polling and provider usage."""
from django.core.management.base import BaseCommand
from mongoengine.connection import get_db


class Command(BaseCommand):
    help = 'Create renewal outbox, provider cache TTL and e-invoice usage indexes.'

    def handle(self, *args, **options):
        db = get_db()
        db.invoice_creation_requests.create_index([("organization_id", 1), ("invoice_id", 1), ("status", 1)])
        db.invoice_creation_requests.create_index([("organization_id", 1), ("user_id", 1), ("route", 1), ("fingerprint", 1), ("status", 1)])
        db.payment_operations.create_index([("organization_id", 1), ("kind", 1), ("document_id", 1), ("status", 1)])
        db.saas_payments.create_index([('organization_id', 1), ('mode', 1), ('paid_at', 1)])
        db.saas_commissions.create_index([('partner_id', 1), ('mode', 1), ('paid_at', 1)])
        db.subscription_alerts.create_index([('status', 1), ('created_at', 1)])
        db.subscription_alerts.create_index([('status', 1), ('channel', 1), ('claimed_at', 1)])
        db.provider_results.create_index('expires_at', expireAfterSeconds=0)
        db.saas_einvoice_usage.create_index([('organization_id', 1), ('period', 1)])
        self.stdout.write(self.style.SUCCESS('Reliability indexes created. Pending claims and alert history are retained.'))
