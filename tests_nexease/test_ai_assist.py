import bootstrap
import unittest
from unittest.mock import patch

from apps.saas import ai
from apps.saas.ai_assist import assist, quick_intent, form_for, _money


def entry(kind, items=None, **fields):
    f = dict.fromkeys(ai.FIELDS, '')
    f.update(fields)
    return {'kind': kind, 'fields': f, 'items': items or [], 'questions': [], 'warnings': []}


def line(**kw):
    base = dict.fromkeys(ai.ITEM_FIELDS, '')
    base.update(kw)
    return base


class QuickIntentTests(unittest.TestCase):
    def test_received_payment_english_and_hinglish(self):
        d = quick_intent('Received ₹5,000 from Sharma Traders by UPI', ai.FIELDS, '2026-11-26')
        self.assertEqual(d['kind'], 'payment_in')
        self.assertEqual((d['fields']['party_name'], d['fields']['amount'], d['fields']['payment_mode'], d['fields']['date']), ('Sharma Traders', '5000', 'UPI', '2026-11-26'))
        d = quick_intent('Ramesh se 2500 mila cash', ai.FIELDS, '2026-11-26')
        self.assertEqual((d['kind'], d['fields']['party_name'], d['fields']['amount'], d['fields']['payment_mode']), ('payment_in', 'Ramesh', '2500', 'Cash'))

    def test_missing_mode_is_left_blank_not_guessed(self):
        d = quick_intent('got 1200 from Gupta Stores', ai.FIELDS)
        self.assertEqual(d['fields']['payment_mode'], '')

    def test_add_customer_with_phone_gstin_and_city(self):
        d = quick_intent('Add customer Mehta Hardware 9876543210 27ABCDE1234F1Z5 from Pune', ai.FIELDS)
        self.assertEqual(d['kind'], 'customer')
        f = d['fields']
        self.assertEqual((f['name'], f['phone'], f['party_gstin'], f['party_address']), ('Mehta Hardware', '9876543210', '27ABCDE1234F1Z5', 'Pune'))
        self.assertEqual(quick_intent('new vendor Om Steel', ai.FIELDS)['kind'], 'supplier')

    def test_everything_else_goes_to_the_model(self):
        for text in ('Invoice Sharma 10 bags cement at 380', 'paid 500 petrol upi', '', 'x' * 300, 'received\nmoney'):
            self.assertIsNone(quick_intent(text, ai.FIELDS), text)

    def test_quick_result_has_exactly_the_schema_fields(self):
        d = quick_intent('add supplier Om Steel', ai.FIELDS)
        self.assertEqual(set(d['fields']), set(ai.FIELDS))


class AssistTests(unittest.TestCase):
    def test_invoice_asks_for_missing_rate_and_suggests_gst(self):
        a = assist('invoice', entry('invoice', [line(name='Cement', quantity='10')], party_name='Sharma Traders'))
        self.assertEqual(a['form']['type'], 'invoice')
        self.assertFalse(a['ready'])
        fields = [m['field'] for m in a['missing']]
        self.assertEqual(fields, ['items.0.unit_price', 'items.0.tax_rate'])
        self.assertIn('rate for Cement', a['reply'])
        gst = a['missing'][1]
        self.assertFalse(gst['required'])
        self.assertIn('18', gst['choices'])

    def test_complete_invoice_is_ready_with_total(self):
        a = assist('invoice', entry('invoice', [line(name='Cement', quantity='10', unit_price='380', tax_rate='18')], party_name='Sharma Traders'))
        self.assertTrue(a['ready'])
        self.assertEqual(a['missing'], [])
        self.assertIn({'label': 'Total', 'value': '₹4,484'}, a['summary'])

    def test_invoice_without_party_or_items(self):
        a = assist('invoice', entry('invoice'))
        self.assertEqual([m['field'] for m in a['missing']], ['party_name', 'items.0.name'])

    def test_expense_uses_record_form_and_schema_choices(self):
        a = assist('expense', entry('expense', amount='500', description='Petrol'))
        self.assertEqual(a['form'], {'type': 'record', 'record_kind': 'expenses', 'route': '/expenses'})
        missing = {m['field']: m for m in a['missing']}
        self.assertIn('payment_mode', missing)
        self.assertIn('UPI', missing['payment_mode']['choices'])
        self.assertIn('party_name', missing)  # payee comes from party_name
        self.assertNotIn('date', missing)
        self.assertNotIn('reference', missing)

    def test_payment_in_is_form_only(self):
        a = assist('payment_in', entry('payment_in', party_name='Ramesh', amount='2500', payment_mode='Cash'), refs={'party_id': 'abc'})
        self.assertTrue(a['ready'])
        self.assertFalse(a['quick_save'])
        self.assertEqual(a['form']['type'], 'payment')
        self.assertEqual(a['refs'], {'party_id': 'abc'})

    def test_customer_optional_questions_do_not_block(self):
        a = assist('customer', entry('customer', name='Mehta'))
        self.assertTrue(a['ready'])
        self.assertTrue(all(not m['required'] for m in a['missing']))

    def test_question_kind_replies_with_model_question(self):
        d = entry('question')
        d['questions'] = ['Should this be a sales invoice or a purchase bill?']
        a = assist('question', d)
        self.assertIsNone(a['form'])
        self.assertEqual(a['reply'], 'Should this be a sales invoice or a purchase bill?')

    def test_every_supported_kind_has_a_form(self):
        for kind in ai.PERMISSIONS:
            self.assertIsNotNone(form_for(kind), kind)

    def test_indian_money_format(self):
        self.assertEqual(_money('1234567.5'), '₹12,34,567.50')
        self.assertEqual(_money('500'), '₹500')
        self.assertEqual(_money(''), '')


class ConfirmGuardTests(unittest.TestCase):
    def test_form_only_kinds_are_in_schema_enum(self):
        enum = ai.SCHEMA['properties']['kind']['enum']
        for kind in ('customer', 'supplier', 'payment_in', 'payment_out'):
            self.assertIn(kind, enum)

    def test_parse_response_accepts_new_kinds(self):
        import json
        raw = {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(entry('payment_out', party_name='Om Steel', amount='9000'))}]}]}
        self.assertEqual(ai.parse_response(raw)['kind'], 'payment_out')


if __name__ == '__main__':
    unittest.main()
