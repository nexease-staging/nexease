import bootstrap
import json
import unittest
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.test import RequestFactory
from mongoengine.connection import get_db

from apps.accounts.models import User
from apps.business import inventory_insights
from apps.business.models import BusinessRecord as Record
from apps.inventory.api.v1 import views as inventory_views
from apps.inventory.models import Inventory, StockMovement, Warehouse
from apps.organizations.models import Organization
from apps.products.api.v1 import urls as product_urls
from apps.products.models import Category, Product
from apps.purchasing.models import PurchaseOrder, PurchaseOrderItem, Supplier


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


class InventoryFixture(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Stock org", email="s@example.com").save()
        self.other = Organization(name="Other org", email="o@example.com").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="A", last_name="B").save()
        patcher = patch("apps.authorization.services.AuthorizationService.has_permission", return_value=True)
        patcher.start(); self.addCleanup(patcher.stop)
        cat = Category(organization=self.org, name="Building").save()
        self.main = Warehouse(organization=self.org, name="Main godown", code="MAIN").save()
        self.site = Warehouse(organization=self.org, name="Site store", code="SITE").save()
        mk = lambda sku, name, cost: Product(organization=self.org, category=cat, sku=sku, name=name, unit="BAG", cost_price=cost).save()
        self.cement = mk("CEM", "OPC cement", Decimal("380"))
        self.sand = mk("SND", "River sand", Decimal("50"))
        self.paint = mk("PNT", "Old enamel paint", Decimal("200"))
        self.nocost = mk("NOC", "Free sample", None)
        self.stock(self.cement, self.main, 8, reserved=2)
        self.stock(self.cement, self.site, 4)
        self.stock(self.sand, self.main, 0)
        self.stock(self.paint, self.main, 10)
        self.stock(self.nocost, self.main, 3)
        for product, level in [(self.cement, "20"), (self.sand, "5"), (self.paint, "2")]:
            Record(organization=self.org, created_by=self.user, kind="reorder_rule", key=str(product.id), data={"level": level, "enabled": True}).save()
        self.move(self.cement, self.main, days_ago=2)
        self.move(self.paint, self.main, days_ago=200)
        supplier = Supplier(organization=self.org, code="OMC", name="Om Cement Depot").save()
        PurchaseOrder(organization=self.org, po_number="PO-1", supplier=supplier, status="RECEIVED", order_date=date(2026, 11, 1), created_by=self.user,
                      items=[PurchaseOrderItem(product=self.cement, quantity=10, unit_price=Decimal("375"))]).save()
        # Another organisation's data must never appear.
        ocat = Category(organization=self.other, name="X").save()
        oprod = Product(organization=self.other, category=ocat, sku="CEM", name="Other cement", unit="BAG", cost_price=Decimal("999")).save()
        owh = Warehouse(organization=self.other, name="Other", code="OTH").save()
        Inventory(organization=self.other, product=oprod, warehouse=owh, quantity=Decimal("1000")).save()

    def stock(self, product, warehouse, quantity, reserved=0):
        return Inventory(organization=self.org, product=product, warehouse=warehouse, quantity=Decimal(quantity), reserved_quantity=Decimal(reserved)).save()

    def move(self, product, warehouse, days_ago):
        inv = Inventory.objects(organization=self.org, product=product, warehouse=warehouse).first()
        m = StockMovement(organization=self.org, inventory=inv, product=product, warehouse=warehouse, movement_type="STOCK_IN", quantity=Decimal(1),
                          quantity_before=Decimal(0), quantity_after=Decimal(1), created_by=self.user).save()
        StockMovement.objects(id=m.id).update_one(set__created_at=datetime.utcnow() - timedelta(days=days_ago))

    def get(self, **params):
        request = RequestFactory().get("/", params)
        request.api_user = self.user; request.api_organization = self.org; request.user = self.user
        response = unwrap(inventory_insights.insights)(request)
        return response.status_code, json.loads(response.content)



class InventoryInsightsTests(InventoryFixture):
    def test_summary_values_counts_and_isolation(self):
        status, body = self.get()
        self.assertEqual(status, 200, body)
        s = body["data"]["summary"]
        # 12 cement x 380 + 10 paint x 200; sand is 0, free sample has no cost.
        self.assertEqual(s["stock_value"], "6560.00")
        self.assertEqual(s["products"], 4)
        self.assertEqual(s["out_of_stock"], 1)
        self.assertEqual(s["unvalued_products"], 1)
        self.assertEqual([w["code"] for w in body["data"]["by_warehouse"]], ["MAIN", "SITE"])
        self.assertEqual(body["data"]["by_warehouse"][0]["value"], "5040.00")

    def test_low_stock_suggestion_and_last_supplier(self):
        _, body = self.get()
        low = {row["sku"]: row for row in body["data"]["low_stock"]}
        self.assertEqual(set(low), {"CEM", "SND"})  # paint (10 available) is above its level of 2
        cement = low["CEM"]
        self.assertEqual(cement["available"], "10.00")  # 12 on hand - 2 reserved
        self.assertEqual(cement["suggested_quantity"], "30.00")  # back up to 2 x 20
        self.assertEqual(cement["supplier"]["name"], "Om Cement Depot")
        self.assertEqual(cement["supplier"]["last_rate"], "375.00")
        self.assertIsNone(low["SND"]["supplier"])
        self.assertEqual(body["data"]["summary"]["low_stock"], 2)

    def test_dead_stock_uses_last_movement(self):
        _, body = self.get()
        dead = [row["sku"] for row in body["data"]["dead_stock"]]
        self.assertIn("PNT", dead)   # last moved 200 days ago
        self.assertIn("NOC", dead)   # stock with no movement at all
        self.assertNotIn("CEM", dead)
        self.assertEqual(body["data"]["dead_stock"][0]["sku"], "PNT")  # highest value first
        _, shorter = self.get(dead_days=365)
        self.assertNotIn("PNT", [row["sku"] for row in shorter["data"]["dead_stock"]])

    def test_warehouse_filter(self):
        _, body = self.get(warehouse_id=str(self.site.id))
        self.assertEqual(body["data"]["summary"]["stock_value"], "1520.00")

    def test_rejects_bad_input_and_needs_permission(self):
        self.assertIn(self.get(dead_days=3)[0], (400, 422))
        status, _ = self.get(warehouse_id="not-an-id")
        self.assertIn(status, (400, 422))
        with patch("apps.authorization.services.AuthorizationService.has_permission", return_value=False):
            self.assertEqual(self.get()[0], 403)


class InventorySearchAndUnitsTests(InventoryFixture):
    def list(self, view, term):
        request = RequestFactory().get("/", {"search": term})
        request.api_user = self.user; request.api_organization = self.org; request.user = self.user
        response = unwrap(view)(request)
        self.assertEqual(response.status_code, 200, response.content)
        return json.loads(response.content)["data"]

    def test_stock_search_by_product_and_warehouse(self):
        rows = self.list(inventory_views.inventory_collection_api, "cement")["inventory"]
        self.assertEqual(len(rows), 2)
        rows = self.list(inventory_views.inventory_collection_api, "Site store")["inventory"]
        self.assertEqual(len(rows), 1)

    def test_movement_search_by_product(self):
        rows = self.list(inventory_views.stock_movement_collection_api, "enamel")["movements"]
        self.assertEqual(len(rows), 1)

    def test_android_units_route_precedes_product_detail(self):
        names = [p.name for p in product_urls.urlpatterns]
        self.assertLess(names.index("product_units_alias"), names.index("product_detail"))
        alias = next(p for p in product_urls.urlpatterns if p.name == "product_units_alias")
        self.assertIs(alias.callback, next(p for p in product_urls.urlpatterns if p.name == "product_units").callback)
