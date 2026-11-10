import bootstrap
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from threading import Event
from unittest.mock import patch
from uuid import uuid4
from mongoengine.connection import get_db
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.sales.models import Customer, Invoice, InvoiceItem, CustomerPayment
from apps.finance.models import BankAccount, BankTransaction, ChartOfAccount, JournalEntry
from apps.sales.services.payment_service import PaymentService


class PaymentOperationTests(unittest.TestCase):
    def setUp(self):
        self.org = Organization(name='Payment test', email='test@example.com').save()
        self.user = User(organization=self.org, email=uuid4().hex+'@example.com', password='test', first_name='Test', last_name='User').save()
        customer = Customer(organization=self.org, name='Customer', code='C1').save()
        category = Category(organization=self.org, name='Service').save()
        product = Product(organization=self.org, sku='S1', name='Service', category=category, unit='hour').save()
        self.invoice = Invoice(organization=self.org, customer=customer, invoice_number='I1', status='ISSUED',
            invoice_date=datetime.utcnow(), billing_name='Customer', created_by=self.user,
            items=[InvoiceItem(product=product, quantity=1, unit_price=100, line_total=100)],
            total_amount=100, balance_due=100).save()
        self.bank = BankAccount(organization=self.org, account_name='Cash', account_type='CASH', created_by=self.user).save()
        for code in ('ACCOUNTS_RECEIVABLE', 'CASH'):
            ChartOfAccount(organization=self.org, account_code=code, account_name=code, system_key=code,
                is_system_account=True, account_type='ASSET', normal_balance='DEBIT', created_by=self.user).save()
        self.auth = patch('apps.authorization.services.AuthorizationService.has_permission', return_value=True)
        self.auth.start()
        self.addCleanup(self.auth.stop)

    def pay(self, key='test-payment-key-0001', **overrides):
        kwargs = dict(user=self.user, organization=self.org, invoice=self.invoice, bank_account=self.bank,
                      payment_method='CASH', amount='40', request_key=key)
        kwargs.update(overrides)
        return PaymentService.record_invoice_payment(**kwargs)

    def test_success_replay_has_one_payment_bank_and_posted_journal(self):
        first = self.pay()
        again = self.pay()
        self.assertEqual(first.id, again.id)
        self.assertEqual(CustomerPayment.objects(organization=self.org).count(), 1)
        self.assertEqual(BankTransaction.objects(organization=self.org).count(), 1)
        journal = JournalEntry.objects(organization=self.org).get()
        self.assertEqual((journal.status, journal.total_debit, journal.total_credit), ('POSTED', Decimal('40'), Decimal('40')))
        self.assertEqual(self.bank.reload().current_balance, Decimal('40'))
        self.assertEqual(self.invoice.reload().amount_paid, Decimal('40'))

    def test_stale_invoice_is_refreshed_and_overpayment_rejected(self):
        stale = Invoice.objects.get(id=self.invoice.id)
        self.pay(amount='60')
        with self.assertRaisesRegex(ValueError, 'exceed'):
            self.pay(key='test-payment-key-0002', amount='60', invoice=stale)
        self.pay(key='test-payment-key-0002', amount='40', invoice=stale)
        self.assertEqual(self.invoice.reload().status, 'PAID')
        self.assertEqual(self.invoice.amount_paid, Decimal('100'))
        # Replay still succeeds after full settlement.
        self.assertEqual(self.pay(amount='60').amount, Decimal('60'))

    def test_changed_payload_and_other_user_cannot_replay(self):
        self.pay()
        with self.assertRaisesRegex(ValueError, 'different details'):
            self.pay(amount='41')
        another = User(organization=self.org, email=uuid4().hex+'@example.com', password='test', first_name='Other', last_name='User').save()
        with self.assertRaisesRegex(ValueError, 'different details'):
            self.pay(user=another)
        other_org = Organization(name='Other', email='other@example.com').save()
        with self.assertRaises(PermissionError):
            self.pay(organization=other_org)

    def test_posting_failure_retains_evidence_and_blocks_both_retry_keys(self):
        with patch.object(PaymentService, '_post_customer_payment_accounting', side_effect=RuntimeError('injected crash')):
            with self.assertRaisesRegex(ValueError, 'reconciliation'):
                self.pay()
        for key in ('test-payment-key-0001', 'test-payment-key-0002'):
            with self.assertRaisesRegex(ValueError, 'reconciliation'):
                self.pay(key=key)
        self.assertEqual(CustomerPayment.objects(organization=self.org).count(), 1)
        self.assertEqual(BankTransaction.objects(organization=self.org).count(), 1)
        self.assertEqual(self.invoice.reload().amount_paid, Decimal('40'))
        receipt = get_db().payment_operations.find_one({'organization_id': str(self.org.id)})
        self.assertEqual(receipt['status'], 'review_required')
        self.assertTrue(receipt['payment_number'])

    def test_concurrent_request_fails_closed_then_replays(self):
        entered, release = Event(), Event()
        original = PaymentService._post_customer_payment_accounting
        def pause(**kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('Test synchronization timeout')
            return original(**kwargs)
        with ThreadPoolExecutor(max_workers=2) as pool, patch.object(PaymentService, '_post_customer_payment_accounting', side_effect=pause):
            first = pool.submit(self.pay)
            self.assertTrue(entered.wait(5))
            try:
                with self.assertRaisesRegex(ValueError, "Another update"):
                    self.pay()
            finally:
                release.set()
            payment = first.result(timeout=5)
        self.assertEqual(self.pay().id, payment.id)
        self.assertEqual(CustomerPayment.objects(organization=self.org).count(), 1)

    def test_statement_completion_failure_keeps_posted_payment_and_blocks_repayment(self):
        from apps.finance.models import BankStatement, BankStatementLine, BankPaymentSuggestion
        from apps.finance.services.bank_payment_suggestion_service import BankPaymentSuggestionService
        from apps.finance.repositories.bank_payment_suggestion_repository import BankPaymentSuggestionRepository
        from apps.purchasing.models import SupplierPayment
        supplier = hasattr(self, 'bill')
        # Statement-generated payments use the BANK system account.
        ChartOfAccount(organization=self.org, account_code='BANK', account_name='Bank', system_key='BANK',
            is_system_account=True, account_type='ASSET', normal_balance='DEBIT', created_by=self.user).save()
        now = datetime.utcnow()
        statement = BankStatement(organization=self.org, statement_number='ST1', bank_account=self.bank,
            statement_start_date=now, statement_end_date=now, opening_balance=0, closing_balance=-40 if supplier else 40,
            created_by=self.user, lines=[BankStatementLine(line_number='1', transaction_date=now,
                debit_amount=40 if supplier else 0, credit_amount=0 if supplier else 40)]).save()
        suggestion = BankPaymentSuggestion(organization=self.org, statement=statement, line_number='1', amount=40,
            suggestion_type='SUPPLIER_PAYMENT' if supplier else 'CUSTOMER_RECEIPT',
            invoice=None if supplier else self.invoice, vendor_bill=self.bill if supplier else None,
            status='CONFIRMED', created_by=self.user).save()
        execute = BankPaymentSuggestionService.execute_supplier_payment if supplier else BankPaymentSuggestionService.execute_customer_receipt
        with patch.object(BankPaymentSuggestionRepository, 'mark_executed', side_effect=RuntimeError('injected failure')):
            with self.assertRaises(RuntimeError):
                execute(user=self.user, organization=self.org, suggestion=suggestion)
        model = SupplierPayment if supplier else CustomerPayment
        self.assertEqual(model.objects(organization=self.org).count(), 1)
        self.assertEqual(BankTransaction.objects(organization=self.org).count(), 1)
        self.assertEqual(JournalEntry.objects(organization=self.org, status='POSTED').count(), 1)
        with self.assertRaisesRegex(ValueError, 'reconciliation'):
            self.pay(key='test-payment-key-after-statement')


class SupplierOperationTests(PaymentOperationTests):
    # Reuse the complete service tests against the supplier path as well.
    def setUp(self):
        super().setUp()
        from apps.purchasing.models import Supplier, VendorBill, VendorBillItem
        self.supplier = Supplier(organization=self.org, code='S1', name='Supplier').save()
        self.bill = VendorBill(organization=self.org, supplier=self.supplier, bill_number='B1', status='POSTED',
            bill_date=datetime.utcnow(), created_by=self.user,
            items=[VendorBillItem(product=Product.objects(organization=self.org).first(), quantity=1, unit_price=100, line_total=100)],
            total_amount=100, balance_due=100).save()
        ChartOfAccount(organization=self.org, account_code='AP', account_name='Payables', system_key='ACCOUNTS_PAYABLE',
            is_system_account=True, account_type='LIABILITY', normal_balance='CREDIT', created_by=self.user).save()

    def pay(self, key='test-payment-key-0001', **overrides):
        from apps.purchasing.services.supplier_payment_service import SupplierPaymentService
        kwargs = dict(user=self.user, organization=self.org, vendor_bill=self.bill, bank_account=self.bank,
                      payment_method='CASH', amount='40', request_key=key)
        kwargs.update(overrides)
        return SupplierPaymentService.record_bill_payment(**kwargs)

    def test_success_replay_has_one_payment_bank_and_posted_journal(self):
        from apps.purchasing.models import SupplierPayment
        first = self.pay()
        self.assertEqual(self.pay().id, first.id)
        self.assertEqual(SupplierPayment.objects(organization=self.org).count(), 1)
        self.assertEqual(BankTransaction.objects(organization=self.org).count(), 1)
        journal = JournalEntry.objects(organization=self.org).get()
        self.assertEqual((journal.status, journal.total_debit, journal.total_credit), ('POSTED', Decimal('40'), Decimal('40')))
        self.assertEqual(self.bank.reload().current_balance, Decimal('-40'))
        self.assertEqual(self.bill.reload().amount_paid, Decimal('40'))

    def test_stale_invoice_is_refreshed_and_overpayment_rejected(self):
        from apps.purchasing.models import VendorBill
        stale = VendorBill.objects.get(id=self.bill.id)
        self.pay(amount='60')
        with self.assertRaisesRegex(ValueError, 'exceed'):
            self.pay(key='test-payment-key-0002', amount='60', vendor_bill=stale)
        self.pay(key='test-payment-key-0002', amount='40', vendor_bill=stale)
        self.assertEqual(self.bill.reload().status, 'PAID')
        self.assertEqual(self.bill.amount_paid, Decimal('100'))
        self.assertEqual(self.pay(amount='60').amount, Decimal('60'))

    def test_posting_failure_retains_evidence_and_blocks_both_retry_keys(self):
        from apps.purchasing.models import SupplierPayment
        from apps.purchasing.services.supplier_payment_service import SupplierPaymentService
        with patch.object(SupplierPaymentService, '_post_supplier_payment_accounting', side_effect=RuntimeError('injected crash')):
            with self.assertRaisesRegex(ValueError, 'reconciliation'):
                self.pay()
        for key in ('test-payment-key-0001', 'test-payment-key-0002'):
            with self.assertRaisesRegex(ValueError, 'reconciliation'):
                self.pay(key=key)
        self.assertEqual(SupplierPayment.objects(organization=self.org).count(), 1)
        self.assertEqual(BankTransaction.objects(organization=self.org).count(), 1)
        self.assertEqual(self.bill.reload().amount_paid, Decimal('40'))

    def test_concurrent_request_fails_closed_then_replays(self):
        from apps.purchasing.models import SupplierPayment
        from apps.purchasing.services.supplier_payment_service import SupplierPaymentService
        entered, release = Event(), Event()
        original = SupplierPaymentService._post_supplier_payment_accounting
        def pause(**kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('Test synchronization timeout')
            return original(**kwargs)
        with ThreadPoolExecutor(max_workers=2) as pool, patch.object(SupplierPaymentService, '_post_supplier_payment_accounting', side_effect=pause):
            first = pool.submit(self.pay)
            self.assertTrue(entered.wait(5))
            try:
                with self.assertRaisesRegex(ValueError, "Another update"):
                    self.pay()
            finally:
                release.set()
            payment = first.result(timeout=5)
        self.assertEqual(self.pay().id, payment.id)
        self.assertEqual(SupplierPayment.objects(organization=self.org).count(), 1)
