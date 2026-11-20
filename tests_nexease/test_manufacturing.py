import bootstrap
import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from unittest.mock import patch
from bson import ObjectId
from django.test import RequestFactory
from django.core.management import call_command
from mongoengine.connection import get_db
from apps.business.manufacturing import orders
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.products.models import Category, Product
from apps.inventory.models import Warehouse
from apps.business.books import ensure_accounts


@unittest.skipUnless(
    os.getenv("NEXEASE_LOCAL_REPLICA_TEST") == "1",
    "requires isolated loopback MongoDB replica set on port 27183",
)
class ProductionTransactions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mongoengine

        mongoengine.disconnect()
        mongoengine.connect(
            "nexease_test_mfg_" + uuid4().hex,
            host="mongodb://127.0.0.1:27183/?replicaSet=nxcheck",
            serverSelectionTimeoutMS=4000,
        )
        call_command("ensure_manufacturing_indexes")

    @classmethod
    def tearDownClass(cls):
        import mongoengine, mongomock

        mongoengine.disconnect()
        mongoengine.connect(
            "nexease_test_isolated",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
        )

    def setUp(self):
        self.db = get_db()
        self.org = Organization(name="Test", email=uuid4().hex + "@example.com").save()
        self.actor = User(
            organization=self.org,
            email=uuid4().hex + "@example.com",
            password="test",
            first_name="A",
            last_name="B",
        ).save()
        permission = patch(
            "apps.authorization.services.AuthorizationService.has_permission",
            return_value=True,
        )
        permission.start()
        self.addCleanup(permission.stop)
        ensure_accounts(self.org, self.actor)
        cat = Category(organization=self.org, name="Materials").save()

        def product(name, rate):
            return Product(
                organization=self.org,
                category=cat,
                sku=name,
                name=name,
                unit="PCS",
                cost_price=rate,
                selling_price=100,
            ).save()

        self.raw = product("Wood", 10)
        self.finished = product("Desk", 20)
        self.wh = Warehouse(organization=self.org, code="W", name="Works").save()
        self.db.inventory.insert_one(
            dict(
                organization=self.org.id,
                product=self.raw.id,
                warehouse=self.wh.id,
                quantity=12.0,
                reserved_quantity=1.0,
            )
        )
        self.plan = dict(
            due="2026-12-15",
            warehouse=str(self.wh.id),
            outputs=[
                dict(
                    product=str(self.finished.id),
                    quantity="3",
                    specification="120 cm",
                    materials=[dict(product=str(self.raw.id), per_unit="2")],
                )
            ],
        )
        r = self.send(self.plan)
        self.assertEqual(r.status_code, 200, r.content)
        self.job = json.loads(r.content)["data"]["id"]

    def send(self, body, job=None):
        req = RequestFactory().post(
            "/",
            data=json.dumps({"request_key": str(uuid4()), **body}),
            content_type="application/json",
        )
        req.api_organization = self.org
        req.api_user = self.actor
        return orders.__wrapped__(req, job)

    def entry(self, act, rev, **kw):
        return self.send(
            dict(
                action=act,
                revision=rev,
                batch="B1",
                line=0,
                material=str(self.raw.id),
                **kw
            ),
            self.job,
        )

    def test_issue_return_produce_close_retry(self):
        for i, (act, q) in enumerate([("allocate", 6), ("issue", 6), ("return", 1)]):
            r = self.entry(act, i + 1, quantity=q)
            self.assertEqual(r.status_code, 200, r.content)
        token = str(uuid4())
        for _ in range(2):
            r = self.entry(
                "produce", 4, accepted=2, rejected=1, labour=10, request_key=token
            )
            self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(
            self.entry("produce", 4, accepted=3, request_key=token).status_code, 400
        )
        self.assertEqual(self.entry("close", 5).status_code, 200)
        self.assertEqual(self.finished.reload().cost_price, 30)
        self.assertEqual(
            self.db.inventory.find_one({"product": self.raw.id})["quantity"], 7
        )
        self.assertEqual(
            self.db.inventory.find_one({"product": self.finished.id})["quantity"], 2
        )
        self.assertEqual(
            self.db.journal_entries.count_documents({"organization": self.org.id}), 4
        )
        self.assertEqual(
            self.db.manufacturing_events.count_documents({"order": ObjectId(self.job)}),
            6,
        )

    def test_rollback_if_journal_fails(self):
        self.db.chart_of_accounts.update_one(
            {"organization": self.org.id, "system_key": "INVENTORY"},
            {"$set": {"is_active": False}},
        )
        self.assertEqual(self.entry("issue", 1, quantity=2).status_code, 400)
        self.assertEqual(
            self.db.inventory.find_one({"product": self.raw.id})["quantity"], 12
        )
        self.assertEqual(
            self.db.stock_movements.count_documents({"organization": self.org.id}), 0
        )
        self.assertEqual(
            self.db.manufacturing_orders.find_one({"_id": ObjectId(self.job)})[
                "revision"
            ],
            1,
        )

    def test_competing_orders_cannot_consume_reserved_stock(self):
        second = json.loads(self.send(self.plan).content)["data"]["id"]

        def issue(job):
            return self.send(
                dict(
                    action="issue",
                    revision=1,
                    batch="B1",
                    line=0,
                    material=str(self.raw.id),
                    quantity=8,
                ),
                job,
            ).status_code

        with ThreadPoolExecutor(2) as pool:
            self.assertEqual(sorted(pool.map(issue, [self.job, second])), [200, 400])
        self.assertEqual(
            self.db.inventory.find_one({"product": self.raw.id})["quantity"], 4
        )

    def test_custom_order_through_delivery_invoice_and_payment(self):
        from datetime import datetime
        from apps.sales.models import Customer
        from apps.sales.services.sales_order_service import SalesOrderService as Sales
        from apps.sales.services.invoice_service import InvoiceService
        from apps.sales.services.payment_service import PaymentService
        from apps.finance.models import BankAccount

        buyer = Customer(organization=self.org, code="C", name="Buyer").save()
        args = dict(user=self.actor, organization=self.org)
        so = Sales.create_sales_order(
            **args,
            customer=buyer,
            warehouse=self.wh,
            order_date=datetime.now(),
            raw_items=[
                {
                    "product": self.finished,
                    "quantity": 3,
                    "unit_price": 100,
                    "tax_rate": 0,
                    "discount": 0,
                }
            ]
        )
        edit = self.send(
            {**self.plan, "sales_order": str(so.id), "action": "edit", "revision": 1},
            self.job,
        )
        self.assertEqual(edit.status_code, 200, edit.content)
        for batch, rev, count in [("one", 2, 1), ("two", 4, 2)]:
            base = dict(line=0, batch=batch, material=str(self.raw.id))
            for step in [
                dict(action="issue", revision=rev, quantity=count * 2),
                dict(action="produce", revision=rev + 1, accepted=count),
            ]:
                r = self.send({**base, **step}, self.job)
                self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.entry("close", 6).status_code, 200)
        Sales.confirm_sales_order(**args, sales_order_id=so.id)
        for qty in [1, 2]:
            Sales.fulfill_sales_order(
                **args,
                sales_order_id=so.id,
                raw_items=[{"product": self.finished, "quantity": qty}]
            )
        inv = InvoiceService.generate_from_sales_order(**args, sales_order=so.reload())
        InvoiceService.issue_invoice(**args, invoice_id=inv.id)
        bank = BankAccount(
            organization=self.org,
            account_name="Test bank",
            account_type="BANK",
            created_by=self.actor,
        ).save()
        PaymentService.record_invoice_payment(
            **args,
            invoice=inv.reload(),
            bank_account=bank,
            amount=100,
            payment_method="BANK_TRANSFER"
        )
        req = RequestFactory().get("/")
        req.api_organization = self.org
        req.api_user = self.actor
        result = json.loads(orders.__wrapped__(req, self.job).content)["data"]
        self.assertEqual(result["net_revenue"], "300.00")
        self.assertEqual(result["revenue_less_job_cost"], "240.00")
        self.assertEqual(float(result["sales"][0]["due"]), 200)

    def test_tenant_and_role_boundaries(self):
        req = RequestFactory().get("/")
        req.api_user = self.actor
        req.api_organization = Organization(
            name="Other", email=uuid4().hex + "@example.com"
        ).save()
        self.assertEqual(orders.__wrapped__(req, self.job).status_code, 404)
        with patch("apps.business.manufacturing.permitted", return_value=False):
            self.assertEqual(self.entry("issue", 1, quantity=1).status_code, 403)

    def test_old_inventory_screen_cannot_overwrite_a_production_issue(self):
        from apps.inventory.models import Inventory
        from apps.inventory.repositories.inventory_repository import InventoryRepository

        stale = Inventory.objects(organization=self.org, product=self.raw).get()
        self.assertEqual(self.entry("issue", 1, quantity=3).status_code, 200)
        with self.assertRaisesRegex(ValueError, "Stock changed"):
            InventoryRepository.update_quantity(inventory=stale, quantity=20)
        self.assertEqual(stale.reload().quantity, 9)

    def test_report_filters_export_editing_and_rejected_only_batch(self):
        self.assertEqual(self.entry("issue", 1, quantity=1).status_code, 200)
        self.assertEqual(
            self.entry("produce", 2, accepted=0, rejected=1, machine=5).status_code, 200
        )
        self.assertEqual(self.entry("close", 3).status_code, 200)
        for query in (
            "?export=csv&report=materials",
            "?export=csv&report=batches",
            "?export=csv&report=costs",
        ):
            req = RequestFactory().get("/" + query)
            req.api_user = self.actor
            req.api_organization = self.org
            response = orders.__wrapped__(req)
            self.assertEqual(response.status_code, 200, response.content)
            self.assertIn(b"MO-", response.content)
        self.assertFalse(self.db.inventory.find_one({"product": self.finished.id}))
        self.assertEqual(
            self.send(
                {**self.plan, "action": "edit", "revision": 4}, self.job
            ).status_code,
            400,
        )
