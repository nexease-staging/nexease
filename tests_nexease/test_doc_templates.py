import bootstrap
import io
import json
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.test import RequestFactory
from mongoengine.connection import get_db
from pypdf import PdfReader

from apps.accounts.models import User
from apps.business import billing
from apps.business import doc_templates as dt
from apps.business.models import BusinessRecord
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.sales.models import Customer, Invoice, InvoiceItem


def text(pdf):
    return "".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


class TemplateTests(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Demo Traders", email="d@example.com", address="Shop 4, Market Yard, Pune", phone="9209753378").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="A", last_name="B").save()
        BusinessRecord(organization=self.org, kind="gst_settings", key="registration", created_by=self.user,
                       data={"gstin": "27AAACN1234F1Z5", "state_code": "27", "legal_name": "Demo Traders Pvt Ltd", "registration": "regular", "frequency": "monthly"}).save()
        cat = Category(organization=self.org, name="Goods").save()
        self.product = Product(organization=self.org, sku="P1", name="Cement", category=cat, unit="BAG", hsn_code="2523").save()

    def brand(self, **data):
        BusinessRecord.objects(organization=self.org, kind="invoice_settings", key="default").update_one(upsert=True, set__data=data, set__created_by=self.user)

    def invoice(self, pos="27", gstin="27AAPFS1234K1Z5"):
        customer = Customer(organization=self.org, name="Sharma Traders", code="C1").save()
        return Invoice(organization=self.org, customer=customer, invoice_number="INV-7", status="ISSUED", invoice_date=datetime(2026, 11, 26, 6), billing_name="Sharma Traders",
                       billing_address="12 MG Road, Pune", customer_gstin=gstin, created_by=self.user, subtotal=Decimal(1000), tax_amount=Decimal(280),
                       total_amount=Decimal(1280), balance_due=Decimal(1280), amount_paid=Decimal(0),
                       billing_details={"supply_type": "taxable", "place_of_supply": pos, "supplier_state": "27", "supplier_gstin": "27AAACN1234F1Z5", "tax_reviewed": True, "po_number": "PO-42"},
                       items=[InvoiceItem(product=self.product, item_name="Cement", hsn_code="2523", unit="BAG", quantity=4, unit_price=250, tax_rate=28,
                                          line_subtotal=1000, line_tax=280, line_total=1280)]).save()

    def test_every_template_renders_every_document_with_full_details(self):
        for template in dt.TEMPLATES:
            for kind in ("invoice", "quotation", "sales_order", "credit_note", "delivery_challan"):
                pdf = dt.render(dt.sample_document(self.org, kind), template[0], {"upi_id": "demo@okhdfcbank", "bank_details": "HDFC 5020", "terms": "No returns"})
                self.assertTrue(pdf.startswith(b"%PDF"), (template, kind))
                body = text(pdf)
                for expected in ("27AAACN1234F1Z5", "27AAPFS1234K1Z5", "2523", "Sharma Traders", "Rupees", "PO-4471"):
                    self.assertIn(expected, body, (template[0], kind, expected))
                self.assertIn("CGST", body, (template[0], kind))

    def test_invoice_uses_the_business_template_and_splits_tax(self):
        self.brand(template="minimal", accent_color="#be123c")
        inv = self.invoice()
        doc = dt.from_invoice(inv)
        self.assertEqual((doc["title"], doc["cgst"], doc["sgst"], doc["igst"]), ("Tax Invoice", Decimal("140.00"), Decimal("140.00"), Decimal(0)))
        self.assertEqual(doc["words"], "One Thousand Two Hundred Eighty Rupees Only")
        from apps.business.print_documents import invoice_pdf
        body = text(invoice_pdf(inv))
        self.assertIn("PO-42", body)
        self.assertIn("Maharashtra (27)", body)

    def test_inter_state_invoice_shows_igst(self):
        doc = dt.from_invoice(self.invoice(pos="29", gstin="29AAACB1234C1Z5"))
        self.assertTrue(doc["inter"])
        self.assertEqual(doc["igst"], Decimal("280.00"))
        body = text(dt.render(doc, "gst_classic", {}))
        self.assertIn("IGST", body)
        self.assertNotIn("SGST", body)

    def test_upi_qr_only_when_configured(self):
        doc = dt.sample_document(self.org, "invoice")
        self.assertIn("Scan & pay", text(dt.render(doc, "modern", {"upi_id": "demo@okicici"})))
        self.assertNotIn("Scan & pay", text(dt.render(doc, "modern", {})))
        challan = dt.sample_document(self.org, "delivery_challan")
        self.assertNotIn("Scan & pay", text(dt.render(challan, "modern", {"upi_id": "demo@okicici"})))

    def test_delivery_challan_prints_three_copies(self):
        pdf = dt.render(dt.sample_document(self.org, "delivery_challan"), "gst_classic", {})
        body = text(pdf)
        for label in ("Original for consignee", "Duplicate for transporter", "Triplicate for consignor"):
            self.assertIn(label, body)

    def test_legacy_formats_map_to_new_designs(self):
        self.assertEqual(dt.resolve("retail_emerald"), "retail")
        self.assertEqual(dt.resolve("classic"), "gst_classic")
        self.assertEqual(dt.resolve("nonsense"), "gst_classic")
        self.brand(template="executive")
        self.assertEqual(billing.settings(self.org)["template"], "modern")

    def test_round_off_to_rupee(self):
        doc = dt.finish({"kind": "quotation", "lines": [dt.make_line("A", "1001", 1, "NOS", "99.70", 0, 0)], "inter": False})
        self.assertEqual((doc["total"], doc["round_off"]), (Decimal("100.00"), Decimal("0.30")))

    def call(self, view, verb="get", data=None, **params):
        factory = RequestFactory()
        request = factory.get("/", params) if verb == "get" else factory.post("/", data=json.dumps(data or {}), content_type="application/json")
        request.api_user, request.api_organization = self.user, self.org
        with patch("apps.authorization.services.AuthorizationService.has_permission", return_value=True):
            return unwrap(view)(request)

    def test_settings_validate_upi_and_map_template(self):
        response = self.call(billing.invoice_settings, "post", {"template": "bold", "upi_id": "not-an-upi"})
        self.assertEqual(response.status_code, 400)
        response = self.call(billing.invoice_settings, "post", {"template": "bold", "upi_id": "demo@okhdfcbank"})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(json.loads(response.content)["data"]["settings"]["template"], "modern")
        self.assertEqual(len(json.loads(response.content)["data"]["templates"]), 6)

    def test_preview_endpoint(self):
        response = self.call(billing.template_preview, template="thermal", kind="quotation", accent="#be123c")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertEqual(self.call(billing.template_preview, template="x", kind="invoice").status_code, 400)
        self.assertEqual(self.call(billing.template_preview, template="modern", kind="payslip").status_code, 400)


if __name__ == "__main__":
    unittest.main()
