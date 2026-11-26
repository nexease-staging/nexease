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
from apps.business import finance_hub as fh
from apps.finance.models import BankAccount, ChartOfAccount, JournalEntry, JournalLine
from apps.organizations.models import Organization


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


class FinanceFixture(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Books org", email="b@example.com").save()
        self.other = Organization(name="Other", email="o@example.com").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="A", last_name="B").save()
        patcher = patch("apps.authorization.services.AuthorizationService.has_permission", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.a = {}
        for code, name, kind, sub, key, normal in [
            ("1000", "Cash", "ASSET", "CURRENT_ASSET", "CASH", "DEBIT"), ("1010", "Bank", "ASSET", "CURRENT_ASSET", "BANK", "DEBIT"),
            ("1100", "Accounts receivable", "ASSET", "CURRENT_ASSET", "ACCOUNTS_RECEIVABLE", "DEBIT"), ("1500", "Machinery", "ASSET", "FIXED_ASSET", "", "DEBIT"),
            ("1200", "Input GST", "ASSET", "CURRENT_ASSET", "INPUT_TAX", "DEBIT"),
            ("2000", "Accounts payable", "LIABILITY", "CURRENT_LIABILITY", "ACCOUNTS_PAYABLE", "CREDIT"), ("2100", "Output GST", "LIABILITY", "CURRENT_LIABILITY", "OUTPUT_TAX", "CREDIT"),
            ("2500", "Term loan", "LIABILITY", "LONG_TERM_LIABILITY", "", "CREDIT"), ("3000", "Owner's capital", "EQUITY", "CAPITAL", "OWNERS_EQUITY", "CREDIT"),
            ("4000", "Sales", "REVENUE", "OPERATING_REVENUE", "SALES_REVENUE", "CREDIT"), ("4100", "Interest received", "REVENUE", "OTHER_REVENUE", "OTHER_INCOME", "CREDIT"),
            ("5000", "Cost of goods sold", "EXPENSE", "COST_OF_SALES", "COST_OF_GOODS_SOLD", "DEBIT"), ("6000", "Rent", "EXPENSE", "OPERATING_EXPENSE", "", "DEBIT"),
            ("6100", "Bank charges", "EXPENSE", "FINANCE_EXPENSE", "BANK_CHARGES", "DEBIT")]:
            self.a[code] = ChartOfAccount(organization=self.org, account_code=code, account_name=name, account_type=kind, account_subtype=sub, system_key=key or None,
                                          normal_balance=normal, created_by=self.user).save()
        n = [0]

        def j(day, lines, status="POSTED", org=None):
            n[0] += 1
            total = sum(Decimal(str(d)) for _, d, _ in lines)
            return JournalEntry(organization=org or self.org, journal_number=f"J{n[0]}", journal_date=datetime.fromisoformat(day + "T06:00:00"), description="t",
                                lines=[JournalLine(account=self.a[c], debit=Decimal(str(d)), credit=Decimal(str(cr))) for c, d, cr in lines],
                                total_debit=total, total_credit=total, status=status, created_by=self.user).save()
        self.j = j
        j("2026-04-01", [("1010", 500000, 0), ("3000", 0, 500000)])                     # capital
        j("2026-04-05", [("1500", 200000, 0), ("2500", 0, 200000)])                     # machine on loan
        j("2026-05-10", [("1100", 118000, 0), ("4000", 0, 100000), ("2100", 0, 18000)])  # sale
        j("2026-05-10", [("5000", 60000, 0), ("1010", 0, 60000)])                       # cost of sale
        j("2026-06-01", [("6000", 20000, 0), ("1000", 0, 20000)])                       # rent
        j("2026-06-15", [("1010", 1000, 0), ("4100", 0, 1000)])                         # interest
        j("2026-06-30", [("6100", 500, 0), ("1010", 0, 500)])                           # bank charges
        j("2026-03-15", [("1100", 59000, 0), ("4000", 0, 50000), ("2100", 0, 9000)])    # previous year sale
        j("2026-06-20", [("6000", 99999, 0), ("1000", 0, 99999)], status="DRAFT")      # draft: excluded
        j("2026-05-01", [("1010", 777777, 0), ("4000", 0, 777777)], org=self.other)     # other org: excluded

    def call(self, view, kind=None, **params):
        request = RequestFactory().get("/", params)
        request.api_user, request.api_organization = self.user, self.org
        response = unwrap(view)(request, kind) if kind else unwrap(view)(request)
        try:
            return response.status_code, json.loads(response.content)
        except ValueError:
            return response.status_code, response


class StatementTests(FinanceFixture):
    def test_profit_and_loss_sections_and_comparison(self):
        status, body = self.call(fh.statement, "profit-and-loss", **{"from": "2026-04-01", "to": "2026-06-30"})
        self.assertEqual(status, 200, body)
        t = body["data"]["totals"]
        self.assertEqual((t["revenue"], t["cost_of_sales"], t["gross_profit"], t["operating_expenses"], t["other_income"], t["other_expenses"], t["net_profit"]),
                         ("100000.00", "60000.00", "40000.00", "20000.00", "1000.00", "500.00", "20500.00"))
        revenue = next(s for s in body["data"]["sections"] if s["key"] == "revenue")
        self.assertEqual(revenue["rows"][0]["name"], "Sales")
        self.assertEqual(revenue["percent"], "100.0")
        self.assertEqual(body["data"]["previous_period"], {"from": "2026-01-01", "to": "2026-03-31"})
        self.assertEqual(revenue["previous"], "50000.00")

    def test_balance_sheet_balances_with_profit_to_date(self):
        status, body = self.call(fh.statement, "balance-sheet", to="2026-06-30")
        d = body["data"]
        self.assertTrue(d["balanced"], d["totals"])
        t = d["totals"]
        # Assets: cash -20000, bank 440500, AR 177000, machine 200000 = 797500
        self.assertEqual((t["current_assets"], t["non_current_assets"], t["assets"]), ("597500.00", "200000.00", "797500.00"))
        self.assertEqual((t["current_liabilities"], t["non_current_liabilities"]), ("27000.00", "200000.00"))
        self.assertEqual(t["profit_to_date"], "70500.00")
        equity = next(s for s in d["sections"] if s["key"] == "equity")
        self.assertIn("Profit / (loss) to date (not yet closed)", [r["name"] for r in equity["rows"]])

    def test_exports(self):
        status, response = self.call(fh.statement, "profit-and-loss", format="xlsx", to="2026-06-30")
        self.assertEqual(status, 200)
        status, response = self.call(fh.statement, "balance-sheet", format="xlsx", to="2026-06-30")
        self.assertEqual(status, 200)
        self.assertEqual(self.call(fh.statement, "cash", to="2026-06-30")[0], 404)


class OverviewTests(FinanceFixture):
    def test_overview_figures_trend_and_alerts(self):
        BankAccount(organization=self.org, account_name="HDFC current", account_type="BANK", bank_name="HDFC", account_number="50200012345678", current_balance=440500, created_by=self.user).save()
        status, body = self.call(fh.overview, **{"from": "2026-04-01", "to": "2026-06-30"})
        self.assertEqual(status, 200, body)
        d = body["data"]
        self.assertEqual((d["cash_bank"], d["receivable"], d["payable"]), ("420500.00", "177000.00", "0.00"))
        self.assertEqual(d["gst_position"], "27000.00")
        self.assertEqual((d["income"], d["expenses"], d["net_profit"]), ("101000.00", "80500.00", "20500.00"))
        self.assertEqual(d["ratios"]["gross_margin"], "40.0")
        self.assertEqual(len(d["trend"]), 12)
        may = next(x for x in d["trend"] if x["period"] == "2026-05")
        self.assertEqual((may["income"], may["expense"]), ("100000.00", "60000.00"))
        self.assertEqual(d["top_expenses"][0]["name"], "Cost of goods sold")
        self.assertEqual(d["bank_accounts"][0]["number"], "5678")
        self.assertTrue(any("drafts" in a["text"] for a in d["alerts"]))
        self.assertFalse(any("negative" in a["text"] for a in d["alerts"]))
        self.assertEqual(d["previous"], {"from": "2026-01-01", "to": "2026-03-31"})

    def test_validation_and_permission(self):
        self.assertEqual(self.call(fh.overview, **{"from": "2026-07-01", "to": "2026-06-30"})[0], 400)
        self.assertEqual(self.call(fh.overview, to="30-06-2026")[0], 400)
        with patch("apps.business.finance_hub.permitted", return_value=False):
            self.assertEqual(self.call(fh.overview)[0], 403)


if __name__ == "__main__":
    unittest.main()
