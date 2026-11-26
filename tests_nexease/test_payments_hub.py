import bootstrap
import json
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.test import RequestFactory
from mongoengine.connection import get_db

from apps.accounts.models import User
from apps.business import payments_hub as hub
from apps.finance.models import BankAccount, BankTransaction, ChartOfAccount, JournalEntry
from apps.organizations.models import Organization
from apps.products.models import Category, Product
from apps.purchasing.models import Supplier, SupplierPayment, VendorBill, VendorBillItem
from apps.sales.models import CreditNote, Customer, CustomerPayment, Invoice, InvoiceItem


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


class HubFixture(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Pay org", email="p@example.com").save()
        self.other = Organization(name="Other org", email="o@example.com").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="A", last_name="B").save()
        patcher = patch("apps.authorization.services.AuthorizationService.has_permission", return_value=True)
        patcher.start(); self.addCleanup(patcher.stop)
        category = Category(organization=self.org, name="Goods").save()
        self.product = Product(organization=self.org, sku="P1", name="Cement", category=category, unit="BAG").save()
        self.bank = BankAccount(organization=self.org, account_name="Main cash", account_type="CASH", created_by=self.user).save()
        for code, kind, normal in (("ACCOUNTS_RECEIVABLE", "ASSET", "DEBIT"), ("CASH", "ASSET", "DEBIT"),
                                   ("ACCOUNTS_PAYABLE", "LIABILITY", "CREDIT")):
            ChartOfAccount(organization=self.org, account_code=code, account_name=code, system_key=code, is_system_account=True,
                           account_type=kind, normal_balance=normal, created_by=self.user).save()
        self.sharma = Customer(organization=self.org, name="Sharma Traders", code="C1", phone="9876543210").save()
        self.patil = Customer(organization=self.org, name="Patil Hardware", code="C2").save()
        self.omc = Supplier(organization=self.org, name="Om Cement Depot", code="S1").save()
        today = datetime.utcnow()
        self.old = self.invoice("INV-1", self.sharma, 1000, due=today - timedelta(days=45))
        self.new = self.invoice("INV-2", self.sharma, 500, due=today + timedelta(days=10))
        self.patil_inv = self.invoice("INV-3", self.patil, 300, due=today - timedelta(days=100))
        self.invoice("INV-D", self.sharma, 999, status="DRAFT")
        self.bill1 = self.bill("B-1", 800, due=today - timedelta(days=5))
        self.bill2 = self.bill("B-2", 200, due=today + timedelta(days=20))
        # Another organisation's documents must never appear.
        other_customer = Customer(organization=self.other, name="Sharma Traders", code="C1").save()
        Invoice(organization=self.other, customer=other_customer, invoice_number="X-1", status="ISSUED", invoice_date=today,
                billing_name="x", created_by=self.user, items=[InvoiceItem(product=self.product, quantity=1, unit_price=5000, line_total=5000)], total_amount=5000, balance_due=5000).save()

    def invoice(self, number, customer, amount, due=None, status="ISSUED"):
        return Invoice(organization=self.org, customer=customer, invoice_number=number, status=status,
                       invoice_date=datetime.utcnow() - timedelta(days=60), due_date=due, billing_name=customer.name,
                       created_by=self.user, items=[InvoiceItem(product=self.product, quantity=1, unit_price=amount, line_total=amount)],
                       total_amount=amount, balance_due=amount).save()

    def bill(self, number, amount, due=None):
        return VendorBill(organization=self.org, supplier=self.omc, bill_number=number, status="POSTED",
                          bill_date=datetime.utcnow() - timedelta(days=30), due_date=due, created_by=self.user,
                          items=[VendorBillItem(product=self.product, quantity=1, unit_price=amount, line_total=amount)],
                          total_amount=amount, balance_due=amount).save()

    def call(self, view, verb="get", data=None, **params):
        factory = RequestFactory()
        if verb == "get":
            request = factory.get("/", params)
        else:
            request = factory.post("/", data=json.dumps(data or {}), content_type="application/json")
        request.api_user, request.api_organization = self.user, self.org
        response = unwrap(view)(request)
        return response.status_code, json.loads(response.content)

    def receive(self, **body):
        payload = {"party_id": str(self.sharma.id), "payment_method": "CASH", "bank_account_id": str(self.bank.id),
                   "request_key": "receipt-key-000000001"}
        payload.update(body)
        return self.call(hub.receive, "post", payload)


class OutstandingTests(HubFixture):
    def test_party_summary_with_aging_and_overdue_first(self):
        status, body = self.call(hub.outstanding, side="receivable")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual(data["totals"]["outstanding"], "1800.00")
        self.assertEqual(data["totals"]["overdue"], "1300.00")
        self.assertEqual([p["name"] for p in data["parties"]], ["Sharma Traders", "Patil Hardware"])
        sharma = data["parties"][0]
        self.assertEqual((sharma["open_count"], sharma["outstanding"], sharma["overdue"]), (2, "1500.00", "1000.00"))
        self.assertEqual(sharma["buckets"]["d31_60"], "1000.00")
        self.assertEqual(sharma["buckets"]["current"], "500.00")
        self.assertEqual(sharma["phone"], "9876543210")
        self.assertEqual(data["parties"][1]["buckets"]["d90_plus"], "300.00")

    def test_credit_notes_reduce_outstanding(self):
        CreditNote(organization=self.org, credit_note_number="CN-1", invoice=self.old, customer=self.sharma, status="ISSUED",
                   credit_note_date=datetime.utcnow(), reason="Damaged", total_amount=200, applied_amount=200,
                   created_by=self.user).save(validate=False)
        status, body = self.call(hub.outstanding, side="receivable", party_id=str(self.sharma.id))
        self.assertEqual(status, 200)
        docs = body["data"]["documents"]
        self.assertEqual([d["number"] for d in docs], ["INV-1", "INV-2"])  # oldest due first
        self.assertEqual(docs[0]["outstanding"], "800.00")
        self.assertEqual(body["data"]["total"], "1300.00")

    def test_payables_and_search(self):
        status, body = self.call(hub.outstanding, side="payable", search="om cem")
        self.assertEqual(status, 200)
        self.assertEqual([p["name"] for p in body["data"]["parties"]], ["Om Cement Depot"])
        self.assertEqual(body["data"]["totals"]["outstanding"], "1000.00")
        self.assertEqual(body["data"]["totals"]["overdue"], "800.00")

    def test_other_organisation_party_is_not_found(self):
        stranger = Customer(organization=self.other, name="Z", code="Z").save()
        status, _ = self.call(hub.outstanding, side="receivable", party_id=str(stranger.id))
        self.assertEqual(status, 404)
        self.assertEqual(self.call(hub.outstanding, side="bogus")[0], 400)


class ReceiveTests(HubFixture):
    def test_auto_allocation_pays_oldest_first_with_real_accounting(self):
        status, body = self.receive(amount="1200")
        self.assertEqual(status, 200, body)
        parts = body["data"]["payments"]
        self.assertEqual([(p["number"], p["amount"]) for p in parts], [("INV-1", "1000.00"), ("INV-2", "200.00")])
        self.assertEqual(self.old.reload().status, "PAID")
        self.assertEqual((self.new.reload().status, self.new.balance_due), ("PARTIALLY_PAID", Decimal("300")))
        self.assertEqual(CustomerPayment.objects(organization=self.org).count(), 2)
        self.assertEqual(BankTransaction.objects(organization=self.org).count(), 2)
        self.assertEqual(JournalEntry.objects(organization=self.org, status="POSTED").count(), 2)
        self.assertEqual(self.bank.reload().current_balance, Decimal("1200"))

    def test_explicit_allocations_and_reference_suffix(self):
        status, body = self.receive(amount="700", reference_number="UTR99", allocations=[
            {"document_id": str(self.new.id), "amount": "500"}, {"document_id": str(self.old.id), "amount": "200"}])
        self.assertEqual(status, 200, body)
        refs = sorted(p.reference_number for p in CustomerPayment.objects(organization=self.org))
        self.assertEqual(refs, ["UTR99/1", "UTR99/2"])
        self.assertEqual(self.new.reload().status, "PAID")

    def test_validation_blocks_before_anything_is_written(self):
        cases = [
            ({"amount": "1600"}, "more than the total outstanding"),
            ({"amount": "100", "allocations": [{"document_id": str(self.old.id), "amount": "60"}]}, "add up to"),
            ({"amount": "1100", "allocations": [{"document_id": str(self.new.id), "amount": "1100"}]}, "more than its outstanding"),
            ({"amount": "300", "allocations": [{"document_id": str(self.patil_inv.id), "amount": "300"}]}, "not open for this party"),
            ({"amount": "10", "request_key": "short"}, "request_key"),
            ({"amount": "10.005"}, "two decimals"),
            ({"amount": "10", "payment_method": "GOLD"}, "payment method"),
        ]
        for body, message in cases:
            status, response = self.receive(**body)
            self.assertEqual(status, 400, (body, response))
            self.assertIn(message, response["error"]["message"])
        self.assertEqual(CustomerPayment.objects(organization=self.org).count(), 0)

    def test_retry_after_partial_failure_never_pays_twice(self):
        allocations = [{"document_id": str(self.old.id), "amount": "1000"}, {"document_id": str(self.new.id), "amount": "500"}]
        from apps.sales.services.invoice_api_service import InvoiceAPIService
        real = InvoiceAPIService.record_payment
        calls = {"n": 0}

        def flaky(**kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise ValueError("Bank is offline.")
            return real(**kwargs)

        with patch.object(InvoiceAPIService, "record_payment", side_effect=flaky):
            status, body = self.receive(amount="1500", allocations=allocations)
        self.assertEqual(status, 422)
        self.assertIn("Recorded 1 of 2", body["error"]["message"])
        self.assertEqual(body["error"]["details"]["recorded"][0]["number"], "INV-1")
        # Same request again: INV-1 replays, INV-2 is recorded now.
        status, body = self.receive(amount="1500", allocations=allocations)
        self.assertEqual(status, 200, body)
        self.assertEqual(CustomerPayment.objects(organization=self.org).count(), 2)
        self.assertEqual(self.bank.reload().current_balance, Decimal("1500"))
        self.assertEqual((self.old.reload().status, self.new.reload().status), ("PAID", "PAID"))

    def test_first_part_failure_is_a_plain_validation_error(self):
        from apps.sales.services.invoice_api_service import InvoiceAPIService
        with patch.object(InvoiceAPIService, "record_payment", side_effect=ValueError("Bank account is inactive.")):
            status, body = self.receive(amount="100")
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["message"], "Bank account is inactive.")


class PayTests(HubFixture):
    def test_pay_supplier_across_bills(self):
        status, body = self.call(hub.pay, "post", {"party_id": str(self.omc.id), "amount": "900", "payment_method": "UPI",
                                                   "bank_account_id": str(self.bank.id), "request_key": "supplier-key-00000001"})
        self.assertEqual(status, 200, body)
        self.assertEqual([p["number"] for p in body["data"]["payments"]], ["B-1", "B-2"])
        self.assertEqual(self.bill1.reload().status, "PAID")
        self.assertEqual(self.bill2.reload().balance_due, Decimal("100"))
        self.assertEqual(SupplierPayment.objects(organization=self.org).count(), 2)
        self.assertEqual(self.bank.reload().current_balance, Decimal("-900"))
        self.assertIn("2 bills", body["message"])


class RegisterTests(HubFixture):
    def setUp(self):
        super().setUp()
        self.receive(amount="1200")
        self.call(hub.pay, "post", {"party_id": str(self.omc.id), "amount": "300", "payment_method": "UPI",
                                    "bank_account_id": str(self.bank.id), "request_key": "supplier-key-00000002"})

    def test_merged_register_with_totals(self):
        status, body = self.call(hub.register)
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual(data["summary"]["money_in"], "1200.00")
        self.assertEqual(data["summary"]["money_out"], "300.00")
        self.assertEqual(data["summary"]["net"], "900.00")
        self.assertEqual(data["summary"]["count"], 3)
        self.assertEqual(data["summary"]["by_method"]["UPI"]["out"], "300.00")
        self.assertEqual({p["direction"] for p in data["payments"]}, {"in", "out"})
        row = next(p for p in data["payments"] if p["direction"] == "out")
        self.assertEqual((row["party"]["name"], row["account"]["name"], row["documents"][0]["number"]), ("Om Cement Depot", "Main cash", "B-1"))

    def test_filters_search_and_paging(self):
        _, body = self.call(hub.register, direction="in", search="sharma", page_size="1")
        data = body["data"]
        self.assertEqual((data["summary"]["count"], len(data["payments"]), data["pagination"]["pages"]), (2, 1, 2))
        self.assertEqual(data["summary"]["money_out"], "0.00")
        _, body = self.call(hub.register, method="UPI")
        self.assertEqual(body["data"]["summary"]["count"], 1)
        _, body = self.call(hub.register, to="2000-01-01")
        self.assertEqual(body["data"]["summary"]["count"], 0)
        self.assertEqual(self.call(hub.register, direction="sideways")[0], 400)
        self.assertEqual(self.call(hub.register, method="GOLD")[0], 400)

    def test_direction_respects_permissions(self):
        def allow(user, code):
            return code != "bills.read"
        with patch("apps.authorization.services.AuthorizationService.has_permission", side_effect=allow):
            _, body = self.call(hub.register)
            self.assertEqual(body["data"]["summary"]["money_out"], "0.00")
            self.assertEqual(self.call(hub.register, direction="out")[0], 403)


if __name__ == "__main__":
    unittest.main()
