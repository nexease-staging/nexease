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
from apps.business import tally_api, tally_sync as ts, tally_xml as tx
from apps.business.models import BusinessRecord
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.sales.models import Customer, CustomerPayment, Invoice, InvoiceItem, PaymentAllocation
from apps.purchasing.models import Supplier

from fake_tally import FakeTally

MAPPING = {"sales": "Sales GST", "purchase": "Purchase GST", "cgst_out": "Output CGST", "sgst_out": "Output SGST", "igst_out": "Output IGST",
           "cgst_in": "Input CGST", "sgst_in": "Input SGST", "igst_in": "Input IGST", "round_off": "Round Off", "cash": "Cash", "bank": "HDFC Bank",
           "expense_default": "Office Expenses"}


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


class TallyFixture(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Sharma Traders", email="s@example.com").save()
        self.org_id = str(self.org.id)
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="A", last_name="B").save()
        for p in (patch("apps.authorization.services.AuthorizationService.has_permission", return_value=True), patch.object(tally_api, "is_admin", return_value=True),
                  patch.object(ts, "PROBE_SECONDS", -1)):
            p.start()
            self.addCleanup(p.stop)
        self.tally = FakeTally()
        t = self.tally
        self.acme = t.add("ledger", "Acme Retail", parent="Sundry Debtors", gstin="27AAACA1111A1Z1", phone="9876500001", state="Maharashtra", address="12 MG Road\nPune")
        t.add("ledger", "Mumbai Mart", parent="Mumbai Debtors")
        t.add("ledger", "Om Steel", parent="Sundry Creditors", gstin="27AAPFU0939F1ZV")
        t.add("stockitem", "Steel Rod 12mm", unit="Nos", hsn="7214", qty=40, value=24000)
        t.voucher("GST Sales", "T-1", "2026-11-02", "Acme Retail", [("Acme Retail", Decimal("-1180")), ("Sales GST", Decimal("1000")),
                                                                    ("Output CGST", Decimal("90")), ("Output SGST", Decimal("90"))],
                  bills=[{"ledger": "Acme Retail", "name": "T-1", "type": "New Ref", "amount": Decimal("-1180")}])
        t.voucher("Receipt", "R-1", "2026-11-05", "Acme Retail", [("HDFC Bank", Decimal("-500")), ("Acme Retail", Decimal("500"))],
                  bills=[{"ledger": "Acme Retail", "name": "T-1", "type": "Agst Ref", "amount": Decimal("500")}])

    def cycle(self, rounds=10):
        """What the connector does: poll, post each job to Tally, return Tally's reply."""
        for _ in range(rounds):
            jobs = ts.next_jobs(self.org_id, limit=20)
            real = [j for j in jobs if j["type"] != "companies"]
            for j in jobs:
                result = ts.complete(self.org_id, j["id"], {"ok": True, "body": self.tally.handle(j["xml"])})
                self.assertNotEqual(result["status"], "failed", result)
            if not real and _ > 1:
                break

    def call(self, view, verb="get", data=None, **params):
        kwargs = params.pop("kw", {})
        factory = RequestFactory()
        request = factory.get("/", params) if verb == "get" else factory.post("/", data=json.dumps(data or {}), content_type="application/json")
        request.api_user, request.api_organization = self.user, self.org
        response = unwrap(view)(request, **kwargs)
        return response.status_code, json.loads(response.content)

    def connect(self):
        self.cycle()
        ts.save_settings(self.org_id, {"mapping": MAPPING, "push_from": datetime(2020, 1, 1)})


class XmlTests(unittest.TestCase):
    def test_amount_signs_and_control_characters(self):
        self.assertEqual(tx.amount("-1180.00"), Decimal("1180.00"))
        self.assertEqual(tx.amount("500.00 Cr"), Decimal("-500.00"))
        rows = tx.parse_objects("<ENVELOPE><LEDGER NAME='A'><PARENT>&#4; Primary</PARENT><ALTERID TYPE='Number'> 7</ALTERID></LEDGER></ENVELOPE>", "LEDGER")
        self.assertEqual(tx.normalise("ledger", rows[0])["alter_id"], 7)

    def test_voucher_import_is_balanced_and_escaped(self):
        v = {"remote_id": "NX-INV-1", "voucher_type": "Sales", "date": "2026-11-02", "number": "A&B/1", "party": "R & Sons",
             "lines": [{"ledger": "R & Sons", "amount": "118", "party": True}, {"ledger": "Sales", "amount": "-100"}, {"ledger": "IGST", "amount": "-18"}]}
        self.assertTrue(tx.balanced(v))
        xml = tx.voucher_xml("Co", v)
        self.assertIn("R &amp; Sons", xml)
        self.assertIn("<AMOUNT>-118.00</AMOUNT>", xml)

    def test_refused_request_raises(self):
        with self.assertRaises(ValueError):
            tx.parse_objects("<ENVELOPE><HEADER><STATUS>0</STATUS></HEADER><BODY><DATA><LINEERROR>Could not find Company</LINEERROR></DATA></BODY></ENVELOPE>", "LEDGER")


class PullTests(TallyFixture):
    def test_full_pull_mirrors_tally_and_creates_parties_and_items(self):
        self.cycle()
        company = ts.active_company(self.org_id)
        self.assertEqual(company["name"], "Sharma Traders")
        self.assertEqual(company["cursors"]["voucher"], self.tally.alt_vch)
        objs = get_db().tally_objects
        self.assertEqual(objs.count_documents({"kind": "voucher"}), 2)
        self.assertEqual(objs.count_documents({"kind": "ledger"}), 15)
        acme = Customer.objects(organization=self.org, name="Acme Retail").first()
        self.assertEqual((acme.gstin, acme.phone, acme.state), ("27AAACA1111A1Z1", "9876500001", "Maharashtra"))
        self.assertTrue(Customer.objects(organization=self.org, name="Mumbai Mart").first(), "sub-group of Sundry Debtors")
        self.assertTrue(Supplier.objects(organization=self.org, name="Om Steel").first())
        rod = Product.objects(organization=self.org, name="Steel Rod 12mm").first()
        self.assertEqual((rod.hsn_code, rod.unit), ("7214", "Nos"))

    def test_existing_nexease_party_is_matched_not_duplicated(self):
        Customer(organization=self.org, name="Acme Retail", code="C-1", phone="111").save()
        self.cycle()
        self.assertEqual(Customer.objects(organization=self.org, name="Acme Retail").count(), 1)
        self.assertEqual(Customer.objects(organization=self.org, name="Acme Retail").first().phone, "9876500001")

    def test_tally_edit_flows_in_without_echo_back(self):
        self.connect()
        self.acme["fields"]["phone"] = "9000000000"
        self.tally.touch(self.acme, "ledger")
        before = len(self.tally.requests)
        self.cycle()
        self.assertEqual(Customer.objects(organization=self.org, name="Acme Retail").first().phone, "9000000000")
        imports = [r for r in self.tally.requests[before:] if "Import Data" in r]
        self.assertEqual(imports, [], "a change from Tally must not be pushed back")

    def test_deleted_in_tally_is_marked_and_party_deactivated(self):
        self.cycle()
        self.tally.delete("ledger", "Mumbai Mart")
        get_db().tally_companies.update_many({}, {"$set": {"index_at": None}})
        self.cycle()
        self.assertTrue(get_db().tally_objects.find_one({"name": "Mumbai Mart"})["deleted"])
        self.assertFalse(Customer.objects(organization=self.org, name="Mumbai Mart").first().is_active)


class PushTests(TallyFixture):
    def invoice(self, customer, number="INV-9", qty=2, status="ISSUED"):
        cat = Category.objects(organization=self.org).first() or Category(organization=self.org, name="Goods").save()
        rod = Product.objects(organization=self.org, name="Steel Rod 12mm").first() or Product(organization=self.org, sku="R1", name="Steel Rod 12mm", category=cat, unit="Nos").save()
        taxable = Decimal(600) * qty
        tax = (taxable * Decimal("0.18")).quantize(Decimal("0.01"))
        return Invoice(organization=self.org, customer=customer, invoice_number=number, status=status, invoice_date=datetime(2026, 11, 20, 6), billing_name=customer.name,
                       created_by=self.user, subtotal=taxable, tax_amount=tax, total_amount=taxable + tax, balance_due=taxable + tax,
                       billing_details={"supply_type": "taxable", "place_of_supply": "27", "supplier_state": "27", "tax_reviewed": True},
                       items=[InvoiceItem(product=rod, quantity=qty, unit_price=600, tax_rate=18, line_subtotal=taxable, line_tax=tax, line_total=taxable + tax, hsn_code="7214")]).save()

    def test_new_customer_and_invoice_reach_tally_and_edits_alter_same_voucher(self):
        self.connect()
        buyer = Customer(organization=self.org, name="New Buyer", code="C-77", gstin="27AAACB2222B1Z2", state="Maharashtra").save()
        inv = self.invoice(buyer)
        self.cycle()
        led = self.tally.by_name("ledger", "New Buyer")
        self.assertEqual(led["fields"]["parent"], "Sundry Debtors")
        v = self.tally.objects["voucher"][f"NX-INV-{inv.id}"]
        self.assertEqual(v["fields"]["vtype"], "Sales")
        self.assertEqual(self.tally.closing("New Buyer"), Decimal("-1416.00"))
        self.assertEqual(self.tally.closing("Output CGST"), Decimal("198.00"))
        self.assertEqual(v["fields"]["inventory"][0]["item"], "Steel Rod 12mm")
        # The pushed voucher comes back on the next pull: tagged as NexEase's, not a new entry
        mirrored = get_db().tally_objects.find_one({"kind": "voucher", "guid": f"NX-INV-{inv.id}"})
        self.assertEqual(mirrored["from_nexease"], f"NX-INV-{inv.id}")
        count = len(self.tally.objects["voucher"])
        inv.items[0].quantity, inv.items[0].line_subtotal, inv.items[0].line_tax = 3, Decimal(1800), Decimal(324)
        inv.subtotal, inv.tax_amount, inv.total_amount = Decimal(1800), Decimal(324), Decimal(2124)
        inv.save()
        self.cycle()
        self.assertEqual(len(self.tally.objects["voucher"]), count)
        self.assertEqual(self.tally.closing("New Buyer"), Decimal("-2124.00"))
        inv.status = "CANCELLED"
        inv.save()
        self.cycle()
        self.assertTrue(self.tally.objects["voucher"][f"NX-INV-{inv.id}"]["fields"]["cancelled"])
        self.assertEqual(self.tally.closing("New Buyer"), Decimal("0"))

    def test_receipt_settles_tally_bill(self):
        self.connect()
        acme = Customer.objects(organization=self.org, name="Acme Retail").first()
        inv = self.invoice(acme, "INV-10", qty=1)
        self.cycle()
        pay = CustomerPayment(organization=self.org, customer=acme, payment_number="PAY-1", payment_date=datetime(2026, 11, 21, 6), amount=Decimal(708),
                              payment_method="UPI", allocations=[PaymentAllocation(invoice=inv, amount=Decimal(708))], created_by=self.user).save()
        self.cycle()
        v = self.tally.objects["voucher"][f"NX-RCPT-{pay.id}"]
        self.assertEqual(v["fields"]["vtype"], "Receipt")
        self.assertEqual(v["fields"]["bills"][0], {"ledger": "Acme Retail", "name": "INV-10", "type": "Agst Ref", "amount": Decimal("708.00")})
        self.assertEqual(self.tally.closing("HDFC Bank"), Decimal("-1208.00"))

    def test_missing_mapping_blocks_then_retries(self):
        self.cycle()
        ts.save_settings(self.org_id, {"push_from": datetime(2020, 1, 1)})
        acme = Customer.objects(organization=self.org, name="Acme Retail").first()
        inv = self.invoice(acme, "INV-11", qty=1)
        self.cycle()
        status, body = self.call(tally_api.issues)
        self.assertEqual(body["data"]["issues"][0]["state"], "blocked")
        self.assertIn("ledger", body["data"]["issues"][0]["error"])
        self.call(tally_api.sync_settings, "post", {"mapping": MAPPING})
        self.cycle()
        self.assertIn(f"NX-INV-{inv.id}", self.tally.objects["voucher"])

    def test_expense_becomes_payment_voucher(self):
        self.connect()
        rec = BusinessRecord(organization=self.org, kind="expenses", key="EXP-1", created_by=self.user,
                             data={"date": "2026-11-22", "category": "Office", "amount": "250", "payment_mode": "Cash", "payee": "Stationery"}).save()
        self.cycle()
        v = self.tally.objects["voucher"][f"NX-EXP-{rec.id}"]
        self.assertEqual(v["fields"]["lines"], [("Office Expenses", Decimal("-250.00")), ("Cash", Decimal("250.00"))])

    def test_switching_off_write_back_stops_push(self):
        self.connect()
        ts.save_settings(self.org_id, {"write_back": {k: False for k in ts.WRITE_KINDS}})
        Customer(organization=self.org, name="Quiet Buyer", code="C-88").save()
        self.cycle()
        self.assertIsNone(self.tally.by_name("ledger", "Quiet Buyer"))

    def test_tally_error_is_reported_as_issue(self):
        self.connect()
        ts.save_settings(self.org_id, {"debtors_group": "Wrong Group"})
        Customer(organization=self.org, name="Err Buyer", code="C-99").save()
        jobs = []
        for _ in range(4):
            for j in ts.next_jobs(self.org_id, limit=20):
                jobs.append(ts.complete(self.org_id, j["id"], {"ok": True, "body": self.tally.handle(j["xml"])}))
        self.assertTrue(any(r["status"] == "failed" and "Group" in r.get("error", "") for r in jobs))
        status, body = self.call(tally_api.issues)
        self.assertEqual(body["data"]["issues"][0]["state"], "error")


class ViewTests(TallyFixture):
    def test_overview_parties_statement_daybook_trial_balance(self):
        self.cycle()
        status, body = self.call(tally_api.overview)
        data = body["data"]
        self.assertEqual(data["receivable"], 680.0)
        self.assertEqual(data["bank"], 500.0)
        status, body = self.call(tally_api.parties, side="debtors")
        acme = next(p for p in body["data"]["parties"] if p["name"] == "Acme Retail")
        self.assertEqual(acme["balance"], 680.0)
        self.assertTrue(acme["nexease_id"])
        status, body = self.call(tally_api.party_detail, kw={"guid": acme["guid"]}, **{"from": "2026-04-01", "to": "2026-12-31"})
        self.assertEqual([r["balance"] for r in body["data"]["rows"]], [1180.0, 680.0])
        self.assertEqual(body["data"]["bills"][0]["amount"], 680.0)
        status, body = self.call(tally_api.daybook, **{"from": "2026-11-01", "to": "2026-11-30"})
        self.assertEqual([v["base"] for v in body["data"]["vouchers"]], ["Sales", "Receipt"])
        status, body = self.call(tally_api.registers, type="Sales", **{"from": "2026-04-01", "to": "2027-03-31"})
        self.assertEqual(body["data"]["total"], 1180.0)
        status, body = self.call(tally_api.trial_balance)
        self.assertEqual(body["data"]["difference"], 0.0)
        status, body = self.call(tally_api.stock)
        self.assertEqual(body["data"]["items"][0]["qty"], 40.0)
        status, body = self.call(tally_api.status)
        self.assertEqual(body["data"]["companies"][0]["progress"], 100)

    def test_settings_suggests_mapping(self):
        self.cycle()
        status, body = self.call(tally_api.sync_settings)
        s = body["data"]["options"]["suggested"]
        self.assertEqual((s["sales"], s["cgst_out"], s["igst_in"], s["bank"], s["cash"]), ("Sales GST", "Output CGST", "Input IGST", "HDFC Bank", "Cash"))


class AgentTests(TallyFixture):
    def post(self, view, data, token=None, **kw):
        request = RequestFactory().post("/", data=json.dumps(data), content_type="application/json", **({"HTTP_X_NEXEASE_DEVICE": token} if token else {}))
        response = view(request, **kw)
        return response.status_code, json.loads(response.content)

    def test_pair_poll_and_reply(self):
        status, body = self.call(tally_api.pairing, "post")
        code = body["data"]["code"]
        status, body = self.post(tally_api.agent_pair, {"code": code, "name": "Accounts PC"})
        self.assertEqual(status, 200)
        token = body["token"]
        self.assertEqual(self.post(tally_api.agent_pair, {"code": code})[0], 400, "a code works once")
        self.assertEqual(self.post(tally_api.agent_poll, {"info": {"tally_ok": True}})[0], 401)
        status, body = self.post(tally_api.agent_poll, {"info": {"tally_ok": True, "version": "1.0"}}, token)
        job = body["jobs"][0]
        self.assertEqual(job["type"], "companies")
        status, body = self.post(tally_api.agent_job, {"ok": True, "body": self.tally.handle(job["xml"])}, token, job_id=job["id"])
        self.assertEqual(body["status"], "done")
        self.assertEqual(ts.active_company(self.org_id)["name"], "Sharma Traders")
        status, body = self.post(tally_api.agent_poll, {"info": {"tally_ok": False, "error": "Tally closed"}}, token)
        self.assertEqual(body["jobs"], [])
        status, body = self.call(tally_api.revoke_device, "post", kw={"device_id": ts.db().tally_devices.find_one()["_id"]})
        self.assertEqual(self.post(tally_api.agent_poll, {"info": {"tally_ok": True}}, token)[0], 401)


if __name__ == "__main__":
    unittest.main()
