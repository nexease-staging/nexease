import bootstrap
import unittest
from decimal import Decimal
from types import SimpleNamespace as NS
from unittest.mock import patch, Mock
from apps.sales.services.payment_service import PaymentService
from apps.purchasing.services.supplier_payment_service import SupplierPaymentService

class PaymentSafetyTests(unittest.TestCase):
 def test_amount_rejects_nonfinite_and_subpaise(self):
  for service in (PaymentService,SupplierPaymentService):
   for value in ('NaN','sNaN','Infinity','-Infinity','0.001','10.999'):
    with self.subTest(service=service,value=value),self.assertRaises(ValueError):service._to_decimal(value,'amount')
   self.assertEqual(service._to_decimal('123.40','amount'),Decimal('123.40'))
   self.assertEqual(service._to_decimal('1.000','amount'),Decimal('1'))
 def test_draft_journal_retry_posts_existing_without_recreation(self):
  for module,service,method in [('apps.sales.services.payment_service',PaymentService,'_post_customer_payment_accounting'),('apps.purchasing.services.supplier_payment_service',SupplierPaymentService,'_post_supplier_payment_accounting')]:
   org=NS(id='org');payment=NS(id='pay',organization=org,amount=Decimal('10'))
   for status in ('DRAFT','POSTED','REVERSED'):
    journal=NS(id='journal',status=status)
    with patch(module+'.JournalEntryRepository.get_by_source',return_value=journal),patch(module+'.JournalEntryService.post_journal',return_value=journal) as post,patch(module+'.JournalEntryService.create_journal') as create:
     if status=='REVERSED':
      with self.assertRaises(ValueError):getattr(service,method)(user=NS(),organization=org,payment=payment)
     else:self.assertIs(getattr(service,method)(user=NS(),organization=org,payment=payment),journal)
     self.assertEqual(post.call_count,1 if status=='DRAFT' else 0)
     create.assert_not_called()
 def test_missing_account_blocks_before_payment_or_bank_mutation(self):
  org=NS(id='org');user=NS(id='user',organization=org,is_active=True)
  invoice=NS(id='invoice',reload=Mock(),organization=org,status='ISSUED',customer=NS(organization=org),amount_paid=Decimal('0'),balance_due=Decimal('10'),total_amount=Decimal('10'))
  bank=NS(id='bank',reload=Mock(),organization=org,is_active=True)
  module='apps.sales.services.payment_service'
  with patch(module+'.AuthorizationService.has_permission',return_value=True),patch(module+'.InvoiceService.get_invoice_net_receivable',return_value=Decimal('10')),patch(module+'.ChartOfAccountService.get_system_account',side_effect=ValueError('System account missing')),patch(module+'.PaymentRepository.create_payment') as create,patch(module+'.BankTransactionService.create_transaction') as bankwrite:
   with self.assertRaises(ValueError):PaymentService.record_invoice_payment(user=user,organization=org,invoice=invoice,amount='5',payment_method='CASH',bank_account=bank)
   create.assert_not_called();bankwrite.assert_not_called()
