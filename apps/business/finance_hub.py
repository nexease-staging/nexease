"""Finance overview and detailed financial statements, built from posted journals.

Every figure comes from POSTED journal lines (REVERSED originals are kept together with their
reversal entries so they net to zero, as the trial balance does). Nothing here writes data.

- Overview: cash and bank, receivables, payables, GST position, income / expenses / net profit for
  a period against the previous one, a 12-month trend, top expenses, ratios and book-keeping alerts.
- Profit & loss: revenue, cost of sales, gross profit, operating expenses, other income, finance
  and other expenses, net profit, account by account, with a comparison period and % of revenue.
- Balance sheet: current and non-current assets and liabilities, equity with profit to date, and a
  check that assets equal liabilities plus equity, with a comparison date.
"""
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.views.decorators.http import require_http_methods

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.finance.models import BankAccount, BankTransaction, ChartOfAccount, JournalEntry

from .views import permitted, workbook_response

D0 = Decimal(0)
CENT = Decimal("0.01")
IST = timedelta(hours=5, minutes=30)
STATUSES = ("POSTED", "REVERSED")


def money(value):
    return f"{Decimal(value).quantize(CENT):.2f}"


def today_ist():
    return (datetime.utcnow() + IST).date()


def fy_start(day):
    return date(day.year if day.month >= 4 else day.year - 1, 4, 1)


def parse(value, default):
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("Dates must look like 2026-04-01.")


def utc(day, end=False):
    return datetime.combine(day + timedelta(days=1) if end else day, time.min) - IST


def previous_period(start, end):
    """The period just before: whole months when the period is whole months, else the same number of days."""
    next_day = end + timedelta(days=1)
    if start.day == 1 and next_day.day == 1:
        months = (next_day.year - start.year) * 12 + next_day.month - start.month
        y, m = start.year, start.month - months
        while m < 1:
            y, m = y - 1, m + 12
        return date(y, m, 1), start - timedelta(days=1)
    length = (end - start).days + 1
    return start - timedelta(days=length), start - timedelta(days=1)


def accounts(org):
    return {a.id: {"id": str(a.id), "code": a.account_code, "name": a.account_name, "type": a.account_type, "subtype": a.account_subtype or "",
                   "key": a.system_key or "", "normal": a.normal_balance or ("DEBIT" if a.account_type in ("ASSET", "EXPENSE") else "CREDIT")}
            for a in ChartOfAccount.objects(organization=org)}


def journal_lines(org, start=None, end=None):
    """(journal date, account id, debit, credit) for posted journals between two IST dates (inclusive)."""
    query = {"organization": org, "status__in": STATUSES}
    if start:
        query["journal_date__gte"] = utc(start)
    if end:
        query["journal_date__lt"] = utc(end, end=True)
    for j in JournalEntry.objects(**query).only("journal_date", "lines").as_pymongo():
        day = (j["journal_date"] + IST).date() if j.get("journal_date") else None
        for line in j.get("lines", []):
            yield day, line.get("account"), Decimal(str(line.get("debit") or 0)), Decimal(str(line.get("credit") or 0))


def totals(org, start=None, end=None):
    sums = defaultdict(lambda: [D0, D0])
    for _, account, dr, cr in journal_lines(org, start, end):
        sums[account][0] += dr
        sums[account][1] += cr
    return sums


def balance(acc, dr, cr):
    return dr - cr if acc["normal"] == "DEBIT" else cr - dr


# --------------------------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------------------------

PL_SECTIONS = [
    ("revenue", "Revenue from operations", "REVENUE"),
    ("cost_of_sales", "Cost of sales", "EXPENSE"),
    ("operating_expenses", "Operating expenses", "EXPENSE"),
    ("other_income", "Other income", "REVENUE"),
    ("other_expenses", "Finance and other expenses", "EXPENSE"),
]


def pl_section(acc):
    if acc["type"] == "REVENUE":
        return "other_income" if acc["subtype"] == "OTHER_REVENUE" or acc["key"] == "OTHER_INCOME" else "revenue"
    if acc["type"] == "EXPENSE":
        if acc["subtype"] == "COST_OF_SALES" or acc["key"] in ("COST_OF_GOODS_SOLD", "PURCHASE_EXPENSE"):
            return "cost_of_sales"
        if acc["subtype"] in ("FINANCE_EXPENSE", "OTHER_EXPENSE") or acc["key"] in ("BANK_CHARGES", "OTHER_EXPENSE"):
            return "other_expenses"
        return "operating_expenses"
    return None


def bs_section(acc):
    sub = acc["subtype"]
    if acc["type"] == "ASSET":
        return "current_assets" if sub in ("", "CURRENT_ASSET", "CASH", "BANK", "RECEIVABLE", "INVENTORY") or sub.startswith("CURRENT") else "non_current_assets"
    if acc["type"] == "LIABILITY":
        return "current_liabilities" if sub in ("", "CURRENT_LIABILITY", "PAYABLE", "TAX") or sub.startswith("CURRENT") else "non_current_liabilities"
    if acc["type"] == "EQUITY":
        return "equity"
    return None


BS_SECTIONS = [
    ("current_assets", "Current assets", "assets"),
    ("non_current_assets", "Fixed and other non-current assets", "assets"),
    ("current_liabilities", "Current liabilities", "liabilities"),
    ("non_current_liabilities", "Long-term liabilities", "liabilities"),
    ("equity", "Capital and reserves", "equity"),
]


# --------------------------------------------------------------------------------------------
# Statements
# --------------------------------------------------------------------------------------------

def pl_numbers(accs, sums):
    sections = {key: {} for key, _, _ in PL_SECTIONS}
    for aid, (dr, cr) in sums.items():
        acc = accs.get(aid)
        if not acc:
            continue
        section = pl_section(acc)
        if section:
            # Revenue is a credit balance; expenses are debits. Show both as positive amounts.
            sections[section][aid] = cr - dr if acc["type"] == "REVENUE" else dr - cr
    t = {key: sum(rows.values(), D0) for key, rows in sections.items()}
    t["gross_profit"] = t["revenue"] - t["cost_of_sales"]
    t["operating_profit"] = t["gross_profit"] - t["operating_expenses"]
    t["net_profit"] = t["operating_profit"] + t["other_income"] - t["other_expenses"]
    return sections, t


def profit_and_loss(org, start, end, compare=True):
    accs = accounts(org)
    sections, t = pl_numbers(accs, totals(org, start, end))
    prev_sections, pt = {}, {}
    prev = None
    if compare:
        prev = previous_period(start, end)
        prev_sections, pt = pl_numbers(accs, totals(org, *prev))
    revenue = t["revenue"] or None

    def pct(v):
        return f"{(v / revenue * 100):.1f}" if revenue else None

    out = []
    for key, label, _ in PL_SECTIONS:
        ids = set(sections[key]) | set(prev_sections.get(key, {}))
        rows = [{"account_id": accs[i]["id"], "code": accs[i]["code"], "name": accs[i]["name"], "amount": money(sections[key].get(i, D0)),
                 "previous": money(prev_sections.get(key, {}).get(i, D0)) if compare else None, "percent": pct(sections[key].get(i, D0))}
                for i in ids if i in accs and (sections[key].get(i) or prev_sections.get(key, {}).get(i))]
        rows.sort(key=lambda r: -abs(Decimal(r["amount"])))
        out.append({"key": key, "label": label, "rows": rows, "total": money(t[key]), "previous": money(pt.get(key, D0)) if compare else None, "percent": pct(t[key])})
    subtotals = [{"key": k, "label": label, "amount": money(t[k]), "previous": money(pt.get(k, D0)) if compare else None, "percent": pct(t[k])}
                 for k, label in (("gross_profit", "Gross profit"), ("operating_profit", "Operating profit"), ("net_profit", "Net profit"))]
    return {"statement": "pl", "from": start.isoformat(), "to": end.isoformat(), "previous_period": {"from": prev[0].isoformat(), "to": prev[1].isoformat()} if prev else None,
            "sections": out, "subtotals": subtotals, "totals": {k: money(v) for k, v in t.items()}}


def bs_numbers(accs, sums):
    sections = {key: {} for key, _, _ in BS_SECTIONS}
    profit = D0
    for aid, (dr, cr) in sums.items():
        acc = accs.get(aid)
        if not acc:
            continue
        if acc["type"] in ("REVENUE", "EXPENSE"):
            profit += cr - dr
            continue
        section = bs_section(acc)
        if section:
            sections[section][aid] = dr - cr if acc["type"] == "ASSET" else cr - dr
    t = {key: sum(rows.values(), D0) for key, rows in sections.items()}
    t["profit_to_date"] = profit
    t["assets"] = t["current_assets"] + t["non_current_assets"]
    t["liabilities"] = t["current_liabilities"] + t["non_current_liabilities"]
    t["equity_total"] = t["equity"] + profit
    t["difference"] = t["assets"] - t["liabilities"] - t["equity_total"]
    return sections, t


def balance_sheet(org, as_of, compare=True):
    accs = accounts(org)
    sections, t = bs_numbers(accs, totals(org, None, as_of))
    prev_date = date(as_of.year - 1, as_of.month, min(as_of.day, 28)) if compare else None
    prev_sections, pt = bs_numbers(accs, totals(org, None, prev_date)) if compare else ({}, {})
    out = []
    for key, label, group in BS_SECTIONS:
        ids = set(sections[key]) | set(prev_sections.get(key, {}))
        rows = [{"account_id": accs[i]["id"], "code": accs[i]["code"], "name": accs[i]["name"], "amount": money(sections[key].get(i, D0)),
                 "previous": money(prev_sections.get(key, {}).get(i, D0)) if compare else None}
                for i in ids if i in accs and (sections[key].get(i) or prev_sections.get(key, {}).get(i))]
        if key == "equity":
            rows.append({"account_id": "", "code": "", "name": "Profit / (loss) to date (not yet closed)", "amount": money(t["profit_to_date"]),
                         "previous": money(pt.get("profit_to_date", D0)) if compare else None})
        rows.sort(key=lambda r: (r["account_id"] == "", r["code"]))
        total = t["equity_total"] if key == "equity" else t[key]
        out.append({"key": key, "label": label, "group": group, "rows": rows, "total": money(total),
                    "previous": money(pt.get("equity_total" if key == "equity" else key, D0)) if compare else None})
    return {"statement": "bs", "as_of": as_of.isoformat(), "previous_date": prev_date.isoformat() if prev_date else None, "sections": out,
            "totals": {k: money(v) for k, v in t.items()}, "previous_totals": {k: money(v) for k, v in pt.items()} if compare else None,
            "balanced": abs(t["difference"]) < Decimal("0.01")}


# --------------------------------------------------------------------------------------------
# Overview
# --------------------------------------------------------------------------------------------

def overview_data(org, start, end):
    accs = accounts(org)
    by_key = {a["key"]: aid for aid, a in accs.items() if a["key"]}
    life = totals(org, None, end)

    def ledger(*keys):
        return sum((balance(accs[by_key[k]], *life[by_key[k]]) for k in keys if k in by_key), D0)

    # Cash and bank: ledger accounts for cash and bank, plus any other asset account named like a bank or cash account.
    cash_ids = {aid for aid, a in accs.items() if a["key"] in ("CASH", "BANK") or (a["type"] == "ASSET" and a["subtype"] in ("CASH", "BANK"))}
    cash = sum((balance(accs[i], *life[i]) for i in cash_ids), D0)
    _, cur = pl_numbers(accs, totals(org, start, end))
    length = (end - start).days + 1
    prev_start, prev_end = previous_period(start, end)
    _, prev = pl_numbers(accs, totals(org, prev_start, prev_end))

    # 12-month trend ending with the month of `end`.
    first = date(end.year - (1 if end.month < 12 else 0), (end.month % 12) + 1, 1)
    months = []
    m = first
    while m <= end:
        months.append(m.strftime("%Y-%m"))
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    series = {k: {"income": D0, "expense": D0} for k in months}
    expense_by_account = defaultdict(lambda: D0)
    for day, aid, dr, cr in journal_lines(org, first, end):
        acc = accs.get(aid)
        if not acc or not day:
            continue
        key = day.strftime("%Y-%m")
        if acc["type"] == "REVENUE":
            series[key]["income"] += cr - dr
        elif acc["type"] == "EXPENSE":
            series[key]["expense"] += dr - cr
            if start <= day <= end:
                expense_by_account[aid] += dr - cr
    trend = [{"period": k, "income": money(v["income"]), "expense": money(v["expense"]), "net": money(v["income"] - v["expense"])} for k, v in series.items()]
    top = sorted(((aid, v) for aid, v in expense_by_account.items() if v > 0), key=lambda x: -x[1])[:6]
    total_exp = sum((v for _, v in expense_by_account.items() if v > 0), D0) or Decimal(1)

    _, bs = bs_numbers(accs, life)
    receivable, payable = ledger("ACCOUNTS_RECEIVABLE"), ledger("ACCOUNTS_PAYABLE")
    output_tax, input_tax = ledger("OUTPUT_TAX", "TAX_PAYABLE"), ledger("INPUT_TAX")
    sales = cur["revenue"]
    days = length

    def ratio(a, b, scale=Decimal(1)):
        return f"{(a / b * scale):.1f}" if b else None

    bank_accounts = [{"id": str(b.id), "name": b.account_name, "type": b.account_type, "bank": b.bank_name or "", "number": (b.account_number or "")[-4:],
                      "balance": money(b.current_balance or 0)} for b in BankAccount.objects(organization=org, is_active=True).order_by("account_name")]
    unreconciled = BankTransaction.objects(organization=org, reconciliation_status__ne="RECONCILED").count()
    drafts = JournalEntry.objects(organization=org, status="DRAFT").count()
    dr_total = sum((v[0] for v in life.values()), D0)
    cr_total = sum((v[1] for v in life.values()), D0)
    alerts = []
    if abs(dr_total - cr_total) >= Decimal("0.01"):
        alerts.append({"tone": "danger", "text": f"Your books are out of balance by ₹{money(abs(dr_total - cr_total))}. Check the trial balance.", "href": "/trial-balance"})
    if abs(bs["difference"]) >= Decimal("0.01"):
        alerts.append({"tone": "danger", "text": "The balance sheet does not balance. An account may be missing its type.", "href": "/balance-sheet"})
    if drafts:
        alerts.append({"tone": "warn", "text": f"{drafts} journal entries are still drafts and not in your reports.", "href": "/journal-entries"})
    if unreconciled:
        alerts.append({"tone": "info", "text": f"{unreconciled} bank transactions are not reconciled yet.", "href": "/banking"})
    if cash < 0:
        alerts.append({"tone": "danger", "text": "Cash and bank show a negative balance. A receipt may be missing.", "href": "/general-ledger"})

    return {"from": start.isoformat(), "to": end.isoformat(), "previous": {"from": prev_start.isoformat(), "to": prev_end.isoformat()},
            "cash_bank": money(cash), "receivable": money(receivable), "payable": money(payable), "gst_position": money(output_tax - input_tax),
            "income": money(cur["revenue"] + cur["other_income"]), "expenses": money(cur["cost_of_sales"] + cur["operating_expenses"] + cur["other_expenses"]),
            "net_profit": money(cur["net_profit"]), "gross_profit": money(cur["gross_profit"]),
            "previous_income": money(prev["revenue"] + prev["other_income"]), "previous_expenses": money(prev["cost_of_sales"] + prev["operating_expenses"] + prev["other_expenses"]),
            "previous_net_profit": money(prev["net_profit"]),
            "ratios": {"gross_margin": ratio(cur["gross_profit"], sales, Decimal(100)), "net_margin": ratio(cur["net_profit"], sales, Decimal(100)),
                       "current_ratio": ratio(bs["current_assets"], bs["current_liabilities"]), "receivable_days": ratio(receivable, sales, Decimal(days)),
                       "payable_days": ratio(payable, cur["cost_of_sales"] + cur["operating_expenses"], Decimal(days))},
            "trend": trend,
            "top_expenses": [{"account_id": accs[aid]["id"], "name": accs[aid]["name"], "amount": money(v), "share": f"{(v / total_exp * 100):.1f}"} for aid, v in top],
            "bank_accounts": bank_accounts, "unreconciled": unreconciled, "draft_journals": drafts, "alerts": alerts}


# --------------------------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------------------------

def denied(request):
    if not permitted(request, "accounting_reports.read"):
        return R.forbidden(message="You need the Accounting reports permission.", request=request)
    return None


@api_login_required
@require_http_methods(["GET"])
def overview(request):
    block = denied(request)
    if block:
        return block
    try:
        end = parse(request.GET.get("to"), today_ist())
        start = parse(request.GET.get("from"), fy_start(end))
        if start > end:
            raise ValueError("The start date is after the end date.")
        return R.success(data=overview_data(request.api_organization, start, end), request=request)
    except ValueError as e:
        return R.validation_error(message=str(e), request=request)


@api_login_required
@require_http_methods(["GET"])
def statement(request, kind):
    block = denied(request)
    if block:
        return block
    try:
        org = request.api_organization
        compare = request.GET.get("compare", "1") != "0"
        end = parse(request.GET.get("to"), today_ist())
        if kind == "profit-and-loss":
            start = parse(request.GET.get("from"), fy_start(end))
            if start > end:
                raise ValueError("The start date is after the end date.")
            data = profit_and_loss(org, start, end, compare)
            if request.GET.get("format") == "xlsx":
                rows = [["Section", "Code", "Account", f"{start} to {end}", "Previous period", "% of revenue"]]
                for s in data["sections"]:
                    rows += [[s["label"], r["code"], r["name"], float(r["amount"]), float(r["previous"] or 0), r["percent"] or ""] for r in s["rows"]]
                    rows.append([s["label"] + " total", "", "", float(s["total"]), float(s["previous"] or 0), s["percent"] or ""])
                rows += [[x["label"], "", "", float(x["amount"]), float(x["previous"] or 0), x["percent"] or ""] for x in data["subtotals"]]
                return workbook_response({"Profit and loss": rows}, f"NexEase-Profit-and-Loss-{end}")
            return R.success(data=data, request=request)
        if kind == "balance-sheet":
            data = balance_sheet(org, end, compare)
            if request.GET.get("format") == "xlsx":
                rows = [["Section", "Code", "Account", f"As of {end}", f"As of {data['previous_date'] or ''}"]]
                for s in data["sections"]:
                    rows += [[s["label"], r["code"], r["name"], float(r["amount"]), float(r["previous"] or 0)] for r in s["rows"]]
                    rows.append([s["label"] + " total", "", "", float(s["total"]), float(s["previous"] or 0)])
                rows += [["Total assets", "", "", float(data["totals"]["assets"]), ""], ["Liabilities + equity", "", "", float(Decimal(data["totals"]["liabilities"]) + Decimal(data["totals"]["equity_total"])), ""]]
                return workbook_response({"Balance sheet": rows}, f"NexEase-Balance-Sheet-{end}")
            return R.success(data=data, request=request)
        return R.not_found(message="Unknown statement.", request=request)
    except ValueError as e:
        return R.validation_error(message=str(e), request=request)
