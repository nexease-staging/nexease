import bootstrap
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from apps.business import mobile_home
from apps.business.models import BusinessRecord
from apps.purchasing.models import Supplier
from apps.sales.models import Customer, Invoice, InvoiceItem
from test_payments_hub import HubFixture


class MobileHomeTests(HubFixture):
    def test_home_balances_and_feed(self):
        Invoice(organization=self.org, customer=self.patil, invoice_number="INV-T", status="ISSUED", invoice_date=datetime.utcnow(),
                billing_name="Patil", created_by=self.user, items=[InvoiceItem(product=self.product, quantity=1, unit_price=250, line_total=250)],
                total_amount=250, balance_due=250).save()
        BusinessRecord(organization=self.org, kind="expenses", key="e1", data={"payee": "HP pump", "amount": "500", "date": "2026-11-26", "category": "Petrol / fuel", "reference": "R1"}, created_by=self.user).save()
        status, body = self.call(mobile_home.home)
        self.assertEqual(status, 200)
        d = body["data"]
        self.assertEqual(d["receivable"], "2050.00")  # 1800 open + today's 250; drafts and other orgs excluded
        self.assertEqual(d["payable"], "1000.00")
        self.assertEqual(d["sales_today"], "250.00")
        types = {r["type"] for r in d["transactions"]}
        self.assertTrue({"sale", "purchase", "expense"} <= types)
        self.assertNotIn("X-1", [r["number"] for r in d["transactions"]])
        sale = next(r for r in d["transactions"] if r["number"] == "INV-T")
        self.assertEqual((sale["party"], sale["href"]), ("Patil Hardware", "/invoices?view=" + str(Invoice.objects.get(invoice_number="INV-T").id)))

    def test_home_hides_sections_without_permission(self):
        with patch("apps.business.mobile_home.permitted", side_effect=lambda r, code: code.startswith("bills")):
            status, body = self.call(mobile_home.home)
        self.assertEqual(status, 200)
        self.assertIsNone(body["data"]["receivable"])
        self.assertEqual(body["data"]["payable"], "1000.00")
        self.assertFalse(any(r["type"] == "sale" for r in body["data"]["transactions"]))

    def test_parties_with_balances_sorted_and_searchable(self):
        Customer(organization=self.org, name="Zero Balance Co", code="C3").save()
        status, body = self.call(mobile_home.parties, side="customers")
        self.assertEqual(status, 200)
        d = body["data"]
        self.assertEqual([p["name"] for p in d["parties"]], ["Sharma Traders", "Patil Hardware", "Zero Balance Co"])
        self.assertEqual((d["parties"][0]["balance"], d["parties"][0]["overdue"]), ("1500.00", "1000.00"))
        self.assertEqual((d["total_balance"], d["with_balance"]), ("1800.00", 2))
        status, body = self.call(mobile_home.parties, side="customers", search="9876")
        self.assertEqual([p["name"] for p in body["data"]["parties"]], ["Sharma Traders"])
        status, body = self.call(mobile_home.parties, side="suppliers")
        self.assertEqual(body["data"]["parties"][0]["balance"], "1000.00")

    def test_parties_requires_read_permission_and_hides_balance_without_documents_access(self):
        with patch("apps.business.mobile_home.permitted", return_value=False):
            status, _ = self.call(mobile_home.parties, side="customers")
        self.assertEqual(status, 403)
        with patch("apps.business.mobile_home.permitted", side_effect=lambda r, code: code == "customers.read"):
            status, body = self.call(mobile_home.parties, side="customers")
        self.assertEqual(status, 200)
        self.assertIsNone(body["data"]["parties"][0]["balance"])
        self.assertIsNone(body["data"]["total_balance"])


if __name__ == "__main__":
    unittest.main()
