import bootstrap
import json
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.test import RequestFactory
from mongoengine.connection import get_db

from apps.accounts.models import User
from apps.business import jobs as jobs_api
from apps.business import recipes as recipes_api
from apps.business.books import ensure_accounts
from apps.business.direct_entry import direct_invoice
from apps.business.quick_stock import reverse
from apps.inventory.models import Inventory, StockMovement, Warehouse
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.sales.models import Customer, Invoice
from apps.sales.services.sales_order_service import SalesOrderService


def msg(body):
    return body.get("message") or (body.get("error") or {}).get("message", "")


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


class ProductionFixture(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Sharma Furniture", email=uuid4().hex + "@example.com").save()
        self.other = Organization(name="Other", email=uuid4().hex + "@example.com").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="Ramesh", last_name="S").save()
        patcher = patch("apps.authorization.services.AuthorizationService.has_permission", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        ensure_accounts(self.org, self.user)
        cat = Category(organization=self.org, name="Furniture").save()

        def item(sku, name, unit, cost, price=0):
            return Product(organization=self.org, category=cat, sku=sku, name=name, unit=unit, cost_price=cost, selling_price=price).save()

        self.almirah = item("ALM", "Steel almirah", "PCS", 0, 25000)
        self.rack = item("RACK", "Slotted rack", "PCS", 0, 3000)
        self.ply = item("PLY", "Plywood 18mm", "SHEET", 1200)
        self.hinge = item("HNG", "Hinge", "PCS", 40)
        self.wh = Warehouse(organization=self.org, code="MAIN", name="Main godown").save()
        Inventory(organization=self.org, product=self.ply, warehouse=self.wh, quantity=Decimal("20")).save()
        Inventory(organization=self.org, product=self.hinge, warehouse=self.wh, quantity=Decimal("100")).save()
        self.customer = Customer(organization=self.org, name="Patil Builders", code="C1", phone="9876543210").save()

    def call(self, view, verb="get", data=None, org=None, **kwargs):
        factory = RequestFactory()
        if verb == "get":
            request = factory.get("/", kwargs.pop("params", {}))
        else:
            request = factory.generic(verb.upper(), "/", json.dumps(data or {}), content_type="application/json")
        request.api_user, request.api_organization = self.user, org or self.org
        response = unwrap(view)(request, **kwargs)
        return response.status_code, json.loads(response.content)

    def stock(self, product):
        row = Inventory.objects(organization=self.org, product=product, warehouse=self.wh).first()
        return row.quantity if row else Decimal(0)

    def make_recipe(self, product=None, mto=True):
        product = product or self.almirah
        return self.call(recipes_api.recipes, "post", {
            "made_to_order": mto, "labour_per_unit": "1500",
            "materials": [{"product": str(self.ply.id), "per_unit": "4"}, {"product": str(self.hinge.id), "per_unit": "8"}],
        }, product_id=str(product.id))


class RecipeTests(ProductionFixture):
    def test_save_and_read_recipe(self):
        status, body = self.make_recipe()
        self.assertEqual(status, 200, body)
        d = body["data"]
        self.assertTrue(d["made_to_order"])
        self.assertEqual([m["name"] for m in d["materials"]], ["Plywood 18mm", "Hinge"])
        self.assertEqual(d["material_cost"], "5120.00")  # 4 × 1200 + 8 × 40
        self.assertEqual(d["unit_cost"], "6620.00")
        self.assertEqual(d["can_make"], 5)  # 20 sheets / 4 per almirah
        status, body = self.call(recipes_api.recipes)
        self.assertEqual(body["data"]["count"], 1)
        status, body = self.call(recipes_api.recipes, product_id=str(self.rack.id))
        self.assertEqual((status, body["data"]["made_to_order"], body["data"]["materials"]), (200, False, []))

    def test_recipe_validation(self):
        status, body = self.call(recipes_api.recipes, "post", {"made_to_order": True, "materials": []}, product_id=str(self.almirah.id))
        self.assertEqual(status, 400)
        self.assertIn("raw materials", msg(body))
        status, body = self.call(recipes_api.recipes, "post", {"materials": [{"product": str(self.almirah.id), "per_unit": "1"}]}, product_id=str(self.almirah.id))
        self.assertIn("itself", msg(body))
        status, body = self.call(recipes_api.recipes, "post", {"materials": [{"product": str(self.ply.id), "per_unit": "1"}, {"product": str(self.ply.id), "per_unit": "2"}]}, product_id=str(self.almirah.id))
        self.assertIn("twice", msg(body))
        status, body = self.call(recipes_api.recipes, "post", {"materials": [{"product": str(self.ply.id), "per_unit": "0"}]}, product_id=str(self.almirah.id))
        self.assertEqual(status, 400)
        self.make_recipe()
        status, body = self.call(recipes_api.recipes, "post", {"materials": [{"product": str(self.almirah.id), "per_unit": "1"}]}, product_id=str(self.rack.id))
        self.assertIn("made to order", msg(body))
        with patch("apps.business.recipes.permitted", side_effect=lambda r, p: p != "manufacturing.manage"):
            status, _ = self.call(recipes_api.recipes, "post", {"materials": []}, product_id=str(self.rack.id))
        self.assertEqual(status, 403)
        status, _ = self.call(recipes_api.recipes, "delete", product_id=str(self.almirah.id))
        self.assertEqual(status, 200)
        self.assertFalse(recipes_api.made_to_order_ids(self.org.id, [self.almirah.id]))


class MadeToOrderSellingTests(ProductionFixture):
    def test_sales_order_does_not_need_finished_stock(self):
        """The reported bug: confirming a custom almirah failed with 'Inventory not found'."""
        so = SalesOrderService.create_sales_order(
            user=self.user, organization=self.org, customer=self.customer, warehouse=self.wh, order_date=date.today(),
            raw_items=[{"product": self.almirah, "quantity": "1", "unit_price": "25000"}],
        )
        with self.assertRaises(ValueError):
            SalesOrderService.confirm_sales_order(user=self.user, organization=self.org, sales_order_id=str(so.id))
        self.make_recipe()
        so.reload()
        SalesOrderService.confirm_sales_order(user=self.user, organization=self.org, sales_order_id=str(so.id))
        SalesOrderService.fulfill_sales_order(user=self.user, organization=self.org, sales_order_id=str(so.id),
                                              raw_items=[{"product": self.almirah, "quantity": "1"}])
        so.reload()
        self.assertEqual(so.status, "FULFILLED")
        self.assertFalse(Inventory.objects(organization=self.org, product=self.almirah).first(), "no finished stock record needed")

    def test_direct_invoice_uses_raw_materials_and_cancel_restores_them(self):
        self.make_recipe()
        status, body = self.call(direct_invoice, "post", {
            "invoice_date": "2026-11-27", "warehouse_id": str(self.wh.id),
            "customer": {"id": str(self.customer.id), "name": self.customer.name},
            "items": [{"sku": "ALM", "name": "Steel almirah", "quantity": "2", "unit_price": "25000"}],
        })
        self.assertEqual(status, 200, body)
        self.assertEqual((self.stock(self.ply), self.stock(self.hinge), self.stock(self.almirah)), (Decimal("12"), Decimal("84"), Decimal(0)))
        invoice = Invoice.objects(id=body["data"]["id"]).first()
        self.assertEqual(invoice.billing_details["recipe_snapshot"][str(self.almirah.id)][0]["per_unit"], "4")
        notes = [m.notes for m in StockMovement.objects(organization=self.org, reference_id=str(invoice.id))]
        self.assertTrue(all("made-to-order" in n for n in notes))
        # A later recipe change must not affect the reversal of this invoice.
        self.call(recipes_api.recipes, "post", {"made_to_order": True, "materials": [{"product": str(self.ply.id), "per_unit": "10"}]}, product_id=str(self.almirah.id))
        reverse(invoice, self.user)
        self.assertEqual((self.stock(self.ply), self.stock(self.hinge)), (Decimal("20"), Decimal("100")))

    def test_editing_a_made_to_order_invoice_moves_raw_materials(self):
        from apps.business.invoice_edit import edit
        self.make_recipe()
        status, body = self.call(direct_invoice, "post", {
            "invoice_date": "2026-11-27", "warehouse_id": str(self.wh.id), "customer": {"id": str(self.customer.id), "name": self.customer.name},
            "items": [{"sku": "ALM", "name": "Steel almirah", "quantity": "2", "unit_price": "25000"}],
        })
        self.assertEqual(status, 200, body)
        iid = body["data"]["id"]
        with patch("apps.business.invoice_edit.is_admin", return_value=True):
            status, snap = self.call(edit, invoice_id=iid)
            self.assertEqual(status, 200, snap)
            data = snap["data"]
            data["items"] = [{**data["items"][0], "quantity": "3"}]
            status, body = self.call(edit, "post", data, invoice_id=iid)
        self.assertEqual(status, 200, body)
        self.assertEqual((self.stock(self.ply), self.stock(self.hinge), self.stock(self.almirah)), (Decimal("8"), Decimal("76"), Decimal(0)))
        invoice = Invoice.objects(id=iid).first()
        self.assertIn(str(self.almirah.id), invoice.billing_details["recipe_snapshot"])

    def test_regular_goods_still_move_themselves(self):
        Inventory(organization=self.org, product=self.rack, warehouse=self.wh, quantity=Decimal("10")).save()
        status, body = self.call(direct_invoice, "post", {
            "invoice_date": "2026-11-27", "warehouse_id": str(self.wh.id), "customer": {"id": str(self.customer.id), "name": self.customer.name},
            "items": [{"sku": "RACK", "name": "Slotted rack", "quantity": "3", "unit_price": "3000"}],
        })
        self.assertEqual(status, 200, body)
        self.assertEqual((self.stock(self.rack), self.stock(self.ply)), (Decimal("7"), Decimal("20")))


class JobTests(ProductionFixture):
    def new_job(self, **extra):
        body = {"product_id": str(self.almirah.id), "quantity": "2", "customer_id": str(self.customer.id), "due": (date.today() + timedelta(days=5)).isoformat(),
                "priority": "high", "assignees": "Raju, Imran", "specification": "6 ft, 3 shelves, mirror door", "warehouse_id": str(self.wh.id)}
        body.update(extra)
        status, res = self.call(jobs_api.jobs, "post", body)
        self.assertEqual(status, 200, res)
        return res["data"]

    def act(self, job, **data):
        data.setdefault("revision", job["revision"])
        return self.call(jobs_api.jobs, "post", data, job_id=job["id"])

    def test_full_made_to_order_job(self):
        self.make_recipe()
        job = self.new_job()
        self.assertEqual(job["number"], "JOB-0001")
        self.assertEqual(job["title"], "Steel almirah")
        self.assertTrue(job["made_to_order"])
        self.assertEqual(job["quoted"], "50000.00")
        self.assertEqual(job["assignees"], ["Raju", "Imran"])
        self.assertEqual({m["name"]: m["planned"] for m in job["materials"]}, {"Plywood 18mm": "8", "Hinge": "16"})
        self.assertEqual(job["costs"]["planned_material"], "10240.00")

        status, body = self.act(job, action="stage", stage="cutting")
        self.assertEqual(status, 200, body)
        job = body["data"]
        self.assertEqual((job["stage_label"], job["progress"]), ("Cutting", 29))

        status, body = self.act(job, action="issue", product=str(self.ply.id), quantity="30")
        self.assertEqual(status, 400)
        self.assertIn("Only 20 SHEET of Plywood 18mm is available in Main godown", msg(body))
        status, body = self.act(job, action="issue", product=str(self.ply.id), quantity="8")
        job = body["data"]
        self.assertEqual(self.stock(self.ply), Decimal("12"))
        status, body = self.act(job, action="issue", product=str(self.hinge.id), quantity="16")
        job = body["data"]
        status, body = self.act(job, action="return", product=str(self.ply.id), quantity="1")
        job = body["data"]
        self.assertEqual(self.stock(self.ply), Decimal("13"))
        ply = next(m for m in job["materials"] if m["name"] == "Plywood 18mm")
        self.assertEqual((ply["issued"], ply["value"], ply["pending"]), ("7", "8400.00", "1"))

        status, body = self.act(job, action="labour", worker="Raju", hours="8", rate="400")
        job = body["data"]
        status, body = self.act(job, action="labour", worker="Imran", amount="2500")
        job = body["data"]
        status, body = self.act(job, action="expense", kind="transport", amount="800", note="Tempo to site")
        job = body["data"]
        c = job["costs"]
        self.assertEqual((c["material"], c["labour"], c["expenses"], c["total"]), ("9040.00", "5700.00", "800.00", "15540.00"))
        self.assertEqual((c["margin"], c["margin_pct"]), ("34460.00", "68.9"))
        imran = next(x for x in job["labour"] if x["worker"] == "Imran")
        status, body = self.act(job, action="remove_entry", kind="labour", id=imran["id"])
        job = body["data"]
        self.assertEqual(job["costs"]["labour"], "3200.00")

        status, body = self.act(job, action="complete")
        job = body["data"]
        self.assertEqual((job["status"], job["finished_to_stock"], job["progress"]), ("completed", False, 100))
        self.assertEqual(self.stock(self.almirah), Decimal(0), "made to order never enters stock")
        status, body = self.act(job, action="labour", worker="Raju", amount="100")
        self.assertIn("complete", msg(body))

        before = (self.stock(self.ply), self.stock(self.hinge))
        status, body = self.call(direct_invoice, "post", {
            "invoice_date": "2026-11-27", "warehouse_id": str(self.wh.id), "job_id": job["id"],
            "customer": {"id": str(self.customer.id), "name": self.customer.name},
            "items": [{"sku": "ALM", "name": "Steel almirah", "quantity": "2", "unit_price": "25000"}],
        })
        self.assertEqual(status, 200, body)
        self.assertEqual((self.stock(self.ply), self.stock(self.hinge)), before, "the job already used the materials")
        status, body = self.call(jobs_api.jobs, job_id=job["id"])
        job = body["data"]
        self.assertEqual(job["invoice"]["number"], Invoice.objects(id=job["invoice"]["id"]).first().invoice_number)
        status, body = self.call(direct_invoice, "post", {
            "invoice_date": "2026-11-27", "job_id": job["id"], "customer": {"id": str(self.customer.id), "name": self.customer.name},
            "items": [{"sku": "ALM", "name": "Steel almirah", "quantity": "2", "unit_price": "25000"}],
        })
        self.assertIn("already has invoice", msg(body))
        status, body = self.act(job, action="deliver")
        self.assertEqual(body["data"]["status"], "delivered")
        kinds = [e["kind"] for e in body["data"]["events"]]
        self.assertIn("invoice", kinds)
        self.assertEqual(kinds[0], "deliver", "newest first")

    def test_stocked_item_completes_into_stock_at_job_cost(self):
        job = self.new_job(product_id=str(self.rack.id), quantity="10", materials=[{"product": str(self.ply.id), "planned": "5"}])
        self.assertFalse(job["made_to_order"])
        status, body = self.call(direct_invoice, "post", {
            "invoice_date": "2026-11-27", "job_id": job["id"], "customer": {"id": str(self.customer.id), "name": self.customer.name},
            "items": [{"sku": "RACK", "name": "Slotted rack", "quantity": "10", "unit_price": "3000"}],
        })
        self.assertIn("Complete the job first", msg(body))
        _, body = self.act(job, action="issue", product=str(self.ply.id), quantity="5")
        _, body = self.act(body["data"], action="labour", worker="Raju", amount="2000")
        _, body = self.act(body["data"], action="complete", quantity="10")
        job = body["data"]
        self.assertTrue(job["finished_to_stock"])
        self.assertEqual(self.stock(self.rack), Decimal("10"))
        self.rack.reload()
        self.assertEqual(self.rack.cost_price, Decimal("800.00"))  # (6000 + 2000) / 10
        self.assertEqual(job["costs"]["unit_cost"], "800.00")

    def test_job_without_recipe_cancel_and_conflicts(self):
        job = self.new_job(product_id="", title="Shop counter for Gupta Medical", quantity="1", quoted="40000")
        self.assertEqual((job["title"], job["materials"], job["product"]), ("Shop counter for Gupta Medical", [], None))
        status, body = self.act(job, action="issue", product=str(self.ply.id), quantity="2")
        job2 = body["data"]
        self.assertEqual(job2["materials"][0]["planned"], "0", "unplanned material is added as it is issued")
        status, body = self.act(job, action="note", text="stale")
        self.assertIn("changed", msg(body))
        status, body = self.act(job2, action="cancel")
        self.assertIn("Return the issued material", msg(body))
        _, body = self.act(job2, action="return", product=str(self.ply.id), quantity="2")
        status, body = self.act(body["data"], action="cancel", reason="Customer cancelled")
        self.assertEqual(body["data"]["status"], "cancelled")
        self.assertEqual(self.stock(self.ply), Decimal("20"))
        status, body = self.act(body["data"], action="stage", stage="cutting")
        self.assertIn("cancelled", msg(body))

    def test_board_summary_filters_and_isolation(self):
        self.make_recipe()
        a = self.new_job()
        b = self.new_job(due=(date.today() - timedelta(days=2)).isoformat(), priority="urgent", title="Wardrobe for Mehta")
        self.new_job(due="", priority="low")
        self.act(a, action="hold", reason="Waiting for mirror")
        status, body = self.call(jobs_api.jobs)
        d = body["data"]
        self.assertEqual(d["rows"][0]["id"], b["id"], "overdue first")
        self.assertTrue(d["rows"][0]["overdue"])
        s = d["summary"]
        self.assertEqual((s["active"], s["on_hold"], s["overdue"], s["due_week"]), (3, 1, 1, 1))
        self.assertEqual(s["by_stage"][0], {"key": "design", "label": "Design & measurement", "count": 3})
        _, body = self.call(jobs_api.jobs, params={"search": "mehta"})
        self.assertEqual([r["id"] for r in body["data"]["rows"]], [b["id"]])
        _, body = self.call(jobs_api.jobs, params={"overdue": "1"})
        self.assertEqual(len(body["data"]["rows"]), 1)
        _, body = self.call(jobs_api.jobs, org=self.other)
        self.assertEqual(body["data"]["rows"], [])
        status, _ = self.call(jobs_api.jobs, job_id=a["id"], org=self.other)
        self.assertEqual(status, 404)
        with patch("apps.business.jobs.permitted", side_effect=lambda r, p: p != "manufacturing.manage"):
            status, _ = self.call(jobs_api.jobs, "post", {"title": "x"})
        self.assertEqual(status, 403)

    def test_custom_stages(self):
        status, body = self.call(jobs_api.job_settings, "post", {"stages": [{"label": "Welding"}, {"label": "Painting"}, {"label": "Packing"}]})
        self.assertEqual([s["key"] for s in body["data"]["stages"]], ["welding", "painting", "packing"])
        job = self.new_job(product_id="", title="Gate")
        self.assertEqual(job["stage"], "welding")
        status, body = self.call(jobs_api.job_settings, "post", {"stages": [{"label": "Painting"}, {"label": "Packing"}]})
        self.assertIn("open jobs", msg(body))


if __name__ == "__main__":
    unittest.main()
