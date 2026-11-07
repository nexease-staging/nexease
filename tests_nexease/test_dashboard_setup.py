import bootstrap
import unittest,json
from unittest.mock import patch
from django.test import RequestFactory
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.authorization.models import Role
from apps.business.models import BusinessRecord
from apps.business.views import configuration
class DashboardSetupTests(unittest.TestCase):
 def setUp(self):
  get_db().client.drop_database(get_db().name)
  self.org=Organization(name="Demo",email="demo@example.com").save()
  self.user=User(organization=self.org,email="admin@example.com",password="test",first_name="Demo",last_name="Admin").save()
  self.user.role=Role(organization=self.org,name="Admin",is_system=True).save();self.user.save()
 def status(self):
  req=RequestFactory().get('/api/v1/business/configuration/')
  req.api_user=self.user;req.api_organization=self.org
  view=configuration
  while hasattr(view,'__wrapped__'):view=view.__wrapped__
  return json.loads(view(req).content)['data']
 def settings(self,**data):
  BusinessRecord(organization=self.org,created_by=self.user,kind="invoice_settings",key="default",data=data).save()
 def test_new_business_is_incomplete(self):
  self.assertEqual(self.status()['setup'],dict(logo=False,email=False,bank=False))
 def test_all_settings_completed(self):
  self.settings(logo="data:image/png;base64,example",bank_details="Account details configured")
  get_db().user_mailboxes.insert_one(dict(user_id=str(self.user.id),organization_id=str(self.org.id),email=self.user.email,secret="NEVER-RETURN-THIS",provider="gmail"))
  response=self.status()
  self.assertEqual(response['setup'],dict(logo=True,email=True,bank=True))
  self.assertNotIn("NEVER-RETURN-THIS",json.dumps(response))
 def test_whitespace_bank_does_not_mark_complete(self):
  self.settings(logo="",bank_details="  ")
  self.assertFalse(self.status()['setup']['bank'])
 def test_mailbox_is_per_user_and_organisation(self):
  get_db().user_mailboxes.insert_one(dict(user_id="different",organization_id=str(self.org.id),email=self.user.email))
  get_db().user_mailboxes.insert_one(dict(user_id=str(self.user.id),organization_id="different",email=self.user.email))
  self.assertFalse(self.status()['setup']['email'])
 def test_changed_email_needs_reconnection(self):
  get_db().user_mailboxes.insert_one(dict(user_id=str(self.user.id),organization_id=str(self.org.id),email="old@example.com"))
  self.assertFalse(self.status()['setup']['email'])
if __name__=="__main__":unittest.main()
