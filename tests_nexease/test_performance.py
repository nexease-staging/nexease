import bootstrap
import json, unittest
from bson import ObjectId
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace as NS
from unittest.mock import patch
from django.http import HttpResponse
from django.test import RequestFactory
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.accounts.services import AuthenticationService as Auth
from apps.sales.models import Invoice, Customer
from apps.sales.services.invoice_service import InvoiceService
from apps.sales.services.customer_payment_api_service import CustomerPaymentAPIService as Payments
from apps.sales.api.v1.invoice_overview_views import invoice_overview
from apps.core.services.request_performance import begin, finish, read_once, RequestMongoListener
from apps.core.middleware.performance_middleware import PerformanceMiddleware

class PerformanceTests(unittest.TestCase):
 def setUp(self):
  get_db().client.drop_database(get_db().name)
  self.org=Organization(name='First',email='first@example.test').save()
  self.other=Organization(name='Other',email='other@example.test').save()
  self.user=User(organization=self.org,email='user@example.test',password='test',first_name='Test',last_name='User').save()
  self.customer=Customer(organization=self.org,code='C1',name='Buyer').save(validate=False)
  self.now=datetime.utcnow()
 def invoice(self,number,org=None,balance='100.00'):
  return Invoice(organization=org or self.org,customer=self.customer,invoice_number=number,invoice_date=self.now,due_date=self.now-timedelta(days=2),status='ISSUED',items=[],balance_due=Decimal(balance),total_amount=Decimal('100'),created_by=self.user).save(validate=False)
 def credit(self,invoice,amount,status='ISSUED',org=None):
  get_db().credit_notes.insert_one({'organization':(org or self.org).id,'invoice':invoice.id,'sales_return':ObjectId(),'status':status,'applied_amount':float(amount),'credit_note_number':str(get_db().credit_notes.count_documents({}))})
 def test_bulk_credit_financial_parity_and_tenant_scope(self):
  first=self.invoice('I1'); second=self.invoice('I2',balance='20')
  self.credit(first,'10.25');self.credit(first,'5.50');self.credit(first,'99',status='DRAFT');self.credit(first,'99',org=self.other);self.credit(second,'25');self.invoice('OTHER',org=self.other)
  expected=InvoiceService.get_invoice_net_receivable(organization=self.org,invoice=first)
  with patch.object(get_db().credit_notes,'find',wraps=get_db().credit_notes.find) as find:rows=Payments._outstanding_invoices(organization=self.org,as_of=self.now)
  self.assertEqual(find.call_count,1)
  self.assertEqual([(str(r['invoice'].id),r['net_receivable']) for r in rows],[(str(first.id),expected)])
  self.assertEqual(expected,Decimal('84.25'))
 def test_read_cache_is_request_and_tenant_scoped(self):
  invoice=self.invoice('I1');token=begin('GET')
  try:
   first=Payments._outstanding_invoices(organization=self.org,as_of=self.now)
   with patch.object(Payments,'_load_outstanding_invoices',side_effect=AssertionError('repeat')):self.assertIs(Payments._outstanding_invoices(organization=self.org,as_of=self.now),first)
   self.assertEqual(Payments._outstanding_invoices(organization=self.other,as_of=self.now),[])
  finally:finish(token)
  self.credit(invoice,'10');self.assertEqual(Payments._outstanding_invoices(organization=self.org,as_of=self.now)[0]['net_receivable'],Decimal('90'))
 def test_writes_do_not_memoize(self):
  token=begin('POST');calls=[]
  try:
   for _ in range(2):read_once('key',lambda:calls.append(1))
  finally:finish(token)
  self.assertEqual(len(calls),2)
 def test_auth_snapshot_reuse_invalidation_and_new_request(self):
  class Session(dict):session_key='session'
  req=NS(session=Session(ims_user_id='one',nexease_session_channel='web'))
  token=begin('GET');self.addCleanup(finish,token)
  with patch.object(Auth,'_load_user',return_value=self.user) as load:
   Auth.get_user(req);Auth.get_user(req);self.assertEqual(load.call_count,1)
   Auth._clear_request_user(req);Auth.get_user(req);self.assertEqual(load.call_count,2)
   Auth.get_user(NS(session=req.session));self.assertEqual(load.call_count,3)
   req.session['ims_user_id']='two';Auth.get_user(req);self.assertEqual(load.call_count,4)
 def view(self,permitted):
  req=RequestFactory().get('/api/v1/invoices/overview/');req.api_user=self.user;req.api_organization=self.org
  view=invoice_overview
  while hasattr(view,'__wrapped__'):view=view.__wrapped__
  with patch('apps.sales.api.v1.invoice_overview_views.AuthorizationService.has_permission',return_value=permitted):return view(req)
 def test_overview_permission_denial(self):self.assertEqual(self.view(False).status_code,403)
 def test_overview_preserves_totals_without_dashboard(self):
  self.invoice('I1')
  with patch('apps.finance.services.main_dashboard_service.MainDashboardService.get_dashboard',side_effect=AssertionError('dashboard called')):data=json.loads(self.view(True).content)['data']
  self.assertEqual(data['kpis'],{'receivables':'100.00','total_sales':'100.00'});self.assertEqual(data['alerts']['overdue_invoices'],1)
 def test_metrics_success_failure_and_no_command_inspection(self):
  token=begin('GET');listener=RequestMongoListener()
  try:
   listener.started(object());listener.succeeded(NS(duration_micros=231200));listener.started(object());listener.failed(NS(duration_micros=1000))
  finally:state=finish(token)
  self.assertEqual(state['mongo_commands'],2);self.assertAlmostEqual(state['mongo_ms'],232.2)
 def test_metrics_reset_on_exception_and_header(self):
  def fail(req):read_once('key',lambda:1);raise ValueError('test')
  with self.assertRaises(ValueError):PerformanceMiddleware(fail)(RequestFactory().get('/test'))
  self.assertEqual(read_once('key',lambda:2),2)
  response=PerformanceMiddleware(lambda req:HttpResponse('ok'))(RequestFactory().get('/test'));self.assertIn('mongo;dur=',response['Server-Timing'])
if __name__=='__main__':unittest.main()
