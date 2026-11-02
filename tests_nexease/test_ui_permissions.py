import bootstrap
import json,unittest
from unittest.mock import patch
from django.http import JsonResponse
from django.test import RequestFactory
from test_oct31_workflows import WorkflowTests
from apps.business.billing import invoice_details
from apps.business.pro_api import invoice_descriptions
from apps.authorization.models import Role
from apps.core.middleware.security_response_middleware import SecurityResponseMiddleware

class IssuedInvoiceRules(WorkflowTests):
 def test_admin_can_correct_issued_presentation_only(self):
  inv=self.invoice();inv.status='ISSUED';inv.billing_details={'supply_type':'unregistered','place_of_supply':''};inv.save()
  before=inv.total_amount
  res=self.call(invoice_details,{'po_number':'PO-42','supply_type':'unregistered'},invoice_id=str(inv.id))
  self.assertEqual(res.status_code,200,res.content);inv.reload();self.assertEqual(inv.billing_details['po_number'],'PO-42');self.assertEqual(inv.total_amount,before)
  res=self.call(invoice_details,{'supply_type':'taxable'},invoice_id=str(inv.id));self.assertEqual(res.status_code,400)
 def test_nonadmin_cannot_edit_issued_when_toggle_off(self):
  inv=self.invoice();inv.status='ISSUED';inv.save();self.org.invoice_admin_only=False;self.org.save()
  self.user.role=Role(organization=self.org,name='Sales',is_system=False).save();self.user.save()
  self.assertEqual(self.call(invoice_details,{'po_number':'bad'},invoice_id=str(inv.id)).status_code,403)
  self.assertEqual(self.call(invoice_descriptions,{'items':[{'description':'bad','show':True}]},invoice_id=str(inv.id)).status_code,403)
 def test_cost_redacted_from_nested_json(self):
  req=RequestFactory().get('/api/v1/products/');req.api_user=self.user
  response=lambda _:JsonResponse({'data':{'products':[{'name':'P','cost_price':'42','selling_price':'90'}]}})
  with patch('apps.core.services.cost_visibility.can_read_cost',return_value=False):
   body=json.loads(SecurityResponseMiddleware(response)(req).content)
  self.assertNotIn('cost_price',body['data']['products'][0]);self.assertEqual(body['data']['products'][0]['selling_price'],'90')
 def test_authorized_cost_retained(self):
  req=RequestFactory().get('/api/v1/products/');req.api_user=self.user
  with patch('apps.core.services.cost_visibility.can_read_cost',return_value=True):
   res=SecurityResponseMiddleware(lambda _:JsonResponse({'cost_price':'42'}))(req)
  self.assertEqual(json.loads(res.content)['cost_price'],'42')
