import os,json
from io import BytesIO,StringIO
from unittest.mock import patch,MagicMock
from urllib.error import HTTPError,URLError
from django.test import SimpleTestCase,RequestFactory
from django.core.cache import cache
from django.core.management import call_command,CommandError
from apps.business.gst_provider import request_json,sandbox_lookup,normalize_taxpayer,configuration,GSTLookupError
class GSTDiagnosticsTests(SimpleTestCase):
 def setUp(self):
  cache.clear();self.env=patch.dict(os.environ,GST_LOOKUP_PROVIDER='sandbox',GST_SANDBOX_ENV='test',GST_SANDBOX_API_KEY='key_test_example',GST_SANDBOX_API_SECRET='secret_test_example',GST_SANDBOX_API_VERSION='');self.env.start();self.addCleanup(self.env.stop)
 def taxpayer(self):return {'code':200,'data':{'status_cd':'1','data':{'gstin':'27ABCDE1234F1Z5','lgnm':'Test Business','pradr':{'addr':{'stcd':'Maharashtra'}}}}}
 def test_missing_and_invalid_configuration_reports_specific_code(self):
  with patch.dict(os.environ,GST_SANDBOX_API_SECRET=''):
   with self.assertRaises(GSTLookupError) as ctx:configuration()
   self.assertEqual(ctx.exception.code,'GST_CONFIG_MISSING')
  with patch.dict(os.environ,GST_SANDBOX_ENV='"live"'):
   with self.assertRaises(GSTLookupError) as ctx:configuration()
   self.assertEqual(ctx.exception.code,'GST_ENV_INVALID')
 def test_live_keys_with_test_host_rejected_without_printing_credentials(self):
  with patch.dict(os.environ,GST_SANDBOX_API_KEY='key_live_private_dont_echo'):
   with self.assertRaises(GSTLookupError) as ctx:configuration()
   self.assertEqual(ctx.exception.code,'GST_ENV_MISMATCH');self.assertNotIn('private_dont_echo',str(ctx.exception))
 def test_pair_mismatch_and_quotes_detected(self):
  with patch.dict(os.environ,GST_SANDBOX_API_SECRET='secret_live_private'):
   with self.assertRaises(GSTLookupError):configuration()
  with patch.dict(os.environ,GST_SANDBOX_API_KEY='"key_test_private"'):
   with self.assertRaises(GSTLookupError) as ctx:configuration()
   self.assertEqual(ctx.exception.code,'GST_CONFIG_INVALID')
 @patch('apps.business.gst_provider.build_opener')
 def test_auth_http_failure_is_safe_and_stage_specific(self,opener):
  body=json.dumps({'message':'secret_test_should_never_echo','transaction_id':'12345678-1234-1234-1234-123456789abc'}).encode();opener.return_value.open.side_effect=HTTPError('https://test-api.sandbox.co.in/authenticate',401,'Unauthorized',{},BytesIO(body))
  with self.assertRaises(GSTLookupError) as ctx:request_json('https://test-api.sandbox.co.in/authenticate',{},None)
  e=ctx.exception;self.assertEqual(e.code,'GST_AUTH_REJECTED');self.assertEqual(e.stage,'authentication');self.assertNotIn('should_never_echo',e.public_message());self.assertIn('12345678-1234',e.public_message())
 @patch('apps.business.gst_provider.build_opener')
 def test_forbidden_billing_rate_and_service_statuses_are_distinct(self,opener):
  for status,code in [(403,'GST_ACCESS_DENIED'),(402,'GST_PROVIDER_BILLING'),(429,'GST_PROVIDER_LIMIT'),(503,'GST_PROVIDER_UNAVAILABLE')]:
   opener.return_value.open.side_effect=HTTPError('https://test-api.sandbox.co.in/gst/compliance/public/gstin/search',status,'Error',{},BytesIO(b'{}'))
   with self.assertRaises(GSTLookupError) as ctx:request_json('https://test-api.sandbox.co.in/gst/compliance/public/gstin/search',{}, {})
   self.assertEqual(ctx.exception.code,code)
 @patch('apps.business.gst_provider.build_opener')
 def test_network_and_bad_json_are_distinct(self,opener):
  opener.return_value.open.side_effect=URLError('private network details')
  with self.assertRaises(GSTLookupError) as ctx:request_json('https://test-api.sandbox.co.in/authenticate',{},None)
  self.assertEqual(ctx.exception.code,'GST_NETWORK_ERROR')
  opener.return_value.open.side_effect=None;opener.return_value.open.return_value.__enter__.return_value.read.return_value=b'<html>not json</html>'
  with self.assertRaises(GSTLookupError) as ctx:request_json('https://test-api.sandbox.co.in/authenticate',{},None)
  self.assertEqual(ctx.exception.code,'GST_RESPONSE_INVALID')
 def test_http_200_business_error_is_not_misclassified_as_bad_gstin(self):
  with self.assertRaises(GSTLookupError) as ctx:normalize_taxpayer({'code':200,'data':{'status_cd':'0','error':{'error_cd':'FO8000','message':'Do not echo this'}}},'27ABCDE1234F1Z5')
  self.assertEqual(ctx.exception.code,'GST_NOT_FOUND');self.assertNotIn('Do not echo',str(ctx.exception))
 def test_demo_gstin_mismatch_is_never_applied_to_real_customer(self):
  with self.assertRaises(GSTLookupError) as ctx:normalize_taxpayer(self.taxpayer(),'29ABCDE1234F1Z5')
  self.assertEqual(ctx.exception.code,'GST_GSTIN_MISMATCH')
 @patch('apps.business.gst_provider.request_json')
 def test_auth_no_body_token_raw_default_search_version(self,req):
  req.side_effect=[{'code':200,'data':{'access_token':'private-token'}},self.taxpayer()];sandbox_lookup('27ABCDE1234F1Z5')
  self.assertIsNone(req.call_args_list[0].args[2]);headers=req.call_args_list[1].args[1];self.assertEqual(headers['authorization'],'private-token');self.assertEqual(headers['x-api-version'],'1.0.0');self.assertNotIn('x-api-secret',headers)
 @patch('apps.business.gst_provider.request_json')
 def test_expired_token_refreshed_exactly_once(self,req):
  req.side_effect=[{'data':{'access_token':'old'}},GSTLookupError('GST_AUTH_REJECTED','expired',status=401),{'data':{'access_token':'new'}},self.taxpayer()];result=sandbox_lookup('27ABCDE1234F1Z5');self.assertEqual(result['name'],'Test Business');self.assertEqual(req.call_count,4)
 @patch('apps.business.gst_provider.request_json')
 def test_missing_auth_data_gives_actionable_error_not_attribute_error(self,req):
  req.return_value={'code':200,'data':'bad'}
  with self.assertRaises(GSTLookupError) as ctx:sandbox_lookup('27ABCDE1234F1Z5')
  self.assertEqual(ctx.exception.code,'GST_AUTH_RESPONSE_INVALID')
 @patch('apps.business.gst_provider.request_json')
 def test_config_command_does_not_authenticate_or_print_keys(self,req):
  out=StringIO();call_command('check_gst_lookup',stdout=out);req.assert_not_called();self.assertNotIn('key_test_example',out.getvalue());self.assertIn('NOT authenticated',out.getvalue())
 @patch('apps.business.gst_provider.sandbox_lookup')
 @patch('apps.business.gst_lookup.permitted',return_value=True)
 def test_lookup_api_returns_specific_error_instead_of_generic_message(self,permitted,lookup):
  from apps.business.gst_lookup import lookup as view
  lookup.side_effect=GSTLookupError('GST_ENV_MISMATCH','Key environment and backend environment differ.')
  req=RequestFactory().get('/api/v1/business/gst-lookup/?gstin=27ABCDE1234F1Z5')
  # Bypass authentication and rate-limit wrappers for focused response regression.
  fn=view
  while hasattr(fn,'__wrapped__'):fn=fn.__wrapped__
  response=fn(req);self.assertEqual(response.status_code,400);self.assertIn(b'GST_ENV_MISMATCH',response.content);self.assertNotIn(b'Check provider credentials, access, environment and GSTIN',response.content)
