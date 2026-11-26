import bootstrap
import json
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from mongoengine.connection import get_db

from apps.accounts.models import User
from apps.business import gst_compliance as gst
from apps.business.models import BusinessRecord
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.purchasing.models import Supplier, VendorBill, VendorBillItem
from apps.sales.models import Customer, Invoice, InvoiceItem

OWN = "27AAACN1234F1Z5"
OM = "27AAPFU0939F1ZV"      # same state: CGST + SGST
DELHI = "07AABCS1429B1ZB"   # other state: IGST


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


def gstr2b(period="102026", gstin=OWN):
    return {"data": {"gstin": gstin, "rtnprd": period, "docdata": {
        "b2b": [
            {"ctin": OM, "trdnm": "Om Steel", "inv": [
                {"inum": "OMS/0221", "dt": "05-10-2026", "val": 15340, "pos": "27", "rev": "N", "itcavl": "Y", "txval": 13000, "igst": 0, "cgst": 1170, "sgst": 1170, "cess": 0},
                {"inum": "OMS/0222", "dt": "06-10-2026", "val": 11800, "pos": "27", "rev": "N", "itcavl": "Y", "txval": 10000, "igst": 0, "cgst": 900, "sgst": 900, "cess": 0},
                {"inum": "RC-1", "dt": "07-10-2026", "val": 5000, "pos": "27", "rev": "Y", "itcavl": "Y", "txval": 5000, "igst": 0, "cgst": 450, "sgst": 450, "cess": 0}]},
            {"ctin": DELHI, "trdnm": "Sharma Exports", "inv": [
                {"inum": "SE-9", "dt": "10-10-2026", "val": 11800, "pos": "27", "rev": "N", "itcavl": "Y", "txval": 10000, "igst": 1800, "cgst": 0, "sgst": 0, "cess": 0}]}],
        "cdnr": [{"ctin": OM, "trdnm": "Om Steel", "nt": [
            {"ntnum": "CN-4", "typ": "C", "dt": "12-10-2026", "val": 1180, "pos": "27", "rev": "N", "itcavl": "Y", "txval": 1000, "igst": 0, "cgst": 90, "sgst": 90, "cess": 0}]}]}}}


class GstFixture(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="GST org", email="g@example.com").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="A", last_name="B").save()
        patcher = patch("apps.authorization.services.AuthorizationService.has_permission", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        BusinessRecord(organization=self.org, kind="gst_settings", key="registration", created_by=self.user,
                       data={"gstin": OWN, "state_code": "27", "legal_name": "GST org", "registration": "regular", "frequency": "monthly"}).save()
        cat = Category(organization=self.org, name="Goods").save()
        self.product = Product(organization=self.org, sku="P1", name="Steel", category=cat, unit="KG").save()
        self.om = Supplier(organization=self.org, name="Om Steel", code="S1", gstin=OM).save()

    def bill(self, number, taxable, tax, when=datetime(2026, 10, 5, 6), gstin=OM, status="POSTED", paid=False):
        total = taxable + tax
        return VendorBill(organization=self.org, supplier=self.om, bill_number="B-" + number, supplier_invoice_number=number, status=status,
                          bill_date=when, created_by=self.user, supplier_name="Om Steel", supplier_gstin=gstin,
                          items=[VendorBillItem(product=self.product, quantity=1, unit_price=taxable, line_total=total)],
                          subtotal=taxable, tax_amount=tax, total_amount=total, balance_due=0 if paid else total).save()

    def invoice(self, number, taxable, rate, gstin="", pos="27", when=datetime(2026, 10, 10, 6), hsn="7214"):
        tax = (Decimal(taxable) * Decimal(rate) / 100).quantize(Decimal("0.01"))
        customer = Customer(organization=self.org, name="Buyer " + number, code="C" + number).save()
        return Invoice(organization=self.org, customer=customer, invoice_number=number, status="ISSUED", invoice_date=when, billing_name="Buyer",
                       customer_gstin=gstin, created_by=self.user, total_amount=Decimal(taxable) + tax, tax_amount=tax, balance_due=Decimal(taxable) + tax,
                       billing_details={"supply_type": "taxable", "place_of_supply": pos, "supplier_state": "27", "tax_reviewed": True},
                       items=[InvoiceItem(product=self.product, quantity=1, unit_price=taxable, tax_rate=rate, line_subtotal=taxable, line_tax=tax,
                                          line_total=Decimal(taxable) + tax, hsn_code=hsn)]).save()

    def call(self, view, verb="get", data=None, files=None, **params):
        factory = RequestFactory()
        kwargs = params.pop("kw", {})
        if verb == "get":
            request = factory.get("/", params)
        elif files:
            request = factory.post("/", {**(data or {}), **files})
        else:
            request = factory.post("/", data=json.dumps(data or {}), content_type="application/json")
        request.api_user, request.api_organization = self.user, self.org
        response = unwrap(view)(request, **kwargs)
        try:
            return response.status_code, json.loads(response.content)
        except ValueError:
            return response.status_code, response

    def upload(self, raw=None):
        f = SimpleUploadedFile("GSTR2B.json", json.dumps(raw or gstr2b()).encode(), content_type="application/json")
        return self.call(gst.ims, "post", files={"file": f})


class ImportTests(GstFixture):
    def test_parses_portal_gstr2b(self):
        period, rows = gst.parse_gstr2b(gstr2b(), self.org)
        self.assertEqual(period, "2026-10")
        self.assertEqual(len(rows), 5)
        first = rows[0]
        self.assertEqual((first["doc_key"], first["doc_date"], first["cgst"], first["total_tax"]), ("OMS221", "2026-10-05", "1170.00", "2340.00"))
        self.assertTrue(next(r for r in rows if r["doc_number"] == "RC-1")["rcm"])
        self.assertEqual(next(r for r in rows if r["doc_number"] == "CN-4")["doc_type"], "CN")

    def test_rejects_another_businesses_file(self):
        with self.assertRaises(ValueError):
            gst.parse_gstr2b(gstr2b(gstin=DELHI), self.org)

    def test_reimport_refreshes_amounts_but_keeps_decisions(self):
        status, body = self.upload()
        self.assertEqual((status, body["data"]["added"]), (200, 5))
        doc = gst.col().find_one({"doc_number": "OMS/0222"})
        self.call(gst.ims_action, "post", {"ids": [str(doc["_id"])], "action": "pending", "reason": "Rate query"})
        status, body = self.upload()
        self.assertEqual((body["data"]["added"], body["data"]["updated"]), (0, 5))
        self.assertEqual(gst.col().find_one({"_id": doc["_id"]})["action"], "pending")

    def test_csv_template_import(self):
        csv = ",".join(gst.TEMPLATE_HEADERS) + "\n" + f"{OM},Om Steel,INV,X-1,01-10-2026,1000,0,90,90,0,27,N\n"
        f = SimpleUploadedFile("ims.csv", csv.encode(), content_type="text/csv")
        status, body = self.call(gst.ims, "post", data={"period": "2026-10"}, files={"file": f})
        self.assertEqual(status, 200, body)
        self.assertEqual(gst.col().count_documents({"source": "csv"}), 1)
        bad = SimpleUploadedFile("ims.csv", (",".join(gst.TEMPLATE_HEADERS) + "\nBADGSTIN,x,INV,1,01-10-2026,1,0,0,0,0,27,N\n").encode())
        status, body = self.call(gst.ims, "post", data={"period": "2026-10"}, files={"file": bad})
        self.assertEqual(status, 400)
        self.assertIn("Row 2", json.dumps(body))


class ReconcileAndImsTests(GstFixture):
    def test_matching_statuses_and_suggestions(self):
        self.bill("OMS-221", 13000, 2340)          # same invoice, different formatting → matched
        self.bill("OMS/222", 10000, 1500)          # tax differs → mismatch
        self.bill("OMS/300", 5000, 900)            # not in 2B → missing
        self.upload()
        status, body = self.call(gst.ims, period="2026-10")
        rows = {r["doc_number"]: r for r in body["data"]["records"]}
        self.assertEqual(rows["OMS/0221"]["match"]["status"], "matched")
        self.assertEqual(rows["OMS/0221"]["suggested"], "accept")
        self.assertEqual(rows["OMS/0222"]["match"]["status"], "mismatch")
        self.assertEqual(rows["OMS/0222"]["suggested"], "pending")
        self.assertEqual(rows["SE-9"]["match"]["status"], "only_in_2b")
        self.assertEqual(rows["RC-1"]["suggested"], "none")
        self.assertEqual([b["number"] for b in body["data"]["missing_in_2b"]], ["OMS/300"])

    def test_action_rules(self):
        self.upload()
        ids = {d["doc_number"]: str(d["_id"]) for d in gst.col().find()}
        status, body = self.call(gst.ims_action, "post", {"ids": [ids["SE-9"]], "action": "reject"})
        self.assertEqual(status, 400)
        self.assertIn("reason", body["error"]["message"])
        status, body = self.call(gst.ims_action, "post", {"ids": [ids["RC-1"], ids["SE-9"]], "action": "reject", "reason": "Not our purchase"})
        self.assertEqual(body["data"]["skipped"], ["RC-1"])
        status, body = self.call(gst.ims_action, "post", {"ids": [ids["CN-4"]], "action": "accept", "itc_reduce": "500"})
        self.assertEqual(status, 400)
        status, _ = self.call(gst.ims_action, "post", {"ids": [ids["CN-4"]], "action": "accept", "itc_reduce": "90"})
        self.assertEqual(status, 200)
        self.assertEqual(gst.col().find_one({"doc_number": "CN-4"})["itc_reduce"], "90.00")

    def test_manual_link(self):
        bill = self.bill("TOTALLY-DIFFERENT", 10000, 1800, gstin=DELHI)
        self.upload()
        rec = gst.col().find_one({"doc_number": "SE-9"})
        status, _ = self.call(gst.link_bill, "post", {"record_id": str(rec["_id"]), "bill_id": str(bill.id)})
        self.assertEqual(status, 200)
        _, body = self.call(gst.ims, period="2026-10")
        row = next(r for r in body["data"]["records"] if r["doc_number"] == "SE-9")
        self.assertEqual(row["match"]["bill"]["id"], str(bill.id))


class ReturnTests(GstFixture):
    def test_gstr3b_itc_follows_ims_and_set_off_order(self):
        self.upload()
        ids = {d["doc_number"]: str(d["_id"]) for d in gst.col().find()}
        self.call(gst.ims_action, "post", {"ids": [ids["OMS/0222"]], "action": "pending", "reason": "Query"})
        self.call(gst.ims_action, "post", {"ids": [ids["SE-9"]], "action": "reject", "reason": "Not ours"})
        self.invoice("INV-1", 100000, 18)                  # intra-state: 9000 + 9000
        self.invoice("INV-2", 50000, 18, pos="29")         # inter-state B2C, ≤ ₹1 lakh → B2CS, IGST 9000
        status, body = self.call(gst.returns, period="2026-10", kw={"form": "gstr3b"})
        self.assertEqual(status, 200, body)
        d = body["data"]
        # 2B ITC: OMS/0221 (1170+1170) less CN-4 (90+90); pending, rejected and RCM excluded.
        self.assertEqual(d["table_4"]["a5_all_other_itc"], {"igst": "0.00", "cgst": "1080.00", "sgst": "1080.00", "cess": "0.00"})
        self.assertEqual(d["table_4"]["a3_reverse_charge"]["cgst"], "450.00")
        self.assertEqual(d["table_3_1"][0]["igst"], "9000.00")
        self.assertEqual(d["table_3_1"][0]["cgst"], "9000.00")
        self.assertEqual(d["table_3_2"][0]["pos"], "29")
        self.assertEqual(d["ims_counts"]["pending"], 1)
        # Liability CGST 9000+450 RCM; ITC 1080 + 450 RCM credit.
        self.assertEqual(d["payment"]["cash"]["cgst"], "7920.00")

    def test_set_off_never_crosses_cgst_and_sgst(self):
        result = gst.set_off({"igst": Decimal(0), "cgst": Decimal(100), "sgst": Decimal(500), "cess": Decimal(0)},
                             {"igst": Decimal(0), "cgst": Decimal(400), "sgst": Decimal(0), "cess": Decimal(0)})
        self.assertEqual(result["cash"]["sgst"], "500.00")
        self.assertEqual(result["carry_forward"]["cgst"], "300.00")
        result = gst.set_off({"igst": Decimal(50), "cgst": Decimal(100), "sgst": Decimal(100), "cess": Decimal(0)},
                             {"igst": Decimal(120), "cgst": Decimal(0), "sgst": Decimal(0), "cess": Decimal(0)})
        self.assertEqual((result["cash"]["igst"], result["cash"]["cgst"], result["cash"]["sgst"]), ("0.00", "30.00", "100.00"))

    def test_rule37_reverses_old_unpaid_bills(self):
        self.bill("OLD-1", 10000, 1800, when=datetime(2026, 3, 1, 6))
        self.bill("OLD-PAID", 10000, 1800, when=datetime(2026, 3, 1, 6), paid=True)
        _, body = self.call(gst.returns, period="2026-10", kw={"form": "gstr3b"})
        self.assertEqual([b["number"] for b in body["data"]["rule37_bills"]], ["B-OLD-1"])
        self.assertEqual(body["data"]["table_4"]["b2_rule37_reversal"]["cgst"], "900.00")

    def test_gstr1_tables(self):
        self.invoice("INV-1", 100000, 18, gstin="29AAACB1234C1Z5", pos="29")  # B2B
        self.invoice("INV-2", 200000, 18, pos="29")                             # B2CL (inter-state, > ₹1 lakh)
        self.invoice("INV-3", 1000, 5)                                          # B2CS
        _, body = self.call(gst.returns, period="2026-10", kw={"form": "gstr1"})
        t = {x["label"]: x for x in body["data"]["tables"]}
        self.assertEqual(t["B2B invoices (registered buyers)"]["count"], 1)
        self.assertEqual(t["B2C large (inter-state, invoice above ₹1 lakh)"]["igst"], "36000.00")
        self.assertEqual(t["B2C others"]["cgst"], "25.00")
        self.assertEqual(body["data"]["documents"], {"from": "INV-1", "to": "INV-3", "issued": 3, "cancelled": 0})
        self.assertEqual({r["section"] for r in body["data"]["hsn"]}, {"B2B", "B2C"})
        status, response = self.call(gst.returns, period="2026-10", format="xlsx", kw={"form": "gstr1"})
        self.assertEqual(status, 200)

    def test_deadlines(self):
        monthly = {d["key"]: d["date"] for d in gst.deadlines("2026-10", {"frequency": "monthly", "state_code": "27"})}
        self.assertEqual((monthly["gstr1"], monthly["gstr3b"], monthly["gstr2b"]), ("2026-11-11", "2026-11-20", "2026-11-14"))
        self.assertEqual(monthly["sec16_4"], "2027-11-30")
        q = {d["key"]: d["date"] for d in gst.deadlines("2026-12", {"frequency": "quarterly", "state_code": "27"})}
        self.assertEqual(q["gstr3b"], "2027-01-22")
        q = {d["key"]: d["date"] for d in gst.deadlines("2026-12", {"frequency": "quarterly", "state_code": "07"})}
        self.assertEqual(q["gstr3b"], "2027-01-24")
        mid = {d["key"] for d in gst.deadlines("2026-11", {"frequency": "quarterly", "state_code": "07"})}
        self.assertIn("iff", mid)

    def test_overview_alerts(self):
        status, body = self.call(gst.overview, period="2026-10")
        self.assertEqual(status, 200, body)
        self.assertTrue(any("Upload this period" in a["text"] for a in body["data"]["alerts"]))

    def test_permissions(self):
        with patch("apps.business.gst_compliance.permitted", return_value=False):
            status, _ = self.call(gst.overview, period="2026-10")
        self.assertEqual(status, 403)
        with patch("apps.business.gst_compliance.permitted", side_effect=lambda r, c: c == "taxation.read"):
            status, _ = self.call(gst.ims_action, "post", {"ids": ["x"], "action": "accept"})
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
