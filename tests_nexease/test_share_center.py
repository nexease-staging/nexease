import bootstrap
import json
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.core import mail
from django.test import RequestFactory, override_settings
from mongoengine.connection import get_db

from apps.accounts.models import User
from apps.business import share_center as sc, tally_sync as ts
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.sales.models import Customer, CustomerPayment, Invoice, InvoiceItem, PaymentAllocation

import test_tally_sync as T


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


class ShareFixture(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Sharma Traders", email="s@example.com").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="Ravi", last_name="Sharma").save()
        self.perm = patch("apps.authorization.services.AuthorizationService.has_permission", return_value=True)
        self.perm.start()
        self.addCleanup(self.perm.stop)
        self.customer = Customer(organization=self.org, name="Acme Retail", code="C1", phone="98765 00001", email="acme@example.com", city="Pune").save()
        cat = Category(organization=self.org, name="Goods").save()
        self.product = Product(organization=self.org, sku="P1", name="Steel Rod", category=cat, unit="Nos").save()
        self.invoice = Invoice(organization=self.org, customer=self.customer, invoice_number="INV-7", status="ISSUED", invoice_date=datetime(2026, 11, 10, 6),
                               due_date=datetime(2026, 11, 25, 6), billing_name="Acme Retail", created_by=self.user, subtotal=Decimal(1000), tax_amount=Decimal(180),
                               total_amount=Decimal(1180), balance_due=Decimal(1180),
                               billing_details={"supply_type": "taxable", "place_of_supply": "27", "supplier_state": "27", "tax_reviewed": True},
                               items=[InvoiceItem(product=self.product, quantity=1, unit_price=1000, tax_rate=18, line_subtotal=1000, line_tax=180, line_total=1180, hsn_code="7214")]).save()

    def call(self, view, verb="get", data=None, **params):
        kwargs = params.pop("kw", {})
        factory = RequestFactory()
        request = factory.get("/", params) if verb == "get" else factory.post("/", data=json.dumps(data or {}), content_type="application/json")
        request.api_user, request.api_organization = self.user, self.org
        response = unwrap(view)(request, **kwargs)
        if response.get("Content-Type", "").startswith("application/json"):
            return response.status_code, json.loads(response.content)
        return response.status_code, response


class DocumentShareTests(ShareFixture):
    def test_prepare_invoice_has_recipient_message_and_live_link(self):
        status, body = self.call(sc.prepare, kind="invoice", id=str(self.invoice.id))
        d = body["data"]
        self.assertEqual(d["recipient"], {"name": "Acme Retail", "phone": "98765 00001", "email": "acme@example.com"})
        self.assertIn("invoice INV-7 for ₹1,180.00", d["whatsapp"])
        self.assertIn("Balance due ₹1,180.00 by 25 Nov 2026", d["whatsapp"])
        self.assertTrue(d["subject"].startswith("Invoice INV-7 from Sharma Traders"))
        self.assertIn("Ravi Sharma", d["body"])
        self.assertIn("/api/v1/business/share/l/", d["link"]["url"])
        status, again = self.call(sc.prepare, kind="invoice", id=str(self.invoice.id))
        self.assertEqual(again["data"]["link"]["token"], d["link"]["token"], "one link per document")
        status, response = self.call(sc.pdf, kind="invoice", id=str(self.invoice.id))
        self.assertTrue(response.content.startswith(b"%PDF"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_sends_pdf_attachment_and_logs(self):
        with patch("apps.core.services.user_mailbox_service.delivery_options", return_value={"from_email": "billing@nexease.test", "reply_to": ["r@example.com"]}):
            status, body = self.call(sc.email, "post", {"kind": "invoice", "id": str(self.invoice.id), "recipients": "acme@example.com, accounts@acme.test",
                                                        "subject": "Your invoice", "message": "Hi", "link": True})
        self.assertEqual(status, 200, body)
        sent = mail.outbox[-1]
        self.assertEqual(sent.to, ["acme@example.com", "accounts@acme.test"])
        self.assertEqual(sent.subject, "Your invoice")
        self.assertIn("View the latest version online:", sent.body)
        name, content, mime = sent.attachments[0]
        self.assertEqual((name, mime), ("Invoice-INV-7.pdf", "application/pdf"))
        self.assertTrue(content.startswith(b"%PDF"))
        status, body = self.call(sc.history, kind="invoice", id=str(self.invoice.id))
        self.assertEqual(body["data"]["history"][0]["channel"], "email")

    def test_email_rejects_bad_address(self):
        status, body = self.call(sc.email, "post", {"kind": "invoice", "id": str(self.invoice.id), "recipients": "not-an-email"})
        self.assertEqual(status, 400)
        self.assertIn("not a valid email", json.dumps(body))

    def test_whatsapp_share_is_logged(self):
        self.call(sc.log, "post", {"kind": "invoice", "id": str(self.invoice.id), "channel": "whatsapp", "recipient": "+91 98765 00001", "number": "INV-7"})
        status, body = self.call(sc.history)
        self.assertEqual(body["data"]["history"][0]["recipients"], ["+919876500001"])

    def test_other_business_document_is_not_found_and_permission_is_checked(self):
        other = Organization(name="Other", email="o@example.com").save()
        self.org, mine = other, self.org
        status, body = self.call(sc.prepare, kind="invoice", id=str(self.invoice.id))
        self.assertEqual(status, 404)
        self.org = mine
        self.perm.stop()
        with patch("apps.authorization.services.AuthorizationService.has_permission", return_value=False):
            status, body = self.call(sc.prepare, kind="invoice", id=str(self.invoice.id))
        self.perm.start()
        self.assertEqual(status, 403)


class StatementShareTests(ShareFixture):
    def test_customer_statement_and_public_link_follow_live_data(self):
        status, body = self.call(sc.prepare, kind="statement", id=str(self.customer.id), side="customer", **{"from": "2026-04-01", "to": "2026-11-30"})
        d = body["data"]
        self.assertEqual(d["extra"]["balance"], 1180.0)
        self.assertIn("The balance due is ₹1,180.00.", d["whatsapp"])
        self.assertTrue(d["filename"].startswith("Statement-Acme-Retail-01Apr2026"))
        token = d["link"]["token"]
        response = sc.public_link(RequestFactory().get("/"), token)
        self.assertEqual(response.status_code, 200)
        first = response.content
        self.assertTrue(first.startswith(b"%PDF"))
        CustomerPayment(organization=self.org, customer=self.customer, payment_number="RCPT-1", payment_date=datetime(2026, 11, 20, 6), amount=Decimal(1180),
                        payment_method="UPI", allocations=[PaymentAllocation(invoice=self.invoice, amount=Decimal(1180))], created_by=self.user).save()
        status, body = self.call(sc.prepare, kind="statement", id=str(self.customer.id), side="customer", **{"from": "2026-04-01", "to": "2026-11-30"})
        self.assertIn("fully settled", body["data"]["whatsapp"])
        self.assertEqual(body["data"]["link"]["token"], token)
        self.assertNotEqual(sc.public_link(RequestFactory().get("/"), token).content, first, "the link renders the current statement")
        self.assertEqual(get_db().share_links.find_one({"_id": token})["views"], 2)
        self.call(sc.revoke, "post", kw={"token": token})
        self.assertEqual(sc.public_link(RequestFactory().get("/"), token).status_code, 410)

    def test_statement_rows(self):
        from apps.business.statement_pdf import party_statement
        from datetime import date
        CustomerPayment(organization=self.org, customer=self.customer, payment_number="RCPT-2", payment_date=datetime(2026, 11, 12, 6), amount=Decimal(500),
                        payment_method="CASH", allocations=[PaymentAllocation(invoice=self.invoice, amount=Decimal(500))], created_by=self.user).save()
        Invoice.objects(id=self.invoice.id).update(set__balance_due=Decimal(680), set__status="PARTIALLY_PAID")
        data = party_statement(self.org, "customer", self.customer, date(2026, 11, 11), date(2026, 11, 30))
        self.assertEqual(data["opening"], 1180.0)
        self.assertEqual([(r["type"], r["balance"]) for r in data["rows"]], [("Receipt", 680.0)])
        self.assertEqual(data["bills"][0]["name"], "INV-7")

    def test_public_link_opens_without_sign_in_through_full_stack(self):
        from django.test import Client
        status, body = self.call(sc.prepare, kind="invoice", id=str(self.invoice.id))
        with override_settings(ALLOWED_HOSTS=["*"]):
            response = Client().get(f"/api/v1/business/share/l/{body['data']['link']['token']}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])

    def test_unknown_link(self):
        self.assertEqual(sc.public_link(RequestFactory().get("/"), "nope").status_code, 410)


class TallyShareTests(T.TallyFixture):
    def test_tally_ledger_and_voucher_share(self):
        self.cycle()
        guid = self.acme["guid"]
        status, body = self.call(sc.prepare, kind="tally_ledger", id=guid, **{"from": "2026-04-01", "to": "2026-11-30"})
        d = body["data"]
        self.assertEqual(d["recipient"]["phone"], "9876500001")
        self.assertEqual(d["extra"]["balance"], 680.0)
        self.assertIn("The balance due is ₹680.00.", d["whatsapp"])
        status, response = unwrap(sc.pdf)(self._req(kind="tally_ledger", id=guid)), None
        self.assertTrue(status.content.startswith(b"%PDF"))
        vguid = next(o["guid"] for o in get_db().tally_objects.find({"kind": "voucher"}))
        status, body = self.call(sc.prepare, kind="tally_voucher", id=vguid)
        self.assertEqual(body["data"]["recipient"]["phone"], "9876500001")
        self.assertTrue(unwrap(sc.pdf)(self._req(kind="tally_voucher", id=vguid)).content.startswith(b"%PDF"))

    def _req(self, **params):
        request = RequestFactory().get("/", params)
        request.api_user, request.api_organization = self.user, self.org
        return request


if __name__ == "__main__":
    unittest.main()
