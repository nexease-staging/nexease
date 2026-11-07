"""Optional business address is validated before account creation and retained."""
import bootstrap
import unittest
from mongoengine.connection import get_db
from django.core.management import call_command
from apps.accounts.organization_signup_service import OrganizationSignupService,OrganizationSignupError
class SignupAddressTest(unittest.TestCase):
 def setUp(self):
  get_db().client.drop_database(get_db().name)
  call_command("seed_permissions",verbosity=0)
 def account(self,**patch):
  return OrganizationSignupService.create_organization_account(organization_name="UI QA",organization_email="office@example.com",first_name="Demo",last_name="Admin",user_email="admin@example.com",password="Secure-demo-2026!",**patch)
 def test_address_is_saved(self):
  result=self.account(address="  Pune, Maharashtra 411001  ")
  self.assertEqual(result["organization"].reload().address,"Pune, Maharashtra 411001")
 def test_old_clients_can_omit_address(self):
  self.assertEqual(self.account()["organization"].address,"")
 def test_invalid_address_creates_no_organisation(self):
  from apps.organizations.models import Organization
  for value in ["x"*501,{"street":"invalid"}]:
   with self.assertRaises(OrganizationSignupError):self.account(address=value)
  self.assertEqual(Organization.objects.count(),0)
if __name__=="__main__":unittest.main()
