import bootstrap
import json
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch
from bson import ObjectId
from django.test import RequestFactory
from mongoengine.connection import get_db
from apps.business.mobile_insights import insights


class MobileDashboard(unittest.TestCase):
    def setUp(self):
        self.org = ObjectId()
        self.other = ObjectId()
        self.db = get_db()

    def read(self, section, allowed, end="2026-11-30"):
        request = RequestFactory().get("/", {"from": "2026-11-01", "to": end})
        request.api_organization = SimpleNamespace(id=self.org)
        with patch("apps.business.mobile_insights.permitted", side_effect=lambda _, p: p in allowed):
            response = insights.__wrapped__(request, section)
        return response.status_code, json.loads(response.content).get("data", {})

    def test_collections_across_pages_and_tenants(self):
        for org, count in [(self.org, 105), (self.other, 2)]:
            self.db.customer_payments.insert_many([dict(organization=org, amount=10,
                payment_date=datetime(2026, 11, 4)) for _ in range(count)])
        self.assertEqual(self.read("collections", ["customer_payments.read"]), (200, {"collections": "1050"}))
        self.assertEqual(self.read("collections", [])[0], 403)
        self.assertEqual(self.read("collections", [], "2026-10-01")[0], 400)

    def test_bank_book_permission_is_separate(self):
        for org in (self.org, self.other):
            self.db.bank_transactions.insert_one(dict(organization=org, reconciliation_status="UNRECONCILED"))
        self.assertEqual(self.read("banking", ["bank_transactions.read"]), (200, {"book_unmatched": 1}))

    def test_production_does_not_mix_units(self):
        outputs = [dict(unit=unit, materials=[], expenses="7", estimate="6", accepted=qty, rejected="0") for unit, qty in [("KG","3"),("PCS","2")]]
        self.db.manufacturing_orders.insert_one(dict(organization=self.org, due="2026-11-10", status="completed", outputs=outputs))
        _, data = self.read("production", ["manufacturing.read"])
        self.assertEqual(data["units"], {"KG": ["3","0"], "PCS":["2","0"]})
        self.assertEqual(data["variance"], "2")
        self.assertNotIn("shortages", data)
