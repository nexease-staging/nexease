import os,json
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from django.test import SimpleTestCase
from cryptography.fernet import Fernet
from mongoengine.connection import get_db
from apps.core.services import user_mailbox_service as mail
from apps.saas.ai import FIELDS,ITEM_FIELDS,parse_response,match_masters
from apps.products.models import Product,Category
from apps.organizations.models import Organization

class MailboxTests(SimpleTestCase):
 def setUp(self):
  self.user=SimpleNamespace(id=uuid4().hex,email='owner@example.test');self.org=SimpleNamespace(id=uuid4().hex);self.user.organization=self.org
  self.env=patch.dict(os.environ,MAILBOX_ENCRYPTION_KEY=Fernet.generate_key().decode());self.env.start();self.addCleanup(self.env.stop)
 def tearDown(self):get_db().user_mailboxes.delete_many(mail.scope(self.user,self.org))
 @patch('apps.core.services.user_mailbox_service.smtplib.SMTP')
 def test_connect_encrypts_secret_and_uses_registered_sender(self,smtp):
  result=mail.connect(self.user,self.org,'gmail','private-app-password')
  smtp.return_value.__enter__.return_value.login.assert_called_once_with(self.user.email,'private-app-password')
  self.assertTrue(result['connected']);self.assertNotIn('secret',result)
  row=mail.get_mailbox(self.user,self.org);self.assertNotEqual(row['secret'],'private-app-password')
  sender=mail.delivery_options(self.user,self.org);self.assertEqual(sender['from_email'],self.user.email);self.assertEqual(sender['connection'].password,'private-app-password')
  from django.core.mail import EmailMessage
  message=EmailMessage(subject='Test',body='Document',to=['recipient@example.test'],**sender)
  self.assertEqual(message.send(),1)
  self.assertFalse(mail.status(self.user,SimpleNamespace(id='other'))['connected'])
  self.user.email='changed@example.test'
  with self.assertRaises(ValueError):mail.delivery_options(self.user,self.org)
 @patch('apps.core.services.user_mailbox_service.smtplib.SMTP',side_effect=OSError('unreachable'))
 def test_failed_auth_does_not_save_credentials(self,_):
  with self.assertRaises(ValueError):mail.connect(self.user,self.org,'gmail','secret')
  self.assertIsNone(mail.get_mailbox(self.user,self.org))
 def test_unconnected_sender_and_unapproved_host_rejected(self):
  with self.assertRaises(ValueError):mail.delivery_options(self.user,self.org)
  with self.assertRaises(ValueError):mail.connect(self.user,self.org,'localhost','secret')

class AIReviewTests(SimpleTestCase):
 def data(self,kind):return {'kind':kind,'fields':dict.fromkeys(FIELDS,''),'items':[],'questions':[],'warnings':[]}
 def parse(self,data):return parse_response({'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(data)}]}]})
 def test_category_name_and_description_populate_review(self):
  data=self.data('category');data['fields'].update(category='Safety Equipment',description='Helmets and gloves')
  result=self.parse(data);self.assertEqual(result['fields']['name'],'Safety Equipment');self.assertEqual(result['fields']['description'],'Helmets and gloves')
 def test_invoice_preserves_supplied_lines_rates_tax_and_notes(self):
  data=self.data('invoice');data['fields'].update(party_name='Acme',po_number='PO-10',notes='Deliver Monday',supply_type='taxable')
  data['items']=[{**dict.fromkeys(ITEM_FIELDS,''),'name':'Helmet','quantity':'3','unit_price':'500','tax_rate':'18','discount':'0'}]
  result=self.parse(data);self.assertEqual(result['items'][0]['unit_price'],'500');self.assertEqual(result['fields']['po_number'],'PO-10');self.assertEqual(result['fields']['notes'],'Deliver Monday')
 def test_unique_master_fills_missing_price_but_preserves_explicit_price(self):
  org=Organization(name='AI review test',email=f'{uuid4()}@example.test').save();category=Category(organization=org,name='Safety').save()
  product=Product(organization=org,category=category,sku='HELMET',name='Helmet',unit='PCS',selling_price=500).save()
  try:
   data=self.data('invoice');data['items']=[{**dict.fromkeys(ITEM_FIELDS,''),'name':'Helmet'}]
   match_masters(org,data);self.assertEqual(data['items'][0]['sku'],'HELMET');self.assertEqual(float(data['items'][0]['unit_price']),500)
   data['items'][0]['unit_price']='450';match_masters(org,data);self.assertEqual(data['items'][0]['unit_price'],'450')
  finally:product.delete();category.delete();org.delete()
