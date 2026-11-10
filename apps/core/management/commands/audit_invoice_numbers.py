"""Read-only numbering evidence; never renumbers or recycles invoices."""
import json
from django.core.management.base import BaseCommand, CommandError
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.sales.models import Invoice


class Command(BaseCommand):
    help = 'Inspect invoice number reservations and missing document links for one organization.'

    def add_arguments(self, parser):
        parser.add_argument('--organization', required=True)
        parser.add_argument('--limit', type=int, default=1000)

    def handle(self, *args, **options):
        if not 1 <= options['limit'] <= 10000:
            raise CommandError('Limit must be between 1 and 10000.')
        try:
            org = Organization.objects(id=options['organization']).first()
        except Exception as exc:
            raise CommandError('Invalid organization ID.') from exc
        if not org:
            raise CommandError('Organization not found.')
        prefix = str(org.id) + ':Invoice:'
        query = {'_id': {'$regex': '^' + prefix}}
        collection = get_db().nexease_number_reservations
        issues = []; checked = 0
        for row in collection.find(query).sort('_id', 1).limit(options['limit']):
            checked += 1
            number = row.get('number') or row['_id'][len(prefix):]
            invoice = Invoice.objects(organization=org, invoice_number=number).only('id').first()
            if not invoice:
                issues.append({'number': number, 'status': row.get('status', 'legacy_reserved'),
                               'issue': 'RESERVED_WITHOUT_DOCUMENT', 'reserved_at': row.get('reserved_at')})
            elif row.get('document_id') != str(invoice.id):
                issues.append({'number': number, 'issue': 'MISSING_OR_DIFFERENT_RESERVATION_LINK'})
        self.stdout.write(json.dumps({'read_only': True, 'organization_id': str(org.id), 'checked': checked,
            'total_reservations': collection.count_documents(query), 'issues': issues,
            'truncated': collection.count_documents(query) > checked,
            'scope': 'Reservation evidence only. Older invoices without reservations and manual numbering gaps require separate review. Never recycle a reserved number.'}, default=str, indent=2))
