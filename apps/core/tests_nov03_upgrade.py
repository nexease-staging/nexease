import json,os
from datetime import datetime,timedelta
from uuid import uuid4
from unittest.mock import patch
from django.test import SimpleTestCase,RequestFactory
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.authorization.models import Role,Permission
from apps.business.models import BusinessRecord
from apps.business.views import records,permitted
from apps.business.upgrade_api import employee_payables
from apps.saas.entitlements import grant_signup_trial,require
from apps.saas.models import Membership
from apps.core.quotation import quotation,deliver_one
from apps.finance.models import JournalEntry

class UpgradeTests(SimpleTestCase):
 def setUp(self):
  self.key=uuid4().hex
  self.org=Organization(name='Upgrade test',email=self.key+'@example.com').save()
  codes=['expenses.manage','expenses.read','payroll.manage','payroll.read']
  for code in codes:Permission.objects(code=code).update_one(upsert=True,set__name=code,set__is_active=True)
  self.role=Role(organization=self.org,name='Admin',is_system=True,permissions=list(Permission.objects(code__in=codes))).save()
  self.user=User(organization=self.org,role=self.role,email=self.key+'user@example.com',password='test',first_name='Test',last_name='User').save()
  self.emp=BusinessRecord(organization=self.org,created_by=self.user,kind='employees',key='E1',data={'name':'Rahul','code':'E1','active':True}).save()
 def req(self,data=None):
  r=RequestFactory().post('/',json.dumps(data or {}),content_type='application/json') if data is not None else RequestFactory().get('/')
  r.api_user=self.user;r.api_organization=self.org
  return r
 def tearDown(self):
  from apps.finance.models import ChartOfAccount
  JournalEntry.objects(organization=self.org).delete();ChartOfAccount.objects(organization=self.org).delete()
  BusinessRecord.objects(organization=self.org).delete();Membership.objects(organization_id=str(self.org.id)).delete();self.user.delete();self.role.delete();self.org.delete()
 def test_expense_advance_is_one_canonical_advance_and_one_journal(self):
  data={'category':'Employee advance','payee':'Rahul','employee_id':str(self.emp.id),'date':'2026-11-03','amount':'1000','description':'Advance','reference':self.key,'payment_mode':'Cash'}
  response=records.__wrapped__(self.req({'data':data}),kind='expenses')
  self.assertEqual(response.status_code,200,response.content)
  self.assertEqual(BusinessRecord.objects(organization=self.org,kind='expenses').count(),0)
  self.assertEqual(BusinessRecord.objects(organization=self.org,kind='advances').count(),1)
  self.assertEqual(JournalEntry.objects(organization=self.org,source_type='EMPLOYEE_ADVANCE').count(),1)
  response=records.__wrapped__(self.req({'data':data}),kind='expenses')
  self.assertEqual(response.status_code,400)
  self.assertEqual(JournalEntry.objects(organization=self.org).count(),1)
 def test_advance_requires_payroll_permission(self):
  self.role.permissions=list(Permission.objects(code='expenses.manage'));self.role.save();self.user.reload()
  response=records.__wrapped__(self.req({'data':{'category':'Employee advance'}}),kind='expenses')
  self.assertEqual(response.status_code,403)
 def test_salary_ap_subtracts_payments_and_excludes_drafts(self):
  data={'status':'approved','rows':[{'employee_id':str(self.emp.id),'employee':{'name':'Rahul'},'result':{'net':'10000'}}],'payments':[{'employee_id':str(self.emp.id),'amount':'2500'}]}
  run=BusinessRecord(organization=self.org,created_by=self.user,kind='payruns',key='2026-11',data=data).save()
  response=employee_payables.__wrapped__(self.req());self.assertEqual(json.loads(response.content)['data']['total'],'7500.00')
  run.update(set__data__status='draft')
  response=employee_payables.__wrapped__(self.req());self.assertEqual(json.loads(response.content)['data']['total'],'0.00')
 def test_trial_is_plus_14_days_and_never_resets(self):
  grant_signup_trial(self.org);m=Membership.objects.get(organization_id=str(self.org.id))
  self.assertEqual(m.plan,'plus');self.assertEqual(m.end-m.start,timedelta(days=14));self.assertNotIn('ai',m.features)
  end=m.end;grant_signup_trial(self.org);m.reload();self.assertEqual(m.end,end)
  m.end=datetime.utcnow()-timedelta(days=1);m.save()
  with patch.dict(os.environ,SAAS_ENFORCEMENT='true'):
   with self.assertRaises(Exception):require(self.org,write=True)
 def test_permission_snapshot_rejects_cross_tenant_role(self):
  self.assertTrue(permitted(self.req(),'payroll.manage'))
  self.role.organization=Organization(name='Other',email=self.key+'other@example.com').save();self.role.save()
  self.user.reload();self.assertFalse(permitted(self.req(),'payroll.manage'));self.role.organization.delete()
 def test_quotation_is_saved_and_sent_to_fixed_inbox(self):
  data={'name':'Test','email':'test@example.com','message':'Need inventory','consent':True,'to':'attacker@example.com'}
  with patch('apps.core.quotation.rate'):
   response=quotation(self.req(data))
  self.assertEqual(response.status_code,200,response.content)
  key=json.loads(response.content)['data']['reference']
  with patch.dict(os.environ,EMAIL_MODE='production',CONTACT_EMAIL='nexease.contact@gmail.com'),patch('django.core.mail.EmailMessage') as message,patch('django.core.mail.get_connection'):
   message.return_value.send.return_value=1;deliver_one()
   self.assertEqual(message.call_args.kwargs['to'],['nexease.contact@gmail.com'])
   self.assertEqual(message.call_args.kwargs['reply_to'],['test@example.com'])
  self.assertEqual(get_db().nexease_quotations.find_one({'_id':key})['status'],'sent');get_db().nexease_quotations.delete_one({'_id':key})
 def test_quotation_rejects_invalid_email_and_missing_consent(self):
  with patch('apps.core.quotation.rate'):
   self.assertEqual(quotation(self.req({'name':'X','email':'bad','message':'Hello','consent':True})).status_code,400)
   self.assertEqual(quotation(self.req({'name':'X','email':'x@example.com','message':'Hello'})).status_code,400)
