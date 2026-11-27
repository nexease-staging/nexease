import bootstrap
import hashlib
import json
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.test import RequestFactory
from mongoengine.connection import get_db

from apps.accounts.models import User
from apps.business import einvoice, ewaybill
from apps.business.models import BusinessRecord
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.sales.models import CreditNote, CreditNoteItem, Customer, Invoice, InvoiceItem

OWN = "27AAACN1234F1Z5"
BUYER = "27AAPFU0939F1ZV"
DELHI = "07AABCS1429B1ZB"
SEZ = "27AABCS9999F1Z1"


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


def msg(body):
    return body.get("message") or (body.get("error") or {}).get("message", "")


class FakePortal:
    """Stands in for Sandbox's IRP and e-way bill APIs; records every request."""

    def __init__(self):
        self.calls = []
        self.fail = None
        self.ewb = 321000000000

    def __call__(self, base, path, headers, body=None, method=None):
        self.calls.append((method or ("POST" if body is not None else "GET"), path, body))
        if self.fail:
            return {"code": 200, "data": {"error": {"errorCodes": self.fail}, "status": "0", "info": ""}}
        if path.endswith("/e-invoice/tax-payer/invoice") and body:
            d = body["DocDtls"]
            start = int(d["Dt"][-4:]) - (int(d["Dt"][3:5]) < 4)
            irn = hashlib.sha256((body["SellerDtls"]["Gstin"] + f"{start}-{str(start + 1)[-2:]}" + d["Typ"] + d["No"]).encode()).hexdigest()
            data = {"Irn": irn, "SignedQRCode": "QR", "AckNo": "1123", "AckDt": "2026-11-27 10:00:00", "Status": "ACT"}
            if "EwbDtls" in body:
                self.ewb += 1
                data.update(EwbNo=self.ewb, EwbDt="27/11/2026 10:00:00 AM", EwbValidTill="28/11/2026 11:59:00 PM")
            return {"code": 200, "data": {"data": data}}
        if "/e-invoice/" in path and path.endswith("/cancel"):
            return {"code": 200, "data": {"Irn": body["Irn"], "CancelDate": "2026-11-27 12:00:00"}}
        if path.endswith("/consignor/bill") and body:
            self.ewb += 1
            return {"code": 200, "data": {"ewayBillNo": self.ewb, "ewayBillDate": "27/11/2026 10:00:00 AM", "validUpto": "28/11/2026 11:59:00 PM",
                                          "alert": "Distance between these two pincodes is 312"}}
        if path.endswith("/cancel"):
            return {"code": 200, "data": {"ewayBillNo": body["ewbNo"], "cancelDate": "27/11/2026 11:00:00 AM"}}
        if path.endswith("/vehicle"):
            return {"code": 200, "data": {"vehUpdDate": "27/11/2026 01:00:00 PM", "validUpto": "29/11/2026 11:59:00 PM"}}
        if path.endswith("/extend"):
            return {"code": 200, "data": {"ewayBillNo": body["ewbNo"], "updatedDate": "28/11/2026 10:00:00 PM", "validUpto": "30/11/2026 11:59:00 PM"}}
        if path.endswith("/consolidated-bill"):
            return {"code": 200, "data": {"cEwbNo": "4100000001", "cEwbDate": "27/11/2026 02:00:00 PM"}}
        raise AssertionError("unexpected call " + path)


class Fixture(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Ramesh Steel", email=uuid4().hex + "@example.com").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="A", last_name="B").save()
        self.portal = FakePortal()
        seller = {"gstin": OWN, "address": "Plot 4, MIDC Bhosari", "city": "Pune", "pincode": "411026", "credentials": "x"}
        for target, value in [
            ("apps.authorization.services.AuthorizationService.has_permission", True),
            ("apps.business.einvoice.has_einvoice", True), ("apps.business.ewaybill.has_einvoice", True),
            ("apps.saas.provider_guard.reserve_einvoice", None),
        ]:
            p = patch(target, return_value=value); p.start(); self.addCleanup(p.stop)
        for module in ("einvoice", "ewaybill"):
            p = patch(f"apps.business.{module}.session", return_value=("https://test", {}, seller)); p.start(); self.addCleanup(p.stop)
            p = patch(f"apps.business.{module}.call", side_effect=self.portal); p.start(); self.addCleanup(p.stop)
        BusinessRecord(organization=self.org, kind="gst_settings", key="registration", created_by=self.user,
                       data={"gstin": OWN, "state_code": "27", "legal_name": "Ramesh Steel Furniture", "registration": "regular"}).save()
        get_db().nexease_einvoice_settings.insert_one({"_id": f"{self.org.id}:test", "gstin": OWN, "credentials": "x", "address": "Plot 4", "city": "Pune", "pincode": "411026"})
        cat = Category(organization=self.org, name="Goods").save()
        self.product = Product(organization=self.org, sku="ALM", name="Steel almirah", category=cat, unit="PCS", hsn_code="9403").save()
        self.customer = Customer(organization=self.org, name="Patil Builders", code="C1").save()

    def invoice(self, number, taxable="10000", rate="18", gstin=BUYER, pos="27", when=None, country="India", issued_at=None):
        taxable = Decimal(taxable)
        tax = (taxable * Decimal(rate) / 100).quantize(Decimal("0.01"))
        when = when or datetime.utcnow() - timedelta(days=2)
        return Invoice(organization=self.org, customer=self.customer, invoice_number=number, status="ISSUED", invoice_date=when,
                       issued_at=issued_at or when, billing_name="Patil Builders Pvt Ltd", billing_address="Shivaji Nagar", billing_city="Pune",
                       billing_pincode="411005", billing_country=country, customer_gstin=gstin, created_by=self.user, subtotal=taxable,
                       discount_amount=0, total_amount=taxable + tax, tax_amount=tax, balance_due=taxable + tax,
                       billing_details={"supply_type": "taxable", "place_of_supply": pos, "supplier_state": "27", "supplier_gstin": OWN, "tax_reviewed": True},
                       items=[InvoiceItem(product=self.product, item_name="Steel almirah", quantity=1, unit_price=taxable, tax_rate=rate, line_subtotal=taxable,
                                          line_tax=tax, line_total=taxable + tax, hsn_code="9403", unit="PCS", item_type="goods")]).save()

    def call(self, view, verb="get", data=None, **params):
        factory = RequestFactory()
        request = factory.get("/", params) if verb == "get" else factory.post("/", json.dumps(data or {}), content_type="application/json")
        request.api_user, request.api_organization = self.user, self.org
        response = unwrap(view)(request)
        return response.status_code, json.loads(response.content)

    def irp(self, **data):
        return self.call(einvoice.einvoices, "post", {"confirm": True, **data})

    def ewb(self, **data):
        return self.call(ewaybill.eway_bills, "post", {"confirm": True, **data})

    def sent(self, suffix):
        return [b for m, p, b in self.portal.calls if p.endswith(suffix)]


class EInvoiceTests(Fixture):
    def test_b2b_invoice_and_credit_note(self):
        inv = self.invoice("INV-0101")
        status, body = self.irp(action="generate", id=str(inv.id))
        self.assertEqual(status, 200, body)
        self.assertEqual((body["data"]["status"], body["data"]["category"]), ("registered", "B2B"))
        doc = self.sent("/tax-payer/invoice")[0]
        self.assertEqual((doc["ValDtls"]["CgstVal"], doc["ValDtls"]["SgstVal"], doc["ValDtls"]["IgstVal"]), (900.0, 900.0, 0.0))

        cn = CreditNote(organization=self.org, credit_note_number="CN-0007", invoice=inv, customer=self.customer, status="ISSUED",
                        credit_note_date=datetime.utcnow(), created_by=self.user, subtotal=Decimal("2000"), tax_amount=Decimal("360"),
                        total_amount=Decimal("2360"), items=[CreditNoteItem(product=self.product, quantity=1, unit_price=Decimal("2000"), tax_rate=18,
                        discount=0, line_subtotal=Decimal("2000"), line_tax=Decimal("360"), line_total=Decimal("2360"))]).save(validate=False)
        status, body = self.call(einvoice.einvoices, kind="credit_note")
        self.assertEqual([r["number"] for r in body["data"]["records"]], ["CN-0007"])
        status, body = self.irp(action="generate", id=str(cn.id), kind="credit_note")
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["status"], "registered")
        doc = self.sent("/tax-payer/invoice")[-1]
        self.assertEqual(doc["DocDtls"]["Typ"], "CRN")
        self.assertEqual(doc["RefDtls"]["PrecDocDtls"][0]["InvNo"], "INV-0101")
        self.assertEqual(doc["TranDtls"]["SupTyp"], "B2B")
        cn.reload()
        self.assertEqual(cn.einvoice["status"], "registered")

    def test_export_without_payment_and_sez(self):
        exp = self.invoice("EXP-0001", rate="0", gstin="", country="United Arab Emirates")
        status, body = self.irp(action="generate", id=str(exp.id), category="EXPWOP")
        self.assertIn("destination country", msg(body))
        self.assertEqual(self.portal.calls, [], "nothing sent when validation fails")
        Invoice.objects(id=exp.id).update_one(unset__einvoice=True)
        status, body = self.irp(action="generate", id=str(exp.id), category="EXPWOP", export={"country": "ae", "currency": "AED", "port": "INNSA1"})
        self.assertEqual(status, 200, body)
        doc = self.sent("/tax-payer/invoice")[0]
        self.assertEqual((doc["BuyerDtls"]["Gstin"], doc["BuyerDtls"]["Pos"], doc["BuyerDtls"]["Stcd"], doc["BuyerDtls"]["Pin"]), ("URP", "96", "96", 999999))
        self.assertEqual(doc["ExpDtls"], {"CntCode": "AE", "ForCur": "AED", "Port": "INNSA1"})

        taxed = self.invoice("EXP-0002", rate="18", gstin="", country="UAE")
        status, body = self.irp(action="generate", id=str(taxed.id), category="EXPWOP", export={"country": "AE"})
        self.assertIn("must carry no GST", msg(body))

        sez = self.invoice("SEZ-0001", gstin=SEZ)
        status, body = self.irp(action="generate", id=str(sez.id), category="SEZWP")
        self.assertEqual(status, 200, body)
        doc = self.sent("/tax-payer/invoice")[-1]
        self.assertEqual((doc["ValDtls"]["IgstVal"], doc["ValDtls"]["CgstVal"], doc["TranDtls"]["IgstOnIntra"]), (1800.0, 0.0, "Y"))

    def test_thirty_day_window(self):
        old = self.invoice("INV-0090", when=datetime.utcnow() - timedelta(days=40))
        fresh = self.invoice("INV-0091", when=datetime.utcnow() - timedelta(days=27))
        _, body = self.call(einvoice.einvoices)
        rows = {r["number"]: r for r in body["data"]["records"]}
        self.assertLess(rows["INV-0090"]["days_left"], 0)
        self.assertIn(rows["INV-0091"]["days_left"], (2, 3, 4))
        self.assertEqual((body["data"]["summary"]["late"], body["data"]["summary"]["due_soon"]), (1, 1))
        self.assertFalse(rows["INV-0090"]["late"], "not flagged until the workspace says turnover is ₹10 crore+")
        status, body = self.irp(action="preferences", turnover_10cr=True)
        self.assertEqual(body["data"]["preferences"]["turnover_10cr"], True)
        status, body = self.irp(action="generate", id=str(old.id))
        self.assertIn("more than 30 days old", msg(body))
        self.assertEqual(self.portal.calls, [])
        status, body = self.irp(action="generate", id=str(fresh.id))
        self.assertEqual(status, 200, body)

    def test_bulk_generation_continues_past_failures(self):
        a, b = self.invoice("INV-0201"), self.invoice("INV-0202")
        bad = self.invoice("INV-0203")
        Invoice.objects(id=bad.id).update_one(set__items__0__hsn_code="12")
        status, body = self.irp(action="generate-bulk", ids=[str(a.id), str(bad.id), str(b.id)])
        self.assertEqual(status, 200, body)
        res = body["data"]["results"]
        self.assertEqual([r["ok"] for r in res], [True, False, True])
        self.assertIn("HSN", res[1]["message"])
        self.assertEqual(body["data"]["registered"], 2)
        status, body = self.irp(action="generate-bulk", ids=[str(a.id)] * 26)
        self.assertEqual(status, 400)

    def test_automatic_irn_only_after_switching_on(self):
        before = self.invoice("INV-0301", issued_at=datetime.utcnow() - timedelta(days=1))
        self.irp(action="preferences", auto_generate=True)
        after = self.invoice("INV-0302", issued_at=datetime.utcnow() + timedelta(seconds=5))
        broken = self.invoice("INV-0303", issued_at=datetime.utcnow() + timedelta(seconds=6))
        Invoice.objects(id=broken.id).update_one(set__items__0__hsn_code="1")
        with patch("apps.business.einvoice.environment", return_value="test"):
            for _ in range(3):
                einvoice.deliver_one()
        before.reload(); after.reload(); broken.reload()
        self.assertEqual(before.einvoice, {}, "invoices issued before auto IRN was switched on are left alone")
        self.assertEqual(after.einvoice["status"], "registered")
        parked = get_db().nexease_einvoice_auto.find_one({"_id": str(broken.id)})
        self.assertIn("HSN", parked["error"])
        self.assertEqual(len(self.sent("/tax-payer/invoice")), 1, "a parked invoice is not retried by the worker")
        _, body = self.call(einvoice.einvoices)
        row = next(r for r in body["data"]["records"] if r["number"] == "INV-0303")
        self.assertIn("HSN", row["auto_error"])


class EWayBillTests(Fixture):
    def challan(self, reason="job_work", when=None, number="DC-0001"):
        doc = {"_id": uuid4().hex, "organization_id": str(self.org.id), "status": "issued", "number": number,
               "date": (when or datetime.utcnow()).date().isoformat(), "reason": reason, "seller_gstin": OWN, "customer_gstin": BUYER,
               "pos": "27", "seller_name": "Ramesh Steel Furniture", "seller_address": "Plot 4, MIDC Bhosari", "customer_name": "Coat Works",
               "address": "Chakan MIDC", "items": [{"name": "CRCA sheet", "hsn": "7209", "qty": "40", "unit": "SHEET", "value": "46000",
                                                    "rate": "18", "cgst": "4140", "sgst": "4140", "igst": "0"}]}
        get_db().nexease_delivery_challans.insert_one(doc)
        return doc["_id"]

    def generate(self, cid, **extra):
        return self.ewb(action="generate", kind="challan", id=cid, mode="1", vehicle="MH12AB1234", destination_city="Chakan",
                        destination_pin="410501", **extra)

    def record(self, cid):
        return get_db().nexease_eway_bills.find_one({"source_id": cid})

    def test_generate_auto_distance_and_reasons(self):
        cid = self.challan("own_use")
        status, body = self.generate(cid, auto_distance=True)
        self.assertEqual(status, 200, body)
        sent = self.sent("/consignor/bill")[0]
        self.assertEqual((sent["transDistance"], sent["subSupplyType"], sent["toGstin"]), ("0", "5", OWN))
        self.assertEqual(sent["itemList"][0]["qtyUnit"], "SHT")
        self.assertEqual(self.record(cid)["distance"], 312)
        pr = self.challan("purchase_return", number="DC-0002")
        self.generate(pr, distance="40")
        self.assertEqual(self.sent("/consignor/bill")[-1]["subSupplyDesc"], "Purchase return")

    def test_document_older_than_180_days_is_blocked(self):
        cid = self.challan(when=datetime.utcnow() - timedelta(days=200))
        status, body = self.generate(cid, distance="40")
        self.assertIn("more than 180 days", msg(body))
        self.assertEqual(self.portal.calls, [])

    def test_cancel_within_24_hours_and_portal_errors(self):
        cid = self.challan()
        self.generate(cid, distance="40")
        number = self.record(cid)["number"]
        status, body = self.ewb(action="cancel", kind="challan", id=cid, reason="2", remarks="Order cancelled")
        self.assertEqual((status, body["data"]["status"]), (200, "cancelled"))
        self.assertEqual(self.sent(f"/bill/{number}/cancel")[0], {"ewbNo": int(number), "cancelRsnCode": 2, "cancelRmrk": "Order cancelled"})

        cid2 = self.challan(number="DC-0003")
        self.generate(cid2, distance="40")
        get_db().nexease_eway_bills.update_one({"source_id": cid2}, {"$set": {"generated_on": datetime.utcnow() - timedelta(hours=25)}})
        status, body = self.ewb(action="cancel", kind="challan", id=cid2, reason="2", remarks="Late")
        self.assertIn("within 24 hours", msg(body))
        get_db().nexease_eway_bills.update_one({"source_id": cid2}, {"$set": {"generated_on": datetime.utcnow()}})
        self.portal.fail = "316,"
        status, body = self.ewb(action="cancel", kind="challan", id=cid2, reason="2", remarks="Late")
        self.assertIn("verified by an officer", msg(body))
        self.assertEqual(self.record(cid2)["status"], "generated")

    def test_vehicle_update_and_extension_rules(self):
        cid = self.challan()
        self.generate(cid, distance="40")
        number = self.record(cid)["number"]
        status, body = self.ewb(action="vehicle", kind="challan", id=cid, mode="1", vehicle="MH14XY9876", from_place="Talegaon", reason="1")
        self.assertEqual(status, 200, body)
        method, path, sent = [c for c in self.portal.calls if c[1].endswith("/vehicle")][0]
        self.assertEqual((method, sent["vehicleNo"], sent["fromState"], sent["reasonCode"]), ("PUT", "MH14XY9876", 27, "1"))
        rec = self.record(cid)
        self.assertEqual((rec["vehicle"], rec["valid_until"]), ("MH14XY9876", "29/11/2026 11:59:00 PM"))

        status, body = self.ewb(action="extend", kind="challan", id=cid, mode="1", vehicle="MH14XY9876", from_place="Talegaon", from_pin="410507",
                                reason="5", remaining_distance="30")
        self.assertIn("opens on", msg(body))
        soon = (ewaybill.ist_now() + timedelta(hours=2)).strftime("%d/%m/%Y %I:%M:%S %p")
        get_db().nexease_eway_bills.update_one({"source_id": cid}, {"$set": {"valid_until": soon}})
        _, listing = self.call(ewaybill.eway_bills)
        self.assertTrue(next(r for r in listing["data"]["records"] if r["source_id"] == cid)["extendable"])
        status, body = self.ewb(action="extend", kind="challan", id=cid, mode="1", vehicle="MH14XY9876", from_place="Talegaon", from_pin="410507",
                                reason="5", remaining_distance="30")
        self.assertEqual(status, 200, body)
        self.assertEqual(self.sent(f"/bill/{number}/extend")[0]["remainingDistance"], 30)
        self.assertEqual(self.record(cid)["extensions"], 1)
        get_db().nexease_eway_bills.update_one({"source_id": cid}, {"$set": {"valid_until": soon}})
        status, body = self.ewb(action="extend", kind="challan", id=cid, consignment_status="T", transit_type="W", from_place="Talegaon",
                                from_pin="410507", reason="1", remaining_distance="30")
        self.assertEqual(status, 200, body)
        stored = self.sent(f"/bill/{number}/extend")[-1]
        self.assertEqual((stored["transMode"], stored["vehicleNo"], stored["transitType"]), ("5", "", "W"))
        get_db().nexease_eway_bills.update_one({"source_id": cid}, {"$set": {"generated_on": datetime.utcnow() - timedelta(days=361), "valid_until": soon}})
        status, body = self.ewb(action="extend", kind="challan", id=cid, mode="1", vehicle="MH14XY9876", from_place="Talegaon", from_pin="410507",
                                reason="5", remaining_distance="30")
        self.assertIn("360 days", msg(body))

    def test_consolidated_bill(self):
        a, b = self.challan(number="DC-0011"), self.challan(number="DC-0012")
        self.generate(a, distance="40"); self.generate(b, distance="40")
        numbers = [self.record(a)["number"], self.record(b)["number"]]
        status, body = self.ewb(action="consolidate", numbers=numbers + ["999999999999"], mode="1", vehicle="MH12AB1234", from_place="Pune")
        self.assertIn("999999999999", msg(body))
        status, body = self.ewb(action="consolidate", numbers=numbers, mode="1", vehicle="MH12AB1234", from_place="Pune")
        self.assertEqual((status, body["data"]["number"]), (200, "4100000001"))
        self.assertEqual(len(self.sent("/consolidated-bill")[0]["tripSheetEwbBills"]), 2)
        _, listing = self.call(ewaybill.eway_bills)
        self.assertEqual(listing["data"]["consolidated"][0]["bills"], sorted(numbers))


if __name__ == "__main__":
    unittest.main()
