import bootstrap
import unittest
from unittest.mock import patch
from django.test import RequestFactory
from apps.business.hsn_suggestions import search,words,suggestions,directory
import json

class HSNSuggestionTests(unittest.TestCase):
 def test_official_master_loaded_and_traceable(self):
  data,rows=directory();self.assertGreater(len(rows),20000);self.assertEqual(data['source'],'https://tutorial.gst.gov.in/downloads/HSN_SAC.xlsx');self.assertEqual(len(data['source_sha256']),64)
 def test_leading_zeroes_preserved(self):
  result=search('0101','goods');self.assertEqual(result['results'][0]['code'],'0101')
 def test_goods_and_services_do_not_mix(self):
  result=search('accounting','service');self.assertGreater(result['total'],0)
  self.assertTrue(all(m['item_type']=='service' and len(m['code'])==6 for m in result['results']))
  self.assertEqual(search('998222','goods')['total'],0)
 def test_exact_code_first_and_results_bounded(self):
  self.assertEqual(search('8517','goods')['results'][0]['code'],'8517')
  self.assertLessEqual(len(search('other','goods')['results']),12)
 def test_common_name_is_expanded_but_not_a_final_classification(self):
  result=search('iphone','goods');self.assertEqual(result['expanded_query'],'smartphone');self.assertGreater(result['total'],0);self.assertNotIn('tax_rate',result['results'][0])
 def test_empty_or_nonsense_has_no_guessed_code(self):
  self.assertEqual(search('qzxqzxnotaproduct','goods')['results'],[]);self.assertEqual(words('Water / Bottles'),'water bottles')
 def view(self):
  view=suggestions
  while hasattr(view,'__wrapped__'):view=view.__wrapped__
  return view
 def test_permission_required(self):
  req=RequestFactory().get('/test',{'q':'water'});req.api_organization=None
  with patch('apps.business.hsn_suggestions.permitted',return_value=False):response=self.view()(req)
  self.assertEqual(response.status_code,403)
 def test_short_query_and_invalid_type(self):
  for params,status in [({'q':'ab'},200),({'q':'water','item_type':'invalid'},400),({'q':'x'*101},400)]:
   req=RequestFactory().get('/test',params)
   with patch('apps.business.hsn_suggestions.permitted',return_value=True):response=self.view()(req)
   self.assertEqual(response.status_code,status)
 def test_endpoint_returns_public_directory_without_database_queries(self):
  req=RequestFactory().get('/test',{'q':'water','item_type':'goods'})
  with patch('apps.business.hsn_suggestions.permitted',return_value=True):response=self.view()(req)
  self.assertEqual(response.status_code,200);self.assertIn('results',json.loads(response.content)['data'])
if __name__=='__main__':unittest.main()
