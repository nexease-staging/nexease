"""Tally XML: the requests NexEase sends to TallyPrime (through the connector) and the parsing of
Tally's replies. Pure functions, no database.

Tally talks XML over HTTP on the computer where it runs (Exchange → Data Synchronization →
Client/Server: "Both", port 9000). NexEase never reaches it directly: the desktop connector relays
each request below to http://localhost:9000 and returns Tally's reply.

Conventions used by Tally XML that matter here:
- Amounts are signed: a debit is negative, a credit positive (ISDEEMEDPOSITIVE=Yes marks debits).
  NexEase normalises to "debit positive".
- Ledger and stock-item balances follow the same sign rule.
- Every object has a GUID and an ALTERID; ALTERID increases on every change, so "ALTERID > n"
  returns only what changed since the last sync. The company's ALTMSTID / ALTVCHID are the latest
  master / voucher alter ids, which tell us cheaply whether anything changed at all.
- Imports with a REMOTEID create the voucher the first time and alter the same voucher afterwards.
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

D0 = Decimal(0)

# Tally's own top-level groups; every ledger's group chain ends in one of these.
PRIMARY_GROUPS = {
    "Sundry Debtors": "debtors", "Sundry Creditors": "creditors", "Bank Accounts": "bank", "Bank OD A/c": "bank", "Cash-in-Hand": "cash",
    "Sales Accounts": "sales", "Purchase Accounts": "purchase", "Direct Expenses": "direct_expense", "Indirect Expenses": "indirect_expense",
    "Direct Incomes": "direct_income", "Indirect Incomes": "indirect_income", "Duties & Taxes": "tax", "Capital Account": "capital",
    "Reserves & Surplus": "capital", "Loans (Liability)": "loan", "Secured Loans": "loan", "Unsecured Loans": "loan", "Current Assets": "current_asset",
    "Current Liabilities": "current_liability", "Fixed Assets": "fixed_asset", "Investments": "investment", "Loans & Advances (Asset)": "current_asset",
    "Deposits (Asset)": "current_asset", "Stock-in-Hand": "stock", "Provisions": "current_liability", "Branch / Divisions": "branch",
    "Suspense A/c": "suspense", "Misc. Expenses (ASSET)": "current_asset",
}
NATURE = {"debtors": "asset", "bank": "asset", "cash": "asset", "current_asset": "asset", "fixed_asset": "asset", "investment": "asset", "stock": "asset",
          "creditors": "liability", "tax": "liability", "loan": "liability", "current_liability": "liability", "capital": "equity",
          "sales": "income", "direct_income": "income", "indirect_income": "income", "purchase": "expense", "direct_expense": "expense",
          "indirect_expense": "expense", "suspense": "liability", "branch": "asset"}

MASTER_KINDS = {
    "group": ("Group", "GUID, ALTERID, NAME, PARENT, ISDELETED"),
    "ledger": ("Ledger", "GUID, ALTERID, NAME, PARENT, OPENINGBALANCE, CLOSINGBALANCE, PARTYGSTIN, LEDGERMOBILE, LEDGERPHONE, EMAIL, LEDSTATENAME, "
                         "COUNTRYNAME, PINCODE, ADDRESS, BILLCREDITPERIOD, CREDITLIMIT, ISBILLWISEON, GSTREGISTRATIONTYPE, LEDGSTREGDETAILS, LEDMAILINGDETAILS, ALIAS"),
    "stockgroup": ("StockGroup", "GUID, ALTERID, NAME, PARENT"),
    "stockitem": ("StockItem", "GUID, ALTERID, NAME, PARENT, CATEGORY, BASEUNITS, OPENINGBALANCE, OPENINGVALUE, OPENINGRATE, CLOSINGBALANCE, CLOSINGVALUE, "
                               "CLOSINGRATE, GSTDETAILS, HSNDETAILS, STANDARDPRICELIST, STANDARDCOSTLIST, DESCRIPTION, ALIAS"),
    "unit": ("Unit", "GUID, ALTERID, NAME, ORIGINALNAME, ISSIMPLEUNIT, DECIMALPLACES"),
    "godown": ("Godown", "GUID, ALTERID, NAME, PARENT"),
    "costcentre": ("CostCentre", "GUID, ALTERID, NAME, PARENT, CATEGORY"),
    "vouchertype": ("VoucherType", "GUID, ALTERID, NAME, PARENT, NUMBERINGMETHOD, ISACTIVE"),
}
VOUCHER_FETCH = ("GUID, ALTERID, MASTERID, DATE, VOUCHERTYPENAME, VOUCHERNUMBER, REFERENCE, REFERENCEDATE, PARTYLEDGERNAME, PARTYNAME, NARRATION, "
                 "ISCANCELLED, ISOPTIONAL, ISDELETED, ISINVOICE, PERSISTEDVIEW, PARTYGSTIN, PLACEOFSUPPLY, STATENAME, BASICBUYERNAME, "
                 "ALLLEDGERENTRIES, LEDGERENTRIES, ALLINVENTORYENTRIES, INVENTORYENTRIES")
SYNC_ORDER = ["unit", "group", "stockgroup", "godown", "costcentre", "vouchertype", "ledger", "stockitem"]


# --------------------------------------------------------------------------------------------
# Request builders (Tally export)
# --------------------------------------------------------------------------------------------

def _envelope(collection, company, body_tdl, statics=""):
    company_var = f"<SVCURRENTCOMPANY>{escape(company)}</SVCURRENTCOMPANY>" if company else ""
    return ("<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE>"
            f"<ID>{collection}</ID></HEADER><BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>{company_var}{statics}"
            f"</STATICVARIABLES><TDL><TDLMESSAGE>{body_tdl}</TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>")


def companies_request():
    """Companies open in Tally, with their latest master / voucher alter ids."""
    tdl = ('<COLLECTION NAME="NXCompanies" ISMODIFY="No"><TYPE>Company</TYPE>'
           "<FETCH>NAME, GUID, ALTMSTID, ALTVCHID, STARTINGFROM, BOOKSFROM, ENDINGAT, STATENAME, COUNTRYNAME, PINCODE, EMAIL, PHONENUMBER, "
           "BASICCOMPANYFORMALNAME, GSTREGISTRATIONNUMBER</FETCH></COLLECTION>")
    return _envelope("NXCompanies", "", tdl)


def master_request(kind, company, after_alter_id=0, upto_alter_id=None):
    tally_type, fetch = MASTER_KINDS[kind]
    name = f"NX{tally_type}s"
    flt = f"$AlterID > {int(after_alter_id)}" + (f" AND $AlterID <= {int(upto_alter_id)}" if upto_alter_id else "")
    tdl = (f'<COLLECTION NAME="{name}" ISMODIFY="No"><TYPE>{tally_type}</TYPE><FETCH>{fetch}</FETCH><FILTER>NXDelta</FILTER></COLLECTION>'
           f'<SYSTEM TYPE="Formulae" NAME="NXDelta">{escape(flt)}</SYSTEM>')
    return _envelope(name, company, tdl)


def voucher_request(company, after_alter_id=0, upto_alter_id=None):
    flt = f"$AlterID > {int(after_alter_id)}" + (f" AND $AlterID <= {int(upto_alter_id)}" if upto_alter_id else "")
    tdl = (f'<COLLECTION NAME="NXVouchers" ISMODIFY="No"><TYPE>Voucher</TYPE><FETCH>{VOUCHER_FETCH}</FETCH><FILTER>NXDelta</FILTER></COLLECTION>'
           f'<SYSTEM TYPE="Formulae" NAME="NXDelta">{escape(flt)}</SYSTEM>')
    return _envelope("NXVouchers", company, tdl)


def index_request(kind, company):
    """Only GUID and ALTERID of every object of one kind, to find objects deleted in Tally."""
    tally_type = "Voucher" if kind == "voucher" else MASTER_KINDS[kind][0]
    tdl = f'<COLLECTION NAME="NXIndex" ISMODIFY="No"><TYPE>{tally_type}</TYPE><FETCH>GUID, ALTERID</FETCH></COLLECTION>'
    return _envelope("NXIndex", company, tdl)


# --------------------------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------------------------

_BAD_REFS = re.compile(r"&#(?:x0*[0-8bBcCeEfF]|x0*1[0-9a-fA-F]|0*(?:[0-8]|1[1-2]|1[4-9]|2[0-9]|3[01]));")
_BAD_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean(xml_text):
    """Tally writes control characters (e.g. &#4; before 'Any' or 'Primary') that strict XML rejects."""
    if isinstance(xml_text, bytes):
        for enc in ("utf-8", "utf-16"):
            try:
                xml_text = xml_text.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            xml_text = xml_text.decode("latin-1")
    xml_text = _BAD_REFS.sub("", xml_text)
    return _BAD_CHARS.sub("", xml_text).lstrip("﻿")


def element_to_dict(el):
    """Tally element → dict. Repeated '.LIST' children become lists; attributes are kept with '@'."""
    out = {f"@{k}": v for k, v in el.attrib.items()}
    for child in el:
        key = child.tag
        # Leaf fields carry only a TYPE attribute in Tally exports (e.g. <ALTERID TYPE="Number"> 12</ALTERID>); keep their text.
        value = element_to_dict(child) if len(child) else (child.text or "").strip()
        if key.endswith(".LIST"):
            out.setdefault(key, []).append(value)
        elif key in out:
            if not isinstance(out[key], list):
                out[key] = [out[key]]
            out[key].append(value)
        else:
            out[key] = value
    return out


def parse_objects(xml_text, tag):
    """All objects of one tag (e.g. LEDGER, VOUCHER) anywhere in Tally's reply."""
    root = ET.fromstring(clean(xml_text))
    status = root.findtext("HEADER/STATUS")
    if status is not None and status.strip() == "0":
        raise ValueError("Tally refused the request: " + (root.findtext(".//LINEERROR") or root.findtext("BODY/DATA") or "unknown error"))
    return [element_to_dict(el) for el in root.iter(tag)]


def text(value):
    if isinstance(value, dict):
        return ""
    if isinstance(value, list):
        return text(value[0]) if value else ""
    return (value or "").strip()


def amount(value):
    """Tally amounts: '-1180.00', '1,180.00 Dr', '₹ 1180', or '' → Decimal, debit positive."""
    raw = text(value)
    if not raw:
        return D0
    s = raw.replace(",", "").replace("₹", "").replace("Rs.", "").strip()
    sign = 1
    if s.endswith("Dr"):
        s, sign = s[:-2].strip(), 1
        return Decimal(s or 0) * sign
    if s.endswith("Cr"):
        s, sign = s[:-2].strip(), -1
        return Decimal(s or 0) * sign
    try:
        # Plain Tally amounts: negative = debit. Return debit-positive.
        return -Decimal(s)
    except InvalidOperation:
        return D0


def quantity(value):
    """'12.50 Nos' / '-3 Kg' / '12 Nos = 1 Box' → (Decimal qty, unit)."""
    raw = text(value).split("=")[0].strip()
    m = re.match(r"^(-?[\d,]*\.?\d+)\s*(.*)$", raw)
    if not m:
        return D0, ""
    return Decimal(m.group(1).replace(",", "")), m.group(2).strip()


def rate(value):
    raw = text(value).split("/")[0].replace(",", "").strip()
    try:
        return Decimal(raw) if raw else D0
    except InvalidOperation:
        return D0


def tdate(value):
    raw = text(value)
    if re.fullmatch(r"\d{8}", raw):
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def yes(value):
    return text(value).lower() == "yes"


def first(d, *keys):
    for k in keys:
        if d.get(k) not in (None, "", []):
            return d[k]
    return ""


def _name(d):
    if d.get("@NAME"):
        return d["@NAME"].strip()
    if text(d.get("NAME")):
        return text(d.get("NAME"))
    names = d.get("NAME.LIST") or []
    return text(names[0].get("NAME")) if names and isinstance(names[0], dict) else ""


def _address(d):
    lines = []
    for block in d.get("ADDRESS.LIST", []) or []:
        if isinstance(block, dict):
            addr = block.get("ADDRESS", "")
            lines += addr if isinstance(addr, list) else [addr]
    for m in d.get("LEDMAILINGDETAILS.LIST", []) or []:
        if isinstance(m, dict):
            for block in m.get("ADDRESS.LIST", []) or []:
                if isinstance(block, dict):
                    addr = block.get("ADDRESS", "")
                    lines += addr if isinstance(addr, list) else [addr]
    return ", ".join(text(x) for x in lines if text(x))


def normalise(kind, d):
    """A Tally object → the fields NexEase keeps (strings and plain numbers)."""
    base = {"guid": text(d.get("GUID")), "alter_id": int(text(d.get("ALTERID")) or 0), "name": _name(d), "deleted": yes(d.get("ISDELETED"))}
    if kind in ("group", "stockgroup", "godown", "costcentre", "vouchertype"):
        return {**base, "parent": text(d.get("PARENT"))}
    if kind == "unit":
        return {**base, "name": _name(d) or text(d.get("ORIGINALNAME")), "decimals": text(d.get("DECIMALPLACES"))}
    if kind == "ledger":
        gst_regs = d.get("LEDGSTREGDETAILS.LIST") or []
        gstin = text(d.get("PARTYGSTIN")) or next((text(g.get("GSTIN")) for g in gst_regs if isinstance(g, dict) and text(g.get("GSTIN"))), "")
        mailing = next((m for m in d.get("LEDMAILINGDETAILS.LIST") or [] if isinstance(m, dict)), {})
        return {**base, "parent": text(d.get("PARENT")), "opening": str(amount(d.get("OPENINGBALANCE"))), "closing": str(amount(d.get("CLOSINGBALANCE"))),
                "gstin": gstin.upper(), "phone": text(first(d, "LEDGERMOBILE", "LEDGERPHONE")), "email": text(d.get("EMAIL")),
                "state": text(d.get("LEDSTATENAME")) or text(mailing.get("STATE")), "pincode": text(d.get("PINCODE")) or text(mailing.get("PINCODE")),
                "address": _address(d), "credit_days": re.sub(r"\D", "", text(d.get("BILLCREDITPERIOD"))), "credit_limit": str(-amount(d.get("CREDITLIMIT")) if text(d.get("CREDITLIMIT")) else ""),
                "billwise": yes(d.get("ISBILLWISEON"))}
    if kind == "stockitem":
        hsn, gst = "", ""
        for g in (d.get("GSTDETAILS.LIST") or []) + (d.get("HSNDETAILS.LIST") or []):
            if isinstance(g, dict):
                hsn = text(g.get("HSNCODE")) or hsn
                for st in g.get("STATEWISEDETAILS.LIST", []) or []:
                    for r in (st.get("RATEDETAILS.LIST", []) if isinstance(st, dict) else []) or []:
                        if isinstance(r, dict) and text(r.get("GSTRATEDUTYHEAD")) == "IGST" and text(r.get("GSTRATE")):
                            gst = text(r.get("GSTRATE"))
        open_qty, unit = quantity(d.get("OPENINGBALANCE"))
        close_qty, cunit = quantity(d.get("CLOSINGBALANCE"))
        price = next((rate(p.get("RATE")) for p in d.get("STANDARDPRICELIST.LIST") or [] if isinstance(p, dict) and text(p.get("RATE"))), D0)
        cost = next((rate(p.get("RATE")) for p in d.get("STANDARDCOSTLIST.LIST") or [] if isinstance(p, dict) and text(p.get("RATE"))), D0)
        return {**base, "parent": text(d.get("PARENT")), "category": text(d.get("CATEGORY")), "unit": text(d.get("BASEUNITS")) or unit or cunit,
                "hsn": hsn, "gst_rate": gst, "opening_qty": str(open_qty), "opening_value": str(abs(amount(d.get("OPENINGVALUE")))),
                "closing_qty": str(close_qty), "closing_value": str(abs(amount(d.get("CLOSINGVALUE")))), "closing_rate": str(rate(d.get("CLOSINGRATE"))),
                "selling_price": str(price), "cost_price": str(cost), "description": text(d.get("DESCRIPTION"))}
    if kind == "voucher":
        return {**base, **voucher_fields(d)}
    return base


def voucher_fields(d):
    entries, bills = [], []
    ledger_lists = (d.get("ALLLEDGERENTRIES.LIST") or []) + (d.get("LEDGERENTRIES.LIST") or [])
    inventory = []
    for inv in (d.get("ALLINVENTORYENTRIES.LIST") or []) + (d.get("INVENTORYENTRIES.LIST") or []):
        if not isinstance(inv, dict):
            continue
        qty, unit = quantity(first(inv, "ACTUALQTY", "BILLEDQTY"))
        godown = next((text(b.get("GODOWNNAME")) for b in inv.get("BATCHALLOCATIONS.LIST") or [] if isinstance(b, dict)), "")
        inventory.append({"item": text(inv.get("STOCKITEMNAME")), "qty": str(abs(qty)), "unit": unit, "rate": str(rate(inv.get("RATE"))),
                          "amount": str(abs(amount(inv.get("AMOUNT")))), "discount": text(inv.get("DISCOUNT")), "godown": godown, "inward": yes(inv.get("ISDEEMEDPOSITIVE"))})
        for alloc in inv.get("ACCOUNTINGALLOCATIONS.LIST") or []:
            if isinstance(alloc, dict) and text(alloc.get("LEDGERNAME")):
                ledger_lists.append(alloc)
    for le in ledger_lists:
        if not isinstance(le, dict) or not text(le.get("LEDGERNAME")):
            continue
        amt = amount(le.get("AMOUNT"))
        entries.append({"ledger": text(le.get("LEDGERNAME")), "amount": str(amt)})
        for b in le.get("BILLALLOCATIONS.LIST") or []:
            if isinstance(b, dict) and text(b.get("NAME")):
                bills.append({"ledger": text(le.get("LEDGERNAME")), "name": text(b.get("NAME")), "type": text(b.get("BILLTYPE")), "amount": str(amount(b.get("AMOUNT"))),
                              "credit_days": re.sub(r"\D", "", text(b.get("BILLCREDITPERIOD")))})
    party = text(first(d, "PARTYLEDGERNAME", "PARTYNAME"))
    party_amount = next((Decimal(e["amount"]) for e in entries if e["ledger"] == party), D0)
    total = sum((Decimal(e["amount"]) for e in entries if Decimal(e["amount"]) > 0), D0)
    return {"date": tdate(d.get("DATE")), "voucher_type": text(d.get("VOUCHERTYPENAME")) or d.get("@VCHTYPE", ""), "number": text(d.get("VOUCHERNUMBER")),
            "reference": text(d.get("REFERENCE")), "party": party, "party_gstin": text(d.get("PARTYGSTIN")), "place_of_supply": text(first(d, "PLACEOFSUPPLY", "STATENAME")),
            "narration": text(d.get("NARRATION")), "cancelled": yes(d.get("ISCANCELLED")), "optional": yes(d.get("ISOPTIONAL")), "is_invoice": yes(d.get("ISINVOICE")),
            "amount": str(abs(party_amount) or total), "party_amount": str(party_amount), "entries": entries, "inventory": inventory, "bills": bills,
            "remote_id": d.get("@REMOTEID", "")}


def parse_response(xml_text):
    """Import reply: counts and errors."""
    root = ET.fromstring(clean(xml_text))
    get = lambda tag: int((root.findtext(f".//{tag}") or "0").strip() or 0)
    errors = [e.text.strip() for e in root.iter("LINEERROR") if e.text and e.text.strip()]
    return {"created": get("CREATED"), "altered": get("ALTERED"), "deleted": get("DELETED"), "cancelled": get("CANCELLED"), "errors": get("ERRORS"),
            "exceptions": get("EXCEPTIONS"), "last_id": (root.findtext(".//LASTVCHID") or root.findtext(".//LASTMID") or "").strip(), "messages": errors}


def primary_group(name, groups):
    """Walk a group chain up to Tally's primary group; returns the PRIMARY_GROUPS code."""
    seen = set()
    while name and name not in seen:
        if name in PRIMARY_GROUPS:
            return PRIMARY_GROUPS[name]
        seen.add(name)
        name = groups.get(name, "")
    return ""


# --------------------------------------------------------------------------------------------
# Import builders (NexEase → Tally)
# --------------------------------------------------------------------------------------------

def x(value):
    return escape(str(value if value is not None else ""))


def tamount(value):
    return f"{Decimal(value):.2f}"


def import_envelope(company, report, body):
    return ("<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC>"
            f"<REPORTNAME>{report}</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY>{x(company)}</SVCURRENTCOMPANY></STATICVARIABLES>"
            f'</REQUESTDESC><REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">{body}</TALLYMESSAGE></REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>')


def ledger_xml(company, name, parent, old_name=None, gstin="", state="", address="", phone="", email="", pincode="", billwise=True, credit_days=""):
    action = "Alter" if old_name else "Create"
    addr = "".join(f"<ADDRESS>{x(line.strip())}</ADDRESS>" for line in re.split(r"[\n,]", address or "") if line.strip())[:2000]
    body = (f'<LEDGER NAME="{x(old_name or name)}" ACTION="{action}"><NAME.LIST><NAME>{x(name)}</NAME></NAME.LIST><PARENT>{x(parent)}</PARENT>'
            f"<ISBILLWISEON>{'Yes' if billwise else 'No'}</ISBILLWISEON>"
            + (f"<ADDRESS.LIST>{addr}</ADDRESS.LIST>" if addr else "")
            + (f"<LEDSTATENAME>{x(state)}</LEDSTATENAME><COUNTRYNAME>India</COUNTRYNAME>" if state else "")
            + (f"<PINCODE>{x(pincode)}</PINCODE>" if pincode else "")
            + (f"<LEDGERMOBILE>{x(phone)}</LEDGERMOBILE>" if phone else "")
            + (f"<EMAIL>{x(email)}</EMAIL>" if email else "")
            + (f"<BILLCREDITPERIOD>{x(credit_days)} Days</BILLCREDITPERIOD>" if credit_days else "")
            + (f"<PARTYGSTIN>{x(gstin)}</PARTYGSTIN><GSTREGISTRATIONTYPE>Regular</GSTREGISTRATIONTYPE>"
               f"<LEDGSTREGDETAILS.LIST><APPLICABLEFROM>20170701</APPLICABLEFROM><GSTREGISTRATIONTYPE>Regular</GSTREGISTRATIONTYPE>"
               f"<STATE>{x(state)}</STATE><GSTIN>{x(gstin)}</GSTIN></LEDGSTREGDETAILS.LIST>" if gstin else "")
            + "</LEDGER>")
    return import_envelope(company, "All Masters", body)


def unit_xml(company, symbol):
    return import_envelope(company, "All Masters", f'<UNIT NAME="{x(symbol)}" ACTION="Create"><NAME>{x(symbol)}</NAME><ISSIMPLEUNIT>Yes</ISSIMPLEUNIT></UNIT>')


def stockitem_xml(company, name, unit, hsn="", gst_rate="", old_name=None, price=None, description=""):
    action = "Alter" if old_name else "Create"
    gst = ""
    if hsn or gst_rate:
        rate_value = Decimal(str(gst_rate or 0))
        rates = "".join(f"<RATEDETAILS.LIST><GSTRATEDUTYHEAD>{h}</GSTRATEDUTYHEAD><GSTRATEVALUATIONTYPE>Based on Value</GSTRATEVALUATIONTYPE><GSTRATE>{r:g}</GSTRATE></RATEDETAILS.LIST>"
                        for h, r in (("IGST", rate_value), ("CGST", rate_value / 2), ("SGST/UTGST", rate_value / 2)))
        gst = (f"<GSTAPPLICABLE>&#4; Applicable</GSTAPPLICABLE><GSTDETAILS.LIST><APPLICABLEFROM>20170701</APPLICABLEFROM><HSNCODE>{x(hsn)}</HSNCODE>"
               f"<TAXABILITY>{'Taxable' if rate_value else 'Exempt'}</TAXABILITY><STATEWISEDETAILS.LIST><STATENAME>&#4; Any</STATENAME>{rates}</STATEWISEDETAILS.LIST>"
               "</GSTDETAILS.LIST>")
    price_xml = f"<STANDARDPRICELIST.LIST><DATE>20170401</DATE><RATE>{tamount(price)}/{x(unit)}</RATE></STANDARDPRICELIST.LIST>" if price else ""
    body = (f'<STOCKITEM NAME="{x(old_name or name)}" ACTION="{action}"><NAME.LIST><NAME>{x(name)}</NAME></NAME.LIST><PARENT/>'
            f"<BASEUNITS>{x(unit)}</BASEUNITS>" + (f"<DESCRIPTION>{x(description)}</DESCRIPTION>" if description else "") + gst + price_xml + "</STOCKITEM>")
    return import_envelope(company, "All Masters", body)


def _ledger_entry(ledger, debit_positive, bills=None, party=False):
    """One ledger line. NexEase passes debit-positive amounts; Tally wants debit negative."""
    amt = Decimal(debit_positive)
    is_debit = amt > 0
    bill_xml = "".join(f"<BILLALLOCATIONS.LIST><NAME>{x(b['name'])}</NAME><BILLTYPE>{x(b['type'])}</BILLTYPE><AMOUNT>{tamount(-amt if b.get('amount') is None else -Decimal(b['amount']))}</AMOUNT></BILLALLOCATIONS.LIST>"
                       for b in (bills or []))
    return (f"<LEDGERENTRIES.LIST><LEDGERNAME>{x(ledger)}</LEDGERNAME><ISDEEMEDPOSITIVE>{'Yes' if is_debit else 'No'}</ISDEEMEDPOSITIVE>"
            f"<ISPARTYLEDGER>{'Yes' if party else 'No'}</ISPARTYLEDGER><AMOUNT>{tamount(-amt)}</AMOUNT>{bill_xml}</LEDGERENTRIES.LIST>")


def voucher_xml(company, v):
    """A voucher dictionary → Tally import XML.

    v = {remote_id, voucher_type, date (YYYY-MM-DD), number, reference, narration, party, cancelled,
         lines: [{ledger, amount (debit positive), bills?, party?}],
         inventory: [{item, qty, unit, rate, amount, ledger, godown?}] with amount debit-positive for the item's ledger side}
    """
    vtype = v["voucher_type"]
    if v.get("cancelled"):
        body = (f'<VOUCHER REMOTEID="{x(v["remote_id"])}" VCHTYPE="{x(vtype)}" ACTION="Cancel"><DATE>{v["date"].replace("-", "")}</DATE>'
                f"<VOUCHERTYPENAME>{x(vtype)}</VOUCHERTYPENAME><VOUCHERNUMBER>{x(v.get('number', ''))}</VOUCHERNUMBER></VOUCHER>")
        return import_envelope(company, "Vouchers", body)
    inventory = v.get("inventory") or []
    view = "Invoice Voucher View" if inventory else "Accounting Voucher View"
    inv_xml = ""
    for it in inventory:
        amt = Decimal(it["amount"])
        is_debit = amt > 0
        godown = f"<BATCHALLOCATIONS.LIST><GODOWNNAME>{x(it['godown'])}</GODOWNNAME><BATCHNAME>Primary Batch</BATCHNAME><AMOUNT>{tamount(-amt)}</AMOUNT><ACTUALQTY>{x(it['qty'])} {x(it['unit'])}</ACTUALQTY><BILLEDQTY>{x(it['qty'])} {x(it['unit'])}</BILLEDQTY></BATCHALLOCATIONS.LIST>" if it.get("godown") else ""
        inv_xml += (f"<ALLINVENTORYENTRIES.LIST><STOCKITEMNAME>{x(it['item'])}</STOCKITEMNAME><ISDEEMEDPOSITIVE>{'Yes' if is_debit else 'No'}</ISDEEMEDPOSITIVE>"
                    f"<RATE>{tamount(it['rate'])}/{x(it['unit'])}</RATE><AMOUNT>{tamount(-amt)}</AMOUNT><ACTUALQTY>{x(it['qty'])} {x(it['unit'])}</ACTUALQTY>"
                    f"<BILLEDQTY>{x(it['qty'])} {x(it['unit'])}</BILLEDQTY>{godown}<ACCOUNTINGALLOCATIONS.LIST><LEDGERNAME>{x(it['ledger'])}</LEDGERNAME>"
                    f"<ISDEEMEDPOSITIVE>{'Yes' if is_debit else 'No'}</ISDEEMEDPOSITIVE><AMOUNT>{tamount(-amt)}</AMOUNT></ACCOUNTINGALLOCATIONS.LIST></ALLINVENTORYENTRIES.LIST>")
    lines = "".join(_ledger_entry(l["ledger"], l["amount"], l.get("bills"), l.get("party", False)) for l in v.get("lines", []))
    order = v.get("is_order")
    body = (f'<VOUCHER REMOTEID="{x(v["remote_id"])}" VCHTYPE="{x(vtype)}" ACTION="Create" OBJVIEW="{view}">'
            f"<DATE>{v['date'].replace('-', '')}</DATE><EFFECTIVEDATE>{v['date'].replace('-', '')}</EFFECTIVEDATE><VOUCHERTYPENAME>{x(vtype)}</VOUCHERTYPENAME>"
            f"<VOUCHERNUMBER>{x(v.get('number', ''))}</VOUCHERNUMBER><PERSISTEDVIEW>{view}</PERSISTEDVIEW>"
            + (f"<REFERENCE>{x(v['reference'])}</REFERENCE>" if v.get("reference") else "")
            + (f"<PARTYLEDGERNAME>{x(v['party'])}</PARTYLEDGERNAME><PARTYNAME>{x(v['party'])}</PARTYNAME>" if v.get("party") else "")
            + (f"<PARTYGSTIN>{x(v['party_gstin'])}</PARTYGSTIN>" if v.get("party_gstin") else "")
            + (f"<PLACEOFSUPPLY>{x(v['place_of_supply'])}</PLACEOFSUPPLY>" if v.get("place_of_supply") else "")
            + f"<NARRATION>{x(v.get('narration', ''))}</NARRATION><ISINVOICE>{'Yes' if inventory and not order else 'No'}</ISINVOICE>"
            + ("<ISORDERVOUCHER>Yes</ISORDERVOUCHER>" if order else "")
            + inv_xml + lines + "</VOUCHER>")
    return import_envelope(company, "Vouchers", body)


def balanced(v):
    """Debits equal credits (inventory amounts count on their ledger side)."""
    total = sum((Decimal(l["amount"]) for l in v.get("lines", [])), D0) + sum((Decimal(i["amount"]) for i in v.get("inventory", [])), D0)
    return abs(total) < Decimal("0.01")


def today_tally():
    return date.today().strftime("%Y%m%d")
