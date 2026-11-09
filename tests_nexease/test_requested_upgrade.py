import bootstrap
import json, re, unittest
from datetime import datetime
from decimal import Decimal as D
from unittest.mock import patch
from django.test import RequestFactory, override_settings
from django.core import mail
from mongoengine.connection import get_db
from test_launch_polish import LaunchPolishTests
from apps.inventory.models import Inventory, Warehouse, StockMovement
from apps.business.models import BusinessRecord as Record
from apps.business.quick_stock import move, reverse
from apps.business.invoice_edit import edit, snapshot
from apps.core.services.email_verification import request_link, confirm, verified
from apps.business.reorder import scan
from apps.core.notification_models import Notification


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        LaunchPolishTests.setUp(self)
        mail.outbox = []

    invoice = LaunchPolishTests.invoice

    def test_quick_stock_negative_once_and_reversal(self):
        inv = self.invoice()
        wh = Warehouse(organization=self.org, name="Main", code="M").save()
        move(inv, self.user, wh)
        move(inv, self.user, wh)
        self.assertEqual(Inventory.objects.first().quantity, D("-10"))
        self.assertEqual(StockMovement.objects.count(), 1)
        reverse(inv, self.user)
        reverse(inv, self.user)
        self.assertEqual(Inventory.objects.first().quantity, D("0"))
        self.assertEqual(StockMovement.objects.count(), 2)

    def test_reorder_one_alert_per_episode(self):
        wh = Warehouse(organization=self.org, name="Main", code="M").save()
        stock = Inventory(
            organization=self.org, warehouse=wh, product=self.product, quantity=3
        ).save()
        Record(
            organization=self.org,
            kind="reorder_rule",
            key=str(self.product.id),
            data={"enabled": True, "level": "5"},
            created_by=self.user,
        ).save()
        with patch(
            "apps.authorization.services.AuthorizationService.has_permission",
            return_value=True,
        ):
            scan(self.user)
            scan(self.user)
            self.assertEqual(Notification.objects.count(), 1)
            stock.quantity = 7
            stock.save()
            scan(self.user)
            stock.quantity = 2
            stock.save()
            scan(self.user)
            self.assertEqual(Notification.objects.count(), 2)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_ORIGINS=["https://app.example.test"],
    )
    def test_verification_link_single_use_and_email_binding(self):
        request_link(self.user, "https://app.example.test")
        from urllib.parse import urlparse, parse_qs

        url = re.search(r"https://\S+", mail.outbox[-1].body).group()
        token = parse_qs(urlparse(url).query)["token"][0]
        self.assertFalse(verified(self.user))
        confirm(token)
        self.assertTrue(verified(self.user))
        with self.assertRaises(ValueError):
            confirm(token)
        self.user.email = "changed@example.test"
        self.user.save()
        self.assertFalse(verified(self.user))

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_ORIGINS=["https://app.example.test"],
    )
    def test_tampered_token_cannot_verify(self):
        request_link(self.user, "https://app.example.test")
        with self.assertRaises(ValueError):
            confirm("tampered-token")
        self.assertFalse(verified(self.user))

    def request(self, inv, data):
        req = RequestFactory().post(
            "/edit/", data=json.dumps(data), content_type="application/json"
        )
        req.api_user = self.user
        req.api_organization = self.org
        view = edit
        while hasattr(view, "__wrapped__"):
            view = view.__wrapped__
        with patch("apps.business.invoice_edit.is_admin", return_value=True), patch(
            "apps.business.invoice_edit.permitted", return_value=True
        ), patch(
            "apps.authorization.services.AuthorizationService.has_permission",
            return_value=True,
        ):
            return view(req, str(inv.id))

    def test_edit_draft_recalculates_and_rejects_stale_version(self):
        inv = self.invoice()
        inv.status = "DRAFT"
        inv.save()
        data = snapshot(inv)
        data["items"][0]["unit_price"] = "200"
        response = self.request(inv, data)
        self.assertEqual(response.status_code, 200, response.content)
        inv.reload()
        self.assertEqual(inv.total_amount, D("2360"))
        self.assertEqual(inv.balance_due, D("2360"))
        self.assertEqual(self.request(inv, data).status_code, 400)

    def test_issued_edit_posts_balanced_delta(self):
        inv = self.invoice()
        from apps.business.books import ensure_accounts

        ensure_accounts(self.org, self.user)
        from apps.sales.services.invoice_service import InvoiceService

        with patch(
            "apps.authorization.services.AuthorizationService.has_permission",
            return_value=True,
        ):
            InvoiceService._post_invoice_accounting(
                user=self.user, organization=self.org, invoice=inv
            )
        data = snapshot(inv)
        data["items"][0]["unit_price"] = "200"
        response = self.request(inv, data)
        self.assertEqual(response.status_code, 200, response.content)
        from apps.finance.models import JournalEntry

        journal = JournalEntry.objects(
            source_type="SALES_INVOICE", source_id__contains=":edit:"
        ).first()
        self.assertEqual(journal.status, "POSTED")
        self.assertEqual(
            sum(i.debit for i in journal.lines), sum(i.credit for i in journal.lines)
        )
        inv.reload()
        self.assertEqual(inv.total_amount, D("2360"))

    def test_paid_invoice_cannot_be_cut_below_paid(self):
        inv = self.invoice()
        inv.status = "PAID"
        inv.amount_paid = inv.total_amount
        inv.balance_due = 0
        inv.save()
        data = snapshot(inv)
        data["items"][0]["unit_price"] = "1"
        response = self.request(inv, data)
        self.assertEqual(response.status_code, 400)
        inv.reload()
        self.assertEqual(inv.total_amount, D("1180"))

    def test_stock_compensation_when_movement_save_fails(self):
        inv = self.invoice()
        wh = Warehouse(organization=self.org, name="Main", code="M").save()
        with patch.object(
            StockMovement, "save", side_effect=ValueError("test failure")
        ):
            with self.assertRaises(ValueError):
                move(inv, self.user, wh)
        self.assertEqual(Inventory.objects.first().quantity, D(0))
        self.assertFalse(inv.billing_details.get("quick_stock_applied"))

    def test_partial_restock_can_reduce_negative_balance(self):
        inv = self.invoice()
        wh = Warehouse(organization=self.org, name="Main", code="M").save()
        move(inv, self.user, wh)
        from apps.inventory.services.inventory_service import InventoryService

        with patch(
            "apps.authorization.services.AuthorizationService.has_permission",
            return_value=True,
        ):
            InventoryService.adjust_quantity(
                user=self.user,
                organization=self.org,
                inventory_id=str(Inventory.objects.first().id),
                quantity_change="3",
                notes="Partial restock",
            )
        self.assertEqual(Inventory.objects.first().quantity, D("-7"))

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_ORIGINS=["https://app.example.test"],
    )
    def test_changed_address_requires_new_link(self):
        from urllib.parse import urlparse, parse_qs

        request_link(self.user, "https://app.example.test")
        token = parse_qs(
            urlparse(re.search(r"https://\S+", mail.outbox[-1].body).group()).query
        )["token"][0]
        confirm(token)
        self.user.email = "changed@example.test"
        self.user.save()
        request_link(self.user, "https://app.example.test")
        self.assertFalse(verified(self.user))

    def test_failed_journal_post_restores_invoice_and_stock(self):
        inv = self.invoice()
        wh = Warehouse(organization=self.org, name="Main", code="M").save()
        move(inv, self.user, wh)
        from apps.business.books import ensure_accounts

        ensure_accounts(self.org, self.user)
        from apps.sales.services.invoice_service import InvoiceService

        with patch(
            "apps.authorization.services.AuthorizationService.has_permission",
            return_value=True,
        ):
            InvoiceService._post_invoice_accounting(
                user=self.user, organization=self.org, invoice=inv
            )
        data = snapshot(inv)
        data["items"][0]["quantity"] = "20"
        with patch(
            "apps.finance.services.journal_entry_service.JournalEntryService.post_journal",
            side_effect=ValueError("posting unavailable"),
        ):
            response = self.request(inv, data)
        self.assertEqual(response.status_code, 400, response.content)
        inv.reload()
        self.assertEqual(inv.total_amount, D("1180"))
        self.assertEqual(Inventory.objects.first().quantity, D("-10"))

    def test_payslip_queue_keeps_recipients_separate_and_deduplicates(self):
        from apps.business.payslip_distribution import distribute, execute
        from apps.core.background_job_models import BackgroundJob
        from django.core import mail

        people = []
        rows = []
        for i in range(2):
            employee = Record(
                organization=self.org,
                kind="employees",
                key=str(i),
                data={
                    "name": "Employee " + str(i),
                    "email": f"employee{i}@example.test",
                },
                created_by=self.user,
            ).save()
            people.append(employee)
            rows.append(
                {
                    "employee_id": str(employee.id),
                    "employee": {"name": employee.data["name"], "code": str(i)},
                    "result": {"net": "1000"},
                    "inputs": {},
                }
            )
        run = Record(
            organization=self.org,
            kind="payruns",
            key="2026-11",
            data={"status": "approved", "rows": rows},
            created_by=self.user,
        ).save()
        req = RequestFactory().post(
            "/distribution/",
            data=json.dumps({"employee_ids": [str(e.id) for e in people]}),
            content_type="application/json",
        )
        req.api_user = self.user
        req.api_organization = self.org
        view = distribute
        while hasattr(view, "__wrapped__"):
            view = view.__wrapped__
        with patch(
            "apps.business.payslip_distribution.permitted", return_value=True
        ), patch(
            "apps.business.payslip_distribution.delivery_options", return_value={}
        ):
            self.assertEqual(view(req, str(run.id)).status_code, 200)
            self.assertEqual(view(req, str(run.id)).status_code, 200)
        self.assertEqual(BackgroundJob.objects.count(), 2)
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ), patch(
            "apps.authorization.services.AuthorizationService.has_permission",
            return_value=True,
        ), patch(
            "apps.business.payslip_distribution.delivery_options", return_value={}
        ), patch(
            "apps.business.payslip_distribution.payslip_pdf", return_value=b"%PDF-test"
        ):
            job = BackgroundJob.objects.first()
            execute(job=job)
            execute(job=job)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].to, [job.payload["email"]])
            self.assertEqual(len(mail.outbox[0].attachments), 1)

    def test_quick_invoice_new_product_is_negative_five(self):
        from apps.business.direct_entry import direct_invoice
        from apps.products.models import Product

        Warehouse(organization=self.org, name="Main", code="M").save()
        body = {
            "invoice_date": "2026-11-09",
            "customer": {"id": str(self.customer.id), "name": self.customer.name},
            "items": [
                {
                    "sku": "NEW-QUICK",
                    "name": "Quick item",
                    "quantity": "5",
                    "unit_price": "10",
                    "unit": "PCS",
                    "tax_rate": "0",
                }
            ],
        }
        req = RequestFactory().post(
            "/direct/", data=json.dumps(body), content_type="application/json"
        )
        req.api_user = self.user
        req.api_organization = self.org
        view = direct_invoice
        while hasattr(view, "__wrapped__"):
            view = view.__wrapped__
        with patch(
            "apps.authorization.services.AuthorizationService.has_permission",
            return_value=True,
        ):
            response = view(req)
        self.assertEqual(response.status_code, 200, response.content)
        product = Product.objects(sku="NEW-QUICK").first()
        self.assertEqual(Inventory.objects(product=product).first().quantity, D("-5"))

    def test_stale_invoice_cannot_reverse_stock_twice(self):
        from apps.sales.models import Invoice

        inv = self.invoice()
        wh = Warehouse(organization=self.org, name="Main", code="M").save()
        move(inv, self.user, wh)
        stale = Invoice.objects(id=inv.id).first()
        reverse(inv, self.user)
        reverse(stale, self.user)
        self.assertEqual(Inventory.objects.first().quantity, D("0"))


if __name__ == "__main__":
    unittest.main()
