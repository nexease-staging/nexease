import bootstrap
import unittest,json,zipfile,io
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from django.test import RequestFactory
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.authorization.models import Role
from apps.business.models import BusinessRecord as Record
from apps.business.books import ensure_accounts,sync_record,payment_account
from apps.business.pro_api import bulk_assign,modules,invoice_descriptions,accountant_export,lookup
from apps.business.flow_api import daily_work
from apps.business.views import validate,records
from apps.business.automation import payrow
from apps.finance.models import JournalEntry,ChartOfAccount
from apps.sales.models import Customer,Invoice,InvoiceItem
from apps.products.models import Product,Category
from apps.sales.services.invoice_service import InvoiceService
from apps.finance.documents.invoice_pdf import InvoicePDF

class ProfessionalTests(unittest.TestCase):
 def setUp(self):
  for c in get_db().list_collection_names():get_db().drop_collection(c)
  self.org=Organization(name='Pro test',email='pro@example.com').save();self.user=User(organization=self.org,email='admin@example.com',password='test',first_name='Pro',last_name='Test').save()
  self.user.role=Role(organization=self.org,name='Admin',is_system=True).save();self.user.save()
  self.other=Organization(name='Other',email='other@example.com').save()
 def record(self,kind,key,data):return Record(organization=self.org,created_by=self.user,kind=kind,key=key,data=data).save()
 def employee(self,code='E1',internal=False):return self.record('employees',code,dict(code=code,name=code,joining_date='2026-01-01',basis='daily',rate='500',active=True,employment_type='inhouse' if internal else 'site'))
 def call(self,view,data=None,method='POST',allowed=True,**kwargs):
  req=RequestFactory().get('/',data or {}) if method=='GET' else RequestFactory().post('/',json.dumps(data or {}),content_type='application/json');req.api_user=self.user;req.api_organization=self.org
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=allowed):return view.__wrapped__(req,**kwargs)
 def test_setup_is_idempotent_and_tenant_scoped(self):
  ensure_accounts(self.org,self.user);n=ChartOfAccount.objects.count();ensure_accounts(self.org,self.user);self.assertEqual(ChartOfAccount.objects.count(),n);self.assertFalse(ChartOfAccount.objects(organization=self.other))
 def test_setup_does_not_replace_conflicting_account(self):
  ChartOfAccount(organization=self.org,created_by=self.user,account_code='1100',account_name='Existing custom',account_type='ASSET',normal_balance='DEBIT',system_key='CUSTOM').save()
  with self.assertRaisesRegex(ValueError,'already used'):ensure_accounts(self.org,self.user)
  self.assertEqual(ChartOfAccount.objects(account_code='1100').first().system_key,'CUSTOM')
 def test_expense_posts_balanced_and_retry_is_safe(self):
  x=self.record('expenses','X1',dict(date='2026-09-02',category='Travel',description='Taxi',amount='250',payment_mode='Cash',payment_account='',reference='R1'))
  sync_record(x,self.user);sync_record(x,self.user);j=JournalEntry.objects.get();self.assertEqual(j.total_debit,Decimal('250'));self.assertEqual(j.total_credit,Decimal('250'));self.assertEqual(j.status,'POSTED');self.assertEqual(j.lines[1].account.system_key,'CASH')
 def test_credit_card_uses_liability(self):
  ensure_accounts(self.org,self.user);self.assertEqual(payment_account(self.org,'Credit card').account_type,'LIABILITY')
 def test_payment_account_cannot_cross_tenants(self):
  ensure_accounts(self.other,self.user);a=ChartOfAccount.objects(organization=self.other,system_key='BANK').first()
  with self.assertRaises(ValueError):payment_account(self.org,'Bank transfer',str(a.id))
 def test_opening_recovery_requires_review(self):
  x=self.record('advances','A',dict(date='2026-09-01',amount='500',recovered='100',reference='A'))
  with self.assertRaisesRegex(ValueError,'opening'):sync_record(x,self.user)
  self.assertEqual(JournalEntry.objects.count(),0)
 def test_payroll_and_payment_journals(self):
  e=self.employee();self.record('timesheets','T',dict(employee_id=str(e.id),date='2026-09-01',hours='8',overtime_hours='0',status='approved'))
  a=self.record('advances','A',dict(employee_id=str(e.id),date='2026-09-01',amount='100',recovered='0',reference='A',payment_mode='Cash'));sync_record(a,self.user)
  row=payrow(self.org,e,'2026-09',{},'automatic');r=self.record('payruns','2026-09',dict(status='approved',rows=[row],payments=[dict(employee_id=str(e.id),amount='200',reference='P',date='2026-09-30',payment_mode='UPI')]))
  sync_record(r,self.user);sync_record(r,self.user);self.assertEqual(JournalEntry.objects.count(),3)
  for j in JournalEntry.objects:self.assertEqual(j.total_debit,j.total_credit)
  salary=ChartOfAccount.objects(system_key='SALARY_PAYABLE').first();balance=sum((l.credit-l.debit for j in JournalEntry.objects for l in j.lines if l.account.id==salary.id),Decimal(0));self.assertEqual(balance,200)
 def test_internal_staff_needs_no_assignment(self):
  e=self.employee(internal=True)
  r=self.call(daily_work,{'date':'2026-09-01'},'GET');row=json.loads(r.content)['data']['rows'][0];self.assertEqual(row['site_id'],'internal')
  r=self.call(daily_work,{'date':'2026-09-01','rows':[{'assignment_id':row['assignment_id'],'hours':'8','billable_units':'99'}]});self.assertEqual(r.status_code,200,r.content)
  work=Record.objects(kind='timesheets').get();self.assertEqual(work.data['billable_units'],'0');self.assertEqual(payrow(self.org,e,'2026-09',{},'automatic')['result']['gross'],'500.00')
 def test_site_worker_cannot_use_internal_timesheet(self):
  e=self.employee()
  with self.assertRaisesRegex(ValueError,'site'):validate('timesheets',dict(employee_id=str(e.id),date='2026-09-01',shift='OFFICE',hours='8',billable_units='0',billing_rate='0',status='approved'),self.org)
 def test_bulk_different_rates_and_retry(self):
  e=self.employee();f=self.employee('E2');site=self.record('sites','S',dict(name='Site',code='S',billing_rate='800',active=True))
  p=dict(site_id=str(site.id),start_date='2026-09-01',end_date='2026-09-30',shift='DAY',rows=[dict(employee_id=str(e.id),billing_rate='900'),dict(employee_id=str(f.id),billing_rate='')])
  r=self.call(bulk_assign,p);self.assertEqual(r.status_code,200,r.content);r=self.call(bulk_assign,p);self.assertEqual(r.status_code,200,r.content);self.assertEqual(Record.objects(kind='assignments').count(),2)
  self.assertEqual({a.data['billing_rate'] for a in Record.objects(kind='assignments')},{'900','800'})
 def test_bulk_invalid_row_writes_nothing(self):
  e=self.employee();site=self.record('sites','S',dict(name='Site',code='S',billing_rate='800',active=True))
  p=dict(site_id=str(site.id),start_date='2026-09-01',end_date='2026-09-30',shift='DAY',rows=[dict(employee_id=str(e.id)),dict(employee_id='bad')]);r=self.call(bulk_assign,p);self.assertEqual(r.status_code,400);self.assertEqual(Record.objects(kind='assignments').count(),0)
 def test_module_switch_permission_and_persistence(self):
  r=self.call(modules,dict(workforce=False,expenses=True),allowed=False);self.assertEqual(r.status_code,403)
  r=self.call(modules,dict(workforce=False,expenses=True));self.assertEqual(r.status_code,200);self.org.reload();self.assertFalse(self.org.workforce_enabled)
 def invoice(self):
  c=Customer(organization=self.org,code='C',name='Client').save();cat=Category(organization=self.org,name='Service').save();p=Product(organization=self.org,sku='SERVICE',name='Service',category=cat,unit='PCS').save()
  return Invoice(organization=self.org,invoice_number='INV-TEST',customer=c,billing_name='Client',invoice_date=datetime(2026,9,30),items=[InvoiceItem(product=p,quantity=1,unit_price=100,line_subtotal=100,line_total=100)],subtotal=100,total_amount=100,balance_due=100,created_by=self.user).save()
 def test_invoice_issue_repairs_missing_receivable(self):
  inv=self.invoice()
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True):InvoiceService.issue_invoice(user=self.user,organization=self.org,invoice_id=str(inv.id))
  inv.reload();self.assertEqual(inv.status,'ISSUED');self.assertEqual(JournalEntry.objects(source_type='SALES_INVOICE',status='POSTED').count(),1)
 def test_descriptions_pdf_and_draft_guard(self):
  inv=self.invoice();r=self.call(invoice_descriptions,{'items':[{'description':'Packing service <checked>','show':True}]},invoice_id=str(inv.id));self.assertEqual(r.status_code,200,r.content);inv.reload();self.assertTrue(inv.items[0].show_description)
  pdf=InvoicePDF.generate(invoice=inv) if hasattr(InvoicePDF,'generate') else None
  self.assertTrue(pdf and pdf.startswith(b'%PDF'))
  inv.status='ISSUED';inv.save();self.assertEqual(self.call(invoice_descriptions,{'items':[{'description':'New','show':False}]},invoice_id=str(inv.id)).status_code,400)
 def test_export_contains_books_and_escapes_formulas(self):
  self.invoice();x=self.record('expenses','X',dict(date='2026-09-02',category='Travel',description='=danger',payee='Taxi',amount='250',payment_mode='Cash',reference='R'));sync_record(x,self.user)
  r=self.call(accountant_export,{'from':'2026-09-01','to':'2026-09-30'},'GET');self.assertEqual(r.status_code,200,r.content[:200]);z=zipfile.ZipFile(io.BytesIO(r.content));self.assertIn('Sales.csv',z.namelist());self.assertIn('General_ledger.csv',z.namelist());self.assertIn("'=danger",z.read('expenses.csv').decode());self.assertIn('250.00',z.read('Trial_balance.csv').decode())
 def test_lookup_tenant_and_permission(self):
  Customer(organization=self.org,code='C1',name='Alpha').save();Customer(organization=self.other,code='C2',name='Alpha other').save()
  r=self.call(lookup,{'kind':'customers','q':'alpha'},'GET');self.assertEqual(len(json.loads(r.content)['data']['records']),1)
  self.assertEqual(self.call(lookup,{'kind':'customers'},'GET',allowed=False).status_code,403)
if __name__=='__main__':unittest.main(verbosity=2)
