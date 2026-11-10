import bootstrap
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from mongoengine import ValidationError
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.sales.models import Invoice
from apps.business.numbering import allocate, configure, financial_year, incoming, settings, choice, owned


class InvoiceNumberingTests(unittest.TestCase):
    def setUp(self):
        self.org = Organization(name='Number test', email='number@example.com').save()
        self.token = choice.set(None)
        self.reservations = owned.set({})
        self.addCleanup(choice.reset, self.token)
        self.addCleanup(owned.reset, self.reservations)

    def test_ist_year_boundary_and_date_only(self):
        self.assertEqual(financial_year('2026-03-31'), '2025-26')
        self.assertEqual(financial_year('2026-04-01'), '2026-27')
        self.assertEqual(financial_year(datetime(2026,3,31,18,29,tzinfo=timezone.utc)), '2025-26')
        self.assertEqual(financial_year(datetime(2026,3,31,18,30,tzinfo=timezone.utc)), '2026-27')

    def test_opt_in_year_sequences_and_backdated_documents(self):
        self.assertEqual(allocate(self.org, 'Invoice'), 'INV-00001')
        configure(self.org, 'Invoice', 'automatic', 'INV-', 1, 5, True)
        self.assertEqual(allocate(self.org, 'Invoice', document_date='2026-03-31'), 'INV-25-26/00001')
        self.assertEqual(allocate(self.org, 'Invoice', document_date='2026-04-01'), 'INV-26-27/00001')
        self.assertEqual(allocate(self.org, 'Invoice', document_date='2026-03-30'), 'INV-25-26/00002')
        self.assertEqual(settings(self.org, 'Invoice', '2026-04-02')['preview'], 'INV-26-27/00002')
        configure(self.org, 'Invoice', 'automatic', 'INV-', 1, 5, False)
        self.assertEqual(allocate(self.org, 'Invoice'), 'INV-00002')

    def test_concurrent_allocations_are_unique_and_tenant_scoped(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            numbers = list(pool.map(lambda _: allocate(self.org, 'Invoice'), range(40)))
        self.assertEqual(len(set(numbers)), 40)
        self.assertEqual(set(numbers), {f'INV-{i:05d}' for i in range(1,41)})
        other = Organization(name='Other', email='other@example.com').save()
        self.assertEqual(allocate(other, 'Invoice'), 'INV-00001')

    def test_legacy_collision_is_skipped_and_documented(self):
        # Raw seed represents an invoice created before reservations existed.
        inserted = Invoice._get_collection().insert_one({'organization': self.org.id, 'invoice_number': 'INV-00001'})
        self.assertEqual(allocate(self.org, 'Invoice'), 'INV-00002')
        row = get_db().nexease_number_reservations.find_one({'_id': str(self.org.id)+':Invoice:INV-00001'})
        self.assertEqual(row['document_id'], str(inserted.inserted_id))
        self.assertTrue(row['legacy'])
        with self.assertRaises(ValueError):
            allocate(self.org, 'Invoice', 'INV-00001')

    def test_failed_validation_retry_keeps_same_reservation(self):
        token = choice.set({'kind':'Invoice','mode':'automatic'})
        try:
            invoice = Invoice(organization=self.org, invoice_date=datetime(2026,4,1))
            for _ in range(2):
                with self.assertRaises(ValidationError):
                    invoice.save()
            self.assertEqual(invoice.invoice_number, 'INV-00001')
            self.assertEqual(settings(self.org, 'Invoice')['next'], 2)
            row = get_db().nexease_number_reservations.find_one({'_id':str(self.org.id)+':Invoice:INV-00001'})
            self.assertEqual(row['status'], 'reserved')
        finally:
            choice.reset(token)

    def test_manual_reservation_is_not_recycled(self):
        self.assertEqual(incoming(self.org, 'Invoice', ' manual-1 '), 'MANUAL-1')
        token = owned.set({})
        try:
            with self.assertRaises(ValueError):
                incoming(self.org, 'Invoice', 'MANUAL-1')
        finally:
            owned.reset(token)
        configure(self.org, 'Invoice', 'automatic', 'INV-', 20, 5)
        configure(self.org, 'Invoice', 'automatic', 'INV-', 1, 5)
        self.assertEqual(settings(self.org, 'Invoice')['next'], 20)

    def test_success_attaches_reservation_and_edit_does_not_renumber(self):
        # Minimal stored document isolates numbering signals from invoice validation.
        invoice = Invoice(organization=self.org, invoice_number='MANUAL-9', invoice_date=datetime(2026,4,1)).save(validate=False)
        row = get_db().nexease_number_reservations.find_one({'_id':str(self.org.id)+':Invoice:MANUAL-9'})
        self.assertEqual((row['status'],row['document_id']), ('attached',str(invoice.id)))
        token=choice.set({'kind':'Invoice','mode':'automatic'})
        try:
            invoice.notes='Edited';invoice.save(validate=False)
            self.assertEqual(invoice.invoice_number,'MANUAL-9')
        finally:choice.reset(token)

    def test_concurrent_manual_requests_reserve_once(self):
        def reserve(_):
            try:
                return allocate(self.org, 'Invoice', 'CLIENT-2026-1')
            except ValueError:
                return None
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(reserve, range(8)))
        self.assertEqual(results.count('CLIENT-2026-1'), 1)

    def test_audit_reports_unattached_reservation_without_recycling(self):
        from io import StringIO
        import json
        from django.core.management import call_command
        allocate(self.org, 'Invoice', 'UNSAVED-1')
        before = list(get_db().nexease_number_reservations.find({'organization_id':str(self.org.id)}))
        output = StringIO()
        call_command('audit_invoice_numbers', organization=str(self.org.id), stdout=output)
        result = json.loads(output.getvalue())
        self.assertTrue(result['read_only'])
        self.assertEqual(result['issues'][0]['issue'], 'RESERVED_WITHOUT_DOCUMENT')
        self.assertEqual(before,list(get_db().nexease_number_reservations.find({'organization_id':str(self.org.id)})))
