import bootstrap
import json
import unittest
from datetime import datetime
from uuid import uuid4

from django.test import RequestFactory
from mongoengine.connection import get_db

from apps.accounts.models import User
from apps.business import setup_status as module
from apps.business.models import BusinessRecord as Record
from apps.finance.models import BankAccount
from apps.inventory.models import Inventory, Warehouse
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.sales.models import Customer, Invoice, InvoiceItem


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


class SetupStatusTests(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Fresh Traders", email="f@example.com").save()
        self.user = User(organization=self.org, email="owner@fresh.in", password="x", first_name="A", last_name="B").save()

    def status(self):
        request = RequestFactory().get("/")
        request.api_user, request.api_organization = self.user, self.org
        response = unwrap(module.setup_status)(request)
        body = json.loads(response.content)["data"]
        return body, {i["key"]: i["done"] for i in body["items"]}

    def test_new_business_has_almost_everything_to_do(self):
        body, done = self.status()
        self.assertEqual(body["total"], 11)
        # With no goods yet, there is no opening stock to enter.
        self.assertEqual([k for k, v in done.items() if v], ["opening_stock"])
        self.assertEqual(body["percent"], 9)
        self.assertTrue(all(i["href"].startswith("/") for i in body["items"]))

    def test_items_turn_done_as_the_business_is_set_up(self):
        self.org.phone, self.org.address = "9876543210", "MG Road, Pune"
        self.org.save()
        Record(organization=self.org, kind="gst_settings", key="default", created_by=self.user, data={"gstin": "27AAPFS1234K1Z5", "registration": "regular"}).save()
        Record(organization=self.org, kind="invoice_settings", key="default", created_by=self.user, data={"logo": "data:image/png;base64,AA", "bank_details": "HDFC 0001 IFSC HDFC0000001"}).save()
        get_db().user_mailboxes.insert_one({"organization_id": str(self.org.id), "user_id": str(self.user.id), "email": "owner@fresh.in", "provider": "gmail"})
        BankAccount(organization=self.org, account_name="Cash", account_type="CASH", created_by=self.user).save()
        cat = Category(organization=self.org, name="Building").save()
        cement = Product(organization=self.org, sku="CEM", name="Cement", category=cat, unit="BAG").save()
        _, done = self.status()
        self.assertFalse(done["opening_stock"])  # goods exist but no stock entered
        Inventory(organization=self.org, product=cement, warehouse=Warehouse(organization=self.org, name="Main", code="M").save(), quantity=10).save()
        customer = Customer(organization=self.org, name="Sharma", code="C1").save()
        Invoice(organization=self.org, customer=customer, invoice_number="I-1", status="ISSUED", invoice_date=datetime.utcnow(), billing_name="Sharma",
                created_by=self.user, items=[InvoiceItem(product=cement, quantity=1, unit_price=1, line_total=1)], total_amount=1, balance_due=1).save()
        User(organization=self.org, email=uuid4().hex + "@fresh.in", password="x", first_name="C", last_name="D").save()
        body, done = self.status()
        missing = [k for k, v in done.items() if not v]
        self.assertEqual(missing, [], missing)
        self.assertEqual(body["percent"], 100)

    def test_unregistered_business_counts_gst_as_done(self):
        Record(organization=self.org, kind="gst_settings", key="default", created_by=self.user, data={"gstin": "", "registration": "unregistered"}).save()
        _, done = self.status()
        self.assertTrue(done["gst"])

    def test_another_organisations_data_does_not_count(self):
        other = Organization(name="Other", email="o@example.com").save()
        BankAccount(organization=other, account_name="Bank", account_type="BANK", created_by=self.user).save()
        Customer(organization=other, name="X", code="X").save()
        _, done = self.status()
        self.assertFalse(done["bank_account"])
        self.assertFalse(done["customers"])


if __name__ == "__main__":
    unittest.main()
