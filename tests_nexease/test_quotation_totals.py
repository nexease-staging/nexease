import bootstrap
import unittest
from apps.business.quotations import price_quote


class QuoteTotals(unittest.TestCase):
    def test_discount_tax_and_validity(self):
        data = {"customer":{"name":"Buyer"}, "invoice_date":"2026-11-01", "due_date":"2026-11-30",
                "items":[{"name":"Service","quantity":"2","unit_price":"100","discount":"10","tax_rate":"18"}]}
        self.assertEqual(price_quote(data)["total"], "224.20")
        data["due_date"]="2026-10-01"
        with self.assertRaisesRegex(ValueError,"Validity"):
            price_quote(data)
