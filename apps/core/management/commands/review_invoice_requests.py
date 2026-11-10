"""Read-only inspection of interrupted invoice creation; no automatic replay."""
import json
from django.core.management.base import BaseCommand, CommandError
from mongoengine.connection import get_db
from apps.organizations.models import Organization


class Command(BaseCommand):
    help = 'List incomplete invoice creation requests for one organization.'

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
        collection = get_db().invoice_creation_requests
        query = {'organization_id':str(org.id), 'status':{'$ne':'completed'}}
        rows = list(collection.find(query, {'response':0, 'fingerprint':0}).sort('created_at',1).limit(options['limit']))
        self.stdout.write(json.dumps({'read_only':True, 'organization_id':str(org.id), 'requests':rows,
            'total':collection.count_documents(query), 'truncated':collection.count_documents(query)>len(rows),
            'next_step':'Inspect invoice, stock, masters and audit records before repair. Do not delete receipts or retry with a new key to bypass a hold.'}, default=str, indent=2))
