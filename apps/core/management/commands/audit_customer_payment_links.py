"""Read-only diagnostic; does not repair or certify financial statements."""
from decimal import Decimal
import json
from django.core.management.base import BaseCommand, CommandError
from apps.organizations.models import Organization
from apps.sales.models import CustomerPayment
from apps.finance.models import BankTransaction, JournalEntry


class Command(BaseCommand):
    help = 'Read-only tenant-scoped customer payment/bank/journal linkage audit.'

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
        payments = CustomerPayment.objects(organization=org).order_by('id')
        issues = []
        checked = 0
        for payment in payments.limit(options['limit']):
            checked += 1
            found = []
            if sum((a.amount for a in payment.allocations), Decimal('0')) != payment.amount:
                found.append('ALLOCATION_TOTAL_MISMATCH')
            banks = list(BankTransaction.objects(organization=org, reference_type='CUSTOMER_PAYMENT', reference_id=payment.payment_number))
            if len(banks) != 1:
                found.append('BANK_TRANSACTION_COUNT_' + str(len(banks)))
            else:
                try:
                    if banks[0].amount != payment.amount or banks[0].transaction_type != 'MONEY_IN' or banks[0].bank_account.id != payment.bank_account.id:
                        found.append('BANK_TRANSACTION_MISMATCH')
                except Exception:
                    found.append('MISSING_BANK_ACCOUNT_LINK')
            journals = list(JournalEntry.objects(organization=org, source_type='CUSTOMER_PAYMENT', source_id=str(payment.id)))
            if len(journals) != 1:
                found.append('JOURNAL_COUNT_' + str(len(journals)))
            elif journals[0].status != 'POSTED':
                found.append('JOURNAL_NOT_POSTED')
            elif journals[0].total_debit != payment.amount or journals[0].total_credit != payment.amount:
                found.append('JOURNAL_AMOUNT_MISMATCH')
            for allocation in payment.allocations:
                try:
                    invoice = allocation.invoice
                    if not invoice or invoice.organization.id != org.id:
                        found.append('INVALID_INVOICE_LINK')
                except Exception:
                    found.append('MISSING_INVOICE_LINK')
            if found:
                issues.append({'payment_id':str(payment.id),'payment_number':payment.payment_number,'issues':sorted(set(found))})
        self.stdout.write(json.dumps({'organization_id':str(org.id),'checked':checked,'total':payments.count(),
            'truncated':payments.count()>checked,'issues':issues,'read_only':True,
            'scope':'Customer payment source links only; not a full ledger, balance, tax or bank reconciliation.'},indent=2))
