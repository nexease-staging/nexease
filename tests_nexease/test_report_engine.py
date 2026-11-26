import bootstrap
import json
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.test import RequestFactory
from mongoengine.connection import get_db

from apps.accounts.models import User
from apps.business import report_engine as engine
from apps.business.models import BusinessRecord as Record
from apps.inventory.models import Inventory, Warehouse
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.purchasing.models import Supplier, VendorBill, VendorBillItem
from apps.sales.models import Customer, Invoice, InvoiceItem


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


def item(product, qty, rate, tax_rate=18, discount=0, **extra):
    net = Decimal(qty) * Decimal(rate) - Decimal(discount)
    tax = (net * Decimal(tax_rate) / 100).quantize(Decimal("0.01"))
    return dict(product=product, quantity=qty, unit_price=rate, tax_rate=tax_rate, discount=discount,
                line_subtotal=net, line_tax=tax, line_total=net + tax, **extra)


class ReportFixture(unittest.TestCase):
    allowed = None

    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Report org", email="r@example.com").save()
        self.other = Organization(name="Other", email="o@example.com").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="A", last_name="B").save()
        allowed = self.allowed
        patcher = patch("apps.authorization.services.AuthorizationService.has_permission",
                        side_effect=lambda user, code: allowed is None or code in allowed)
        patcher.start(); self.addCleanup(patcher.stop)
        building = Category(organization=self.org, name="Building").save()
        paint = Category(organization=self.org, name="Paint").save()
        self.cement = Product(organization=self.org, sku="CEM", name="OPC cement", category=building, unit="BAG", cost_price=Decimal("350"), hsn_code="2523").save()
        self.enamel = Product(organization=self.org, sku="PNT", name="Enamel paint", category=paint, unit="TIN", cost_price=None, hsn_code="3208").save()
        self.labour = Product(organization=self.org, sku="SRV", name="Fixing labour", category=building, unit="HR", item_type="service", hsn_code="995411").save()
        self.sharma = Customer(organization=self.org, name="Sharma Traders", code="C1", gstin="27AAPFS1234K1Z5").save()
        self.patil = Customer(organization=self.org, name="Patil Hardware", code="C2").save()
        self.inv("INV-1", self.sharma, datetime(2026, 11, 3), [item(self.cement, 100, 420, discount=1000), item(self.labour, 10, 300, item_type="service", hsn_code="995411")])
        self.inv("INV-2", self.patil, datetime(2026, 11, 20), [item(self.enamel, 4, 560, tax_rate=28)], status="PAID")
        self.inv("INV-3", self.sharma, datetime(2026, 10, 15), [item(self.cement, 10, 400)])  # previous period
        self.inv("INV-D", self.sharma, datetime(2026, 11, 21), [item(self.cement, 999, 1)], status="DRAFT")
        omc = Supplier(organization=self.org, name="Om Cement Depot", code="S1").save()
        VendorBill(organization=self.org, supplier=omc, bill_number="B-1", status="POSTED", bill_date=datetime(2026, 11, 5), created_by=self.user,
                   items=[VendorBillItem(**item(self.cement, 50, 350))], total_amount=0, balance_due=0).save()
        for day, cat, amount in (("2026-11-08", "Rent", "15000"), ("2026-11-09", "Travel", "1200"), ("2026-12-01", "Rent", "15000")):
            Record(organization=self.org, created_by=self.user, kind="expenses", key=uuid4().hex[:8],
                   data={"date": day, "category": cat, "description": cat + " paid", "payee": "X", "amount": amount, "payment_mode": "UPI", "reference": "R"}).save()
        # Another organisation's invoice in the same period never appears.
        ocat = Category(organization=self.other, name="X").save()
        oprod = Product(organization=self.other, sku="CEM", name="Other cement", category=ocat, unit="BAG").save()
        ocust = Customer(organization=self.other, name="Sharma Traders", code="C1").save()
        Invoice(organization=self.other, customer=ocust, invoice_number="X-1", status="ISSUED", invoice_date=datetime(2026, 11, 4), billing_name="x",
                created_by=self.user, items=[InvoiceItem(**item(oprod, 1, 99999))], total_amount=1, balance_due=1).save()

    def inv(self, number, customer, when, lines, status="ISSUED"):
        return Invoice(organization=self.org, customer=customer, invoice_number=number, status=status, invoice_date=when, billing_name=customer.name,
                       created_by=self.user, items=[InvoiceItem(**l) for l in lines], total_amount=0, balance_due=0).save()

    def call(self, report, start="2026-11-01", end="2026-11-30", **extra):
        request = RequestFactory().get("/", {"report": report, "from": start, "to": end, **extra})
        request.api_user, request.api_organization = self.user, self.org
        response = unwrap(engine.run_report)(request)
        return response.status_code, json.loads(response.content)

    def ok(self, report, **kw):
        status, body = self.call(report, **kw)
        self.assertEqual(status, 200, body)
        return body["data"]


class DocumentReportTests(ReportFixture):
    def test_transactions_have_typed_columns_and_totals(self):
        data = self.ok("sales/document")
        self.assertEqual([r["number"] for r in data["rows"]], ["INV-1", "INV-2"])  # draft, other month and other org excluded
        first = data["rows"][0]
        self.assertEqual((first["party"], first["gstin"], first["date"]), ("Sharma Traders", "27AAPFS1234K1Z5", "2026-11-03"))
        self.assertEqual((first["net"], first["discount"], first["tax"]), ("44000.00", "1000.00", "7920.00"))
        self.assertEqual(data["totals"]["net"], "46240.00")
        self.assertEqual({c["key"]: c["type"] for c in data["columns"]}["total"], "money")
        self.assertIsNone(data["previous"])

    def test_item_report_quantity_average_rate_and_share(self):
        data = self.ok("sales/item")
        cement = next(r for r in data["rows"] if r["item"] == "OPC cement")
        self.assertEqual((cement["qty"], cement["unit"], cement["rate_avg"], cement["net"]), ("100.00", "BAG", "410.00", "41000.00"))
        self.assertEqual(data["totals"]["share"], "100.00")
        self.assertNotIn("rate_avg", data["totals"])
        self.assertEqual(data["chart"], {"type": "bar", "y": ["total"], "limit": 8, "x": "item"})

    def test_hsn_sac_and_rate(self):
        hsn = self.ok("sales/hsn")
        self.assertEqual([r["code"] for r in hsn["rows"]], ["2523", "3208"])
        sac = self.ok("sales/sac")
        self.assertEqual([(r["code"], r["net"]) for r in sac["rows"]], [("995411", "3000.00")])
        rate = self.ok("sales/rate")
        self.assertEqual([r["rate"] for r in rate["rows"]], ["18%", "28%"])

    def test_purchases_use_product_hsn_and_party(self):
        data = self.ok("purchases/party")
        self.assertEqual([(r["party"], r["net"]) for r in data["rows"]], [("Om Cement Depot", "17500.00")])
        self.assertEqual(self.ok("purchases/hsn")["rows"][0]["code"], "2523")

    def test_trend_daily_and_monthly_with_compare(self):
        daily = self.ok("sales/trend", compare="1")
        self.assertEqual(len(daily["rows"]), 30)
        self.assertEqual(daily["rows"][2], {"period": "2026-11-03", "documents": 1, "net": "44000.00", "tax": "7920.00", "total": "51920.00"})
        self.assertEqual(daily["previous"]["period"], {"from": "2026-10-02", "to": "2026-10-31"})
        self.assertEqual(daily["previous"]["totals"]["net"], "4000.00")
        monthly = self.ok("sales/trend", start="2026-04-01", end="2027-03-31")
        self.assertEqual([r["period"] for r in monthly["rows"]][:2], ["2026-04", "2026-05"])
        self.assertEqual(len(monthly["rows"]), 12)

    def test_discount_reports(self):
        data = self.ok("sales/discount")
        self.assertEqual([(r["number"], r["discount"], r["rate"]) for r in data["rows"]], [("INV-1", "1000.00", "2.22")])
        self.assertEqual(data["totals"]["rate"], "2.22")

    def test_bad_requests(self):
        self.assertEqual(self.call("sales/nonsense")[0], 400)
        self.assertEqual(self.call("sales/item", start="2026-11-30", end="2026-11-01")[0], 400)
        self.assertEqual(self.call("sales/item", start="2025-01-01", end="2026-11-01")[0], 400)
        self.assertEqual(self.call("sales/item", start="bad")[0], 400)


class OtherReportTests(ReportFixture):
    def test_profit_by_item_and_customer(self):
        data = self.ok("profit/item")
        cement = next(r for r in data["rows"] if r["item"] == "OPC cement")
        self.assertEqual((cement["sales"], cement["cost"], cement["profit"], cement["margin"]), ("41000.00", "35000.00", "6000.00", "14.63"))
        self.assertIn("Enamel paint", " ".join(data["notes"]))  # no cost price
        party = self.ok("profit/party")
        self.assertEqual(party["rows"][0]["party"], "Sharma Traders")
        self.assertEqual(party["totals"]["margin"], str((Decimal(party["totals"]["profit"]) / Decimal(party["totals"]["sales"]) * 100).quantize(Decimal("0.01"))))

    def test_monthly_overview(self):
        data = self.ok("overview/monthly", start="2026-10-01", end="2026-12-31")
        nov = next(r for r in data["rows"] if r["period"] == "2026-11")
        self.assertEqual((nov["sales"], nov["purchases"], nov["expenses"]), ("46240.00", "17500.00", "16200.00"))
        self.assertEqual(nov["result"], "12540.00")
        self.assertEqual(data["chart"]["y"], ["sales", "purchases", "expenses"])

    def test_expenses(self):
        cats = self.ok("expenses/category")
        self.assertEqual([(r["label"], r["amount"]) for r in cats["rows"]], [("Rent", "15000.00"), ("Travel", "1200.00")])
        docs = self.ok("expenses/document")
        self.assertEqual(docs["totals"]["amount"], "16200.00")

    def test_inventory_reports_ignore_dates(self):
        warehouse = Warehouse(organization=self.org, name="Main", code="M").save()
        Inventory(organization=self.org, product=self.cement, warehouse=warehouse, quantity=5).save()
        Record(organization=self.org, created_by=self.user, kind="reorder_rule", key=str(self.cement.id), data={"level": "20", "enabled": True}).save()
        low = self.ok("inventory/low")
        self.assertEqual([(r["item"], r["short"]) for r in low["rows"]], [("OPC cement", "15.00")])
        self.assertFalse(low["dated"])
        cat = self.ok("inventory/category", compare="1")
        self.assertIsNone(cat["previous"])
        self.assertEqual(next(r for r in cat["rows"] if r["category"] == "Building")["value"], "1750.00")


class PermissionTests(ReportFixture):
    allowed = {"invoices.read", "inventory.read"}

    def test_reports_respect_permissions(self):
        self.assertEqual(self.call("sales/item")[0], 200)
        self.assertEqual(self.call("purchases/item")[0], 403)
        self.assertEqual(self.call("sales/hsn")[0], 403)
        self.assertEqual(self.call("profit/item")[0], 403)
        self.assertEqual(self.call("expenses/category")[0], 403)
        overview = self.ok("overview/monthly")
        self.assertEqual(overview["rows"][0]["purchases"], "0.00")
        self.assertIn("Purchases hidden", " ".join(overview["notes"]))
        category = self.ok("inventory/category")
        self.assertNotIn("value", [c["key"] for c in category["columns"]])


if __name__ == "__main__":
    unittest.main()
