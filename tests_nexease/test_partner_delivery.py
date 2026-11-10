import bootstrap
import unittest,json,time,hashlib
from datetime import datetime,timedelta
from unittest.mock import patch,Mock
from django.test import RequestFactory,override_settings
from cryptography.fernet import Fernet
from django.core import signing
from mongoengine.connection import get_db
from apps.saas import partner_mail,partner_actions,commissions
from apps.saas.models import PlatformOwner
from apps.organizations.models import Organization
from django.contrib.auth.hashers import make_password,check_password

class DeliveryTests(unittest.TestCase):
 def setUp(self):
  for c in get_db().list_collection_names():get_db().drop_collection(c)
  self.env=patch.dict('os.environ',OWNER_ENCRYPTION_KEY=Fernet.generate_key().decode());self.env.start();self.addCleanup(self.env.stop)
  self.settings=override_settings(FRONTEND_BASE_URL='https://example.com');self.settings.enable();self.addCleanup(self.settings.disable)
  self.p={'_id':'p1','name':'Partner','email':'p@example.com','status':'approved','generation':0,'email_verified':True,'password':make_password('Old#12345')};get_db().saas_partners.insert_one(dict(self.p))
 def token(self,purpose):
  partner_mail.request_link(self.p,purpose)
  row=get_db().partner_mail.find_one({'purpose':purpose})
  from apps.saas.security import cipher
  from urllib.parse import urlparse,parse_qs
  payload=json.loads(cipher().decrypt(row['payload'].encode()))
  return parse_qs(urlparse(payload['message'].split('\n')[-1]).query)['token'][0]
 def test_reset_single_use_revokes_sessions(self):
  token=self.token('reset');partner_mail.consume(token,'reset','NewSecure#3498')
  row=get_db().saas_partners.find_one();self.assertEqual(row['generation'],1);self.assertTrue(check_password('NewSecure#3498',row['password']))
  with self.assertRaises(ValueError):partner_mail.consume(token,'reset','NewSecure#3498')
 def test_verification_wrong_purpose_and_expiry(self):
  token=self.token('verify')
  with self.assertRaises(ValueError):partner_mail.consume(token,'reset','NewSecure#3498')
  get_db().saas_partners.update_one({'_id':'p1'},{'$set':{'verify_expires':datetime.utcnow()-timedelta(seconds=1)}})
  with self.assertRaises(ValueError):partner_mail.consume(token,'verify')
 def test_delivery_replay_and_ambiguity(self):
  partner_mail.queue_welcome('p1','p@example.com');partner_mail.queue_welcome('p1','p@example.com')
  send=Mock();partner_mail.deliver_one(send);partner_mail.deliver_one(send);self.assertEqual(send.call_count,1)
  self.token('reset');failed=Mock(side_effect=TimeoutError());partner_mail.deliver_one(failed);partner_mail.deliver_one(failed)
  self.assertEqual(failed.call_count,1);self.assertEqual(get_db().partner_mail.count_documents({'status':'review_required'}),1)
 def req(self,body=None,owner=False):
  r=RequestFactory().post('/',json.dumps(body),content_type='application/json') if body is not None else RequestFactory().get('/')
  r.session={'nexease_partner':{'id':'p1','generation':0,'at':time.time()}}
  if owner:r.session={'nexease_owner':{'email':'owner@example.com','generation':0,'at':time.time()}}
  return r
 def prepare_commission(self):
  org=Organization(name='Customer',email='customer@example.com').save()
  get_db().saas_referrals.insert_one({'_id':str(org.id),'partner_id':'p1'})
  get_db().saas_payments.insert_one({'_id':'pay1','organization_id':str(org.id),'subscription_id':'sub1','amount_paise':118000,'refunded_paise':0,'mode':'live','paid_at':100})
  commissions.record_tax('pay1','live',18000,0,'INV1','owner','Reviewed invoice')
 def test_owner_payout_recording_idempotent_and_validated(self):
  self.prepare_commission();PlatformOwner(email='owner@example.com',password=make_password('Owner#12345'),totp_secret='unused').save()
  data={'commission_id':'live:pay1','amount_paise':20000,'reference':'BANK123','reason':'Verified paid transfer','password':'Owner#12345','code':'123456'}
  self.assertEqual(partner_actions.payouts(self.req(data)).status_code,401)
  with patch('apps.saas.partner_actions.verify_totp',return_value=True):
   self.assertEqual(partner_actions.payouts(self.req({**data,'amount_paise':1},True)).status_code,400)
   for _ in range(2):self.assertEqual(partner_actions.payouts(self.req(data,True)).status_code,200)
   self.assertEqual(partner_actions.payouts(self.req({**data,'reference':'BANK999'},True)).status_code,400)
  self.assertEqual(get_db().saas_partner_payouts.count_documents({}),1)
 def test_export_scoped_and_formula_safe(self):
  self.prepare_commission()
  get_db().saas_commissions.update_one({'_id':'live:pay1'},{'$set':{'payment_id':'=CMD()'}})
  get_db().saas_commissions.insert_one({'_id':'other','partner_id':'other','mode':'live'})
  r=partner_actions.statement(self.req());self.assertEqual(r.status_code,200);self.assertIn("'=CMD()",r.content.decode());self.assertNotIn('other',r.content.decode())
  get_db().saas_partners.update_one({'_id':'p1'},{'$set':{'email_verified':False}})
  self.assertEqual(partner_actions.statement(self.req()).status_code,403)
 def test_verification_single_use_and_superseded_mail_cancelled(self):
  first=self.token('verify')
  second=self.token('verify')
  # helper selects first row; read the current digest to select the replacement.
  from apps.saas.security import cipher
  from urllib.parse import urlparse,parse_qs
  current=get_db().saas_partners.find_one()['verify_digest']
  row=get_db().partner_mail.find_one({'_id':current})
  data=json.loads(cipher().decrypt(row['payload'].encode()))
  second=parse_qs(urlparse(data['message'].split('\n')[-1]).query)['token'][0]
  with self.assertRaises(ValueError):partner_mail.consume(first,'verify')
  partner_mail.consume(second,'verify')
  with self.assertRaises(ValueError):partner_mail.consume(second,'verify')
  send=Mock()
  while partner_mail.deliver_one(send):pass
  send.assert_not_called()
 def test_pdf_export_and_unverified_owner_approval(self):
  self.prepare_commission()
  r=self.req();r.GET={'format':'pdf'}
  response=partner_actions.statement(r)
  self.assertEqual(response['Content-Type'],'application/pdf')
  self.assertTrue(response.content.startswith(b'%PDF'))
