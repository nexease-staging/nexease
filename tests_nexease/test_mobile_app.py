import bootstrap
import unittest
from decimal import Decimal
from unittest.mock import patch

from apps.business import mobile_app
from apps.business.models import BusinessRecord
from apps.inventory.models import Inventory, Warehouse
from apps.products.models import Product
from test_payments_hub import HubFixture


class PhoneAppTests(HubFixture):
    def test_sales_list_search_status_and_paging(self):
        status, body = self.call(mobile_app.transactions, type="sale")
        self.assertEqual(status, 200)
        numbers = [r["number"] for r in body["data"]["rows"]]
        self.assertIn("INV-1", numbers)
        self.assertNotIn("X-1", numbers, "other business")
        row = next(r for r in body["data"]["rows"] if r["number"] == "INV-1")
        self.assertEqual((row["party"], row["amount"], row["balance"]), ("Sharma Traders", "1000.00", "1000.00"))
        status, body = self.call(mobile_app.transactions, type="sale", search="patil")
        self.assertEqual([r["number"] for r in body["data"]["rows"]], ["INV-3"])
        status, body = self.call(mobile_app.transactions, type="sale", status="paid")
        self.assertEqual(body["data"]["rows"], [])
        with patch.object(mobile_app, "PAGE", 2):
            status, body = self.call(mobile_app.transactions, type="sale")
            self.assertTrue(body["data"]["more"])
            first = {r["id"] for r in body["data"]["rows"]}
            status, body = self.call(mobile_app.transactions, type="sale", page="1")
            self.assertTrue(body["data"]["rows"])
            self.assertFalse(first & {r["id"] for r in body["data"]["rows"]}, "pages do not overlap")

    def test_purchases_expenses_and_permissions(self):
        status, body = self.call(mobile_app.transactions, type="purchase")
        self.assertEqual({r["number"] for r in body["data"]["rows"]}, {"B-1", "B-2"})
        BusinessRecord(organization=self.org, kind="expenses", key="e1", data={"payee": "HP pump", "amount": "500", "date": "2026-11-26", "category": "Fuel"}, created_by=self.user).save()
        status, body = self.call(mobile_app.transactions, type="expense", search="pump")
        self.assertEqual(body["data"]["rows"][0]["party"], "HP pump")
        with patch("apps.business.mobile_app.permitted", return_value=False):
            status, _ = self.call(mobile_app.transactions, type="sale")
        self.assertEqual(status, 403)
        status, _ = self.call(mobile_app.transactions, type="nope")
        self.assertEqual(status, 400)

    def test_dashboard(self):
        status, body = self.call(mobile_app.dashboard)
        d = body["data"]
        self.assertEqual(d["receivable"], "1800.00")
        self.assertEqual(d["payable"], "1000.00")
        self.assertEqual(len(d["trend"]), 6)
        self.assertEqual(d["top_dues"][0]["name"], "Sharma Traders")
        self.assertEqual(d["banks"][0]["name"], "Main cash")

    def test_items_with_stock(self):
        wh = Warehouse(organization=self.org, name="Main", code="W1").save() if "code" in Warehouse._fields else Warehouse(organization=self.org, name="Main").save()
        Inventory(organization=self.org, product=self.product, warehouse=wh, quantity=Decimal("12")).save()
        Product(organization=self.org, sku="S1", name="Delivery", category=self.product.category, unit="TRIP", item_type="service", hsn_code="996511").save()
        status, body = self.call(mobile_app.items)
        rows = {r["name"]: r for r in body["data"]["rows"]}
        self.assertEqual(rows["Cement"]["stock"], "12")
        self.assertIsNone(rows["Delivery"]["stock"])
        status, body = self.call(mobile_app.items, type="service")
        self.assertEqual([r["name"] for r in body["data"]["rows"]], ["Delivery"])

    def test_document_sheet(self):
        status, body = self.call(mobile_app.document, type="sale", id=str(self.old.id))
        d = body["data"]
        self.assertEqual((d["number"], d["party"]["name"], d["party"]["phone"], d["balance"]), ("INV-1", "Sharma Traders", "9876543210", "1000.00"))
        self.assertTrue(d["can_pay"])
        status, _ = self.call(mobile_app.document, type="sale", id="000000000000000000000000")
        self.assertEqual(status, 404)
        status, body = self.call(mobile_app.document, type="purchase", id=str(self.bill1.id))
        self.assertEqual(body["data"]["party"]["name"], "Om Cement Depot")


if __name__ == "__main__":
    unittest.main()
