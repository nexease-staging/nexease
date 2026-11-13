import bootstrap
import unittest
from unittest.mock import patch
from apps.migration.services.employee_import import validate_employee
from apps.migration.services.migration_schema_service import MigrationSchemaService

class EmployeeImportChoiceTests(unittest.TestCase):
    def row(self, value):
        return dict(code='E001', name='Test employee', employment_type=value, joining_date='2026-11-01', basis='Daily', rate='700')

    def test_location_formats_and_pay_basis_normalize(self):
        with patch('apps.migration.services.employee_import.Record.objects') as records:
            records.return_value.first.return_value=None
            for raw, expected in [('site','site'),(' Site ','site'),('In-house','inhouse'),('IN HOUSE','inhouse'),('in_house','inhouse')]:
                with self.subTest(value=raw):
                    result=validate_employee(None,self.row(raw),set())
                    self.assertTrue(result['valid'], result['errors'])
                    self.assertEqual(result['normalized']['employment_type'],expected)
                    self.assertEqual(result['normalized']['basis'],'daily')

    def test_unknown_type_is_not_silently_reclassified(self):
        result=validate_employee(None,self.row('Permanent'),set())
        self.assertFalse(result['valid'])
        self.assertEqual(result['errors'][0]['field'],'employment_type')
        self.assertIn('site, inhouse',result['errors'][0]['message'])

    def test_schema_explains_choices_and_recognizes_display_header(self):
        field=MigrationSchemaService.get_schema('EMPLOYEES')['fields']['employment_type']
        self.assertEqual(field['choices'],['site','inhouse'])
        self.assertIn('work location type',field['aliases'])
