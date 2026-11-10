"""Read-only interrupted payment inventory. Never releases locks or rewrites money."""
import json
from django.core.management.base import BaseCommand, CommandError
from mongoengine.connection import get_db
from apps.organizations.models import Organization


class Command(BaseCommand):
    help = 'List incomplete customer/supplier payment operations for one organization (read-only).'

    def add_arguments(self, parser):
        parser.add_argument('--organization', required=True)
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        if not 1 <= options['limit'] <= 1000:
            raise CommandError('Limit must be between 1 and 1000.')
        try:
            org = Organization.objects(id=options['organization']).first()
        except Exception as exc:
            raise CommandError('Invalid organization ID.') from exc
        if not org:
            raise CommandError('Organization not found.')
        db = get_db()
        query = {'organization_id': str(org.id), 'status': {'$ne': 'completed'}}
        rows = list(db.payment_operations.find(query, {'fingerprint': 0}).sort('created_at', 1).limit(options['limit']))
        self.stdout.write(json.dumps({'read_only': True, 'organization_id': str(org.id),
            'total': db.payment_operations.count_documents(query), 'operations': rows,
            'organization_lock_present': bool(db.saas_write_locks.find_one({'_id': str(org.id)})),
            'next_step': 'Reconcile payment, bank, document and journal records before any repair. Do not delete receipts or clear locks while a worker may still be running.'}, default=str, indent=2))
