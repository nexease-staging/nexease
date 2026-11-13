import bootstrap
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from apps.migration.services.migration_api_service import MigrationAPIService, MigrationAPIValidationError
from apps.migration.services.migration_preview_service import MigrationPreviewService, MigrationPreviewError

class MigrationFeedbackTests(unittest.TestCase):
    def test_supported_ui_types_are_accepted(self):
        for kind in ('EMPLOYEES', 'GOODS_RECEIPTS', 'VENDOR_BILLS', 'CUSTOMER_PAYMENTS', 'SUPPLIER_PAYMENTS'):
            with self.subTest(kind=kind):
                result = MigrationAPIService._validate_create_payload({'source_system':'GENERIC','migration_type':kind})
                self.assertEqual(result['migration_type'], kind)
        with self.assertRaises(MigrationAPIValidationError):
            MigrationAPIService._validate_create_payload({'source_system':'GENERIC','migration_type':'UNKNOWN'})

    def test_report_keeps_reasons_not_source_data_and_is_bounded(self):
        rows = [{'row_number':i+2,'valid':False,'data':{'salary':'private'},'errors':[{'field':'email','code':'INVALID','message':'Enter a valid email.'}]} for i in range(210)]
        rows.insert(0, {'row_number':1,'valid':True,'errors':[]})
        report = MigrationAPIService.serialize_batch(SimpleNamespace(validation_result={'rows':rows}))
        self.assertEqual(len(report['validation_issues']), 200)
        self.assertEqual(report['validation_issues'][0]['row_number'], 2)
        self.assertNotIn('private', str(report))
        self.assertIn('Enter a valid email.', str(report))

    def test_missing_mapping_names_field_before_validation_starts(self):
        batch=SimpleNamespace(organization='org',status='UPLOADED',upload_id='u',mapping={},migration_type='PRODUCTS')
        upload=SimpleNamespace(purpose='DATA_MIGRATION',status='AVAILABLE',content=b'x',filename='data.csv')
        base='apps.migration.services.migration_preview_service.'
        with patch(base+'BackgroundUploadRepository.get_by_id',return_value=upload), patch(base+'MigrationFileParser.read_rows',return_value={'columns':['name'],'rows':[{'name':'Item'}]}), patch(base+'MigrationBatchService.start_validation') as start:
            with self.assertRaises(MigrationPreviewError) as caught:
                MigrationPreviewService.validate_batch(batch=batch,organization='org')
            self.assertIn('sku:', str(caught.exception))
            self.assertIn('Required field', str(caught.exception))
            start.assert_not_called()
