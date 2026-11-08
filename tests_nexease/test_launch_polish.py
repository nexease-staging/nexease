import bootstrap
import unittest,json,os,tempfile
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace as NS
from unittest.mock import patch
from pathlib import Path
from io import BytesIO
from django.test import RequestFactory
from mongoengine.connection import get_db
from openpyxl import load_workbook
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.sales.models import Invoice,Customer,InvoiceItem
from apps.products.models import Product,Category
from apps.business.models import BusinessRecord as Record
from apps.business.gst_provider import normalize_taxpayer
from apps.business.gst_review_sources import candidate
from apps.business.billing import tax_heads
from apps.business.professional_documents import amount_words,retail_invoice,salary_slip
from apps.business.taxation import gst_report
from apps.business.views import validate

class LaunchPolishTests(unittest.TestCase):
 def setUp(self):
  get_db().client.drop_database(get_db().name)
  self.org=Organization(name='NexEase Demo Trading',email='demo@example.test',address='Demo Road, Pune, Maharashtra 411001',phone='9000000000').save()
  self.user=User(organization=self.org,email='user@example.test',password='test',first_name='Demo',last_name='Admin').save()
  self.customer=Customer(organization=self.org,code='DEMO',name='Demo Customer').save(validate=False)
  category=Category(organization=self.org,name='Goods').save()
  self.product=Product(organization=self.org,category=category,name='Water bottles',sku='W1',unit='PCS').save(validate=False)
 def invoice(self,interstate=False):
  return Invoice(organization=self.org,customer=self.customer,invoice_number='DEMO-001',invoice_date=datetime(2026,11,1),due_date=datetime(2026,11,20),billing_name='Demo Customer',billing_address='Demo Road, Pune',customer_gstin='',created_by=self.user,status='ISSUED',subtotal=Decimal('1000'),tax_amount=Decimal('180'),total_amount=Decimal('1180'),balance_due=Decimal('1180'),items=[InvoiceItem(product=self.product,item_name='Water bottles',unit='PCS',hsn_code='220110',item_type='goods',quantity=Decimal('10'),unit_price=Decimal('100'),tax_rate=Decimal('18'),line_subtotal=Decimal('1000'),line_tax=Decimal('180'),line_total=Decimal('1180'))],billing_details={'tax_reviewed':True,'supply_type':'taxable','supplier_state':'27','supplier_gstin':'27AAACQ3770E2Z0','place_of_supply':'24' if interstate else '27','template':'retail_blue','terms':'Payment due within 15 days.','bank_details':'Demo bank details - sample only','signatory':'Authorised signatory'}).save(validate=False)
 def test_tax_heads_intra_and_interstate(self):
  inv=self.invoice();self.assertEqual(tax_heads(inv),(Decimal('90'),Decimal('90'),Decimal('0')))
  inv.billing_details['place_of_supply']='24';self.assertEqual(tax_heads(inv),(Decimal('0'),Decimal('0'),Decimal('180')))
 def test_lookup_structured_address_and_only_real_contacts(self):
  gst='27AAACQ3770E2Z0';data={'gstin':gst,'lgnm':'Demo','pradr':{'addr':{'dst':'Pune','stcd':'Maharashtra','pncd':'411001'}},'email':'demo@example.test','mobNum':'9000000000'}
  result=normalize_taxpayer({'data':data},gst);self.assertEqual((result['city'],result['country'],result['pincode']),('Pune','India','411001'));self.assertEqual(result['email'],'demo@example.test')
  data['email']='a***@example.test';data['mobNum']='98XXXX1234';result=normalize_taxpayer({'data':data},gst);self.assertEqual(result['email'],'');self.assertEqual(result['phone'],'')
 def test_review_suggestion_keeps_itc_unconfirmed_and_matches_heads(self):
  inv=self.invoice();row=candidate(inv,'invoice',set());self.assertFalse(row['data']['itc_eligible']);self.assertTrue(row['automatically_in_report']);self.assertEqual(row['data']['cgst'],'90.00')
  inv.billing_details={};row=candidate(inv,'invoice',set());self.assertIn('cgst',row['missing']);self.assertEqual(row['data']['supply'],'')
 def test_source_cannot_be_linked_twice(self):
  data=dict(document_number='I1',date='2026-11-01',direction='outward',supply='taxable',party_gstin='',party_name='Demo',place_of_supply='27',hsn='220110',taxable='100',cgst='9',sgst='9',igst='0',cess='0',itc_eligible=False,source_reference='same-source',note='')
  Record(organization=self.org,created_by=self.user,kind='gst_adjustments',key='outward:I1',data=data).save()
  data=dict(data,document_number='I2')
  with self.assertRaisesRegex(ValueError,'already has'):validate('gst_adjustments',data,self.org)
 def test_workpaper_totals_and_calculation_sheet(self):
  self.invoice();req=RequestFactory().get('/api/v1/business/gst/export/',{'from':'2026-11-01','to':'2026-11-30','form':'GSTR-3B'});req.api_user=self.user;req.api_organization=self.org
  view=gst_report
  while hasattr(view,'__wrapped__'):view=view.__wrapped__
  with patch('apps.business.taxation.permitted',return_value=True):response=view(req)
  self.assertEqual(response.status_code,200);book=load_workbook(BytesIO(response.content),data_only=True)
  rows=list(book['Reviewed register'].values);self.assertEqual(rows[1][8:12],(1000,90,90,0));self.assertIn('Calculation checks',book.sheetnames)
 def test_email_diagnostic_never_sends_or_prints_credentials(self):
  from django.core.management import call_command
  from io import StringIO
  import os
  output=StringIO()
  with patch.dict(os.environ,MAILBOX_ENCRYPTION_KEY='not-a-valid-key',OWNER_ENCRYPTION_KEY='owner-private-marker'):
   get_db().user_mailboxes.insert_one({'secret':'mailbox-private-marker'})
   call_command('check_email_delivery',stdout=output)
  text=output.getvalue();self.assertIn('unreadable_mailboxes',text);self.assertNotIn('owner-private-marker',text);self.assertNotIn('mailbox-private-marker',text)
 def test_all_workpaper_variants_export_same_reviewed_source_amounts(self):
  self.invoice();view=gst_report
  while hasattr(view,'__wrapped__'):view=view.__wrapped__
  for form in ('GSTR-1','GSTR-3B','GSTR-9'):
   req=RequestFactory().get('/api/v1/business/gst/export/',{'from':'2026-11-01','to':'2026-11-30','form':form});req.api_user=self.user;req.api_organization=self.org
   with patch('apps.business.taxation.permitted',return_value=True):response=view(req)
   book=load_workbook(BytesIO(response.content),data_only=True);row=list(book['Reviewed register'].values)[1]
   self.assertEqual(row[8:12],(1000,90,90,0))
 def test_amount_words_indian_grouping_and_paise(self):
  self.assertEqual(amount_words('214760'),'Two Lakh Fourteen Thousand Seven Hundred Sixty Rupees Only');self.assertIn('Twenty Five Paise',amount_words('1.25'))
 def test_pdf_layouts_and_stress_invoice(self):
  inv=self.invoice();out=Path(os.environ.get('NEXEASE_QA_OUTPUT',str(Path(tempfile.gettempdir())/'NexEase-Document-QA')));out.mkdir(parents=True,exist_ok=True)
  for template in ('retail_blue','retail_emerald'):
   inv.billing_details['template']=template;blob=retail_invoice(inv,{});self.assertTrue(blob.startswith(b'%PDF'));(out/(template+'.pdf')).write_bytes(blob)
  row={'employee':{'name':'Demo Employee','code':'EMP-001'},'result':{'base':'26000','overtime':'1000','additions':'3000','gross':'30000','pf':'1800','esi':'0','deductions':'2000','net':'28000','employer_pf':'1800','employer_esi':'0'},'inputs':{'professional_tax':'200'}}
  blob=salary_slip(self.org,NS(key='2026-11',id='DEMO-RUN',data={'status':'approved'}),row,{});self.assertTrue(blob.startswith(b'%PDF'));(out/'professional_payslip.pdf').write_bytes(blob)
  inv.items=list(inv.items)*40;inv.subtotal=Decimal('40000');inv.tax_amount=Decimal('7200');inv.total_amount=Decimal('47200');inv.balance_due=Decimal('47200');blob=retail_invoice(inv,{});self.assertTrue(blob.startswith(b'%PDF'));(out/'long_invoice_qa.pdf').write_bytes(blob)
if __name__=='__main__':unittest.main()
