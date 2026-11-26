"""A small in-memory TallyPrime that speaks the XML NexEase sends: collection exports with an
AlterID filter, GUID indexes, and imports of ledgers, units, stock items and vouchers (create,
alter by REMOTEID, cancel). Used by the sync tests and the connector end-to-end test.
"""
import re
import threading
import uuid
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

D0 = Decimal(0)


def amt(text):
    return Decimal((text or "0").strip() or "0")


class FakeTally:
    def __init__(self, company="Sharma Traders", state="Maharashtra", gstin="27AAACS1111A1Z5"):
        self.company = {"name": company, "guid": "company-" + uuid.uuid4().hex[:6], "state": state, "gstin": gstin}
        self.alter = 0
        self.alt_mst = 0
        self.alt_vch = 0
        self.objects = {"group": {}, "ledger": {}, "stockitem": {}, "unit": {}, "stockgroup": {}, "godown": {}, "costcentre": {}, "vouchertype": {}, "voucher": {}}
        self.requests = []
        for name, parent in [("Sundry Debtors", ""), ("Sundry Creditors", ""), ("Sales Accounts", ""), ("Purchase Accounts", ""), ("Duties & Taxes", ""),
                             ("Bank Accounts", ""), ("Cash-in-Hand", ""), ("Indirect Expenses", ""), ("Mumbai Debtors", "Sundry Debtors")]:
            self.add("group", name, parent=parent)
        for name in ["Sales", "Purchase", "Receipt", "Payment", "Journal", "Credit Note", "Debit Note", "Sales Order", "Purchase Order", "Contra"]:
            self.add("vouchertype", name, parent=name)
        self.add("vouchertype", "GST Sales", parent="Sales")
        for name, parent in [("Sales GST", "Sales Accounts"), ("Purchase GST", "Purchase Accounts"), ("Output CGST", "Duties & Taxes"), ("Output SGST", "Duties & Taxes"),
                             ("Output IGST", "Duties & Taxes"), ("Input CGST", "Duties & Taxes"), ("Input SGST", "Duties & Taxes"), ("Input IGST", "Duties & Taxes"),
                             ("HDFC Bank", "Bank Accounts"), ("Cash", "Cash-in-Hand"), ("Round Off", "Indirect Expenses"), ("Office Expenses", "Indirect Expenses")]:
            self.add("ledger", name, parent=parent)
        self.add("unit", "Nos")

    # ---------------------------------------------------------------- state
    def bump(self, kind):
        self.alter += 1
        if kind == "voucher":
            self.alt_vch = self.alter
        else:
            self.alt_mst = self.alter
        return self.alter

    def add(self, kind, name, guid=None, **fields):
        guid = guid or uuid.uuid4().hex
        obj = {"guid": guid, "name": name, "alter_id": self.bump(kind), "fields": fields}
        self.objects[kind][guid] = obj
        return obj

    def by_name(self, kind, name):
        return next((o for o in self.objects[kind].values() if o["name"] == name), None)

    def touch(self, obj, kind):
        obj["alter_id"] = self.bump(kind)

    def delete(self, kind, name):
        obj = self.by_name(kind, name)
        del self.objects[kind][obj["guid"]]
        self.bump(kind)

    def voucher(self, vtype, number, date, party, lines, inventory=(), remote_id=None, bills=()):
        """lines: [(ledger, tally_amount)] with debit negative, like Tally."""
        guid = remote_id or uuid.uuid4().hex
        return self.add("voucher", number, guid=guid, vtype=vtype, number=number, date=date, party=party, lines=list(lines), inventory=list(inventory),
                        bills=list(bills), cancelled=False, remote_id=remote_id or "", narration="")

    def closing(self, ledger):
        opening = self.by_name("ledger", ledger)["fields"].get("opening", D0)
        total = opening
        for v in self.objects["voucher"].values():
            if v["fields"]["cancelled"]:
                continue
            for name, value in v["fields"]["lines"]:
                if name == ledger:
                    total += value
            for it in v["fields"]["inventory"]:
                if it["ledger"] == ledger:
                    total += it["amount"]
        return total

    # ---------------------------------------------------------------- protocol
    def handle(self, xml_text):
        self.requests.append(xml_text)
        root = ET.fromstring(xml_text)
        if (root.findtext("HEADER/TALLYREQUEST") or "").strip() == "Import Data":
            return self.do_import(root)
        return self.do_export(root, xml_text)

    def wrap(self, inner):
        return f'<ENVELOPE><HEADER><VERSION>1</VERSION><STATUS>1</STATUS></HEADER><BODY><DESC></DESC><DATA><COLLECTION>{inner}</COLLECTION></DATA></BODY></ENVELOPE>'

    def do_export(self, root, xml_text):
        ttype = (root.findtext(".//COLLECTION/TYPE") or "").strip()
        m = re.search(r"\$AlterID &gt; (\d+)(?: AND \$AlterID &lt;= (\d+))?", xml_text) or re.search(r"\$AlterID > (\d+)(?: AND \$AlterID <= (\d+))?", xml_text)
        lo, hi = (int(m.group(1)), int(m.group(2)) if m.group(2) else None) if m else (None, None)
        index_only = "<FETCH>GUID, ALTERID</FETCH>" in xml_text
        if ttype == "Company":
            c = self.company
            return self.wrap(f'<COMPANY NAME={quoteattr(c["name"])}><NAME TYPE="String">{escape(c["name"])}</NAME><GUID TYPE="String">{c["guid"]}</GUID>'
                             f'<ALTMSTID TYPE="Number"> {self.alt_mst}</ALTMSTID><ALTVCHID TYPE="Number"> {self.alt_vch}</ALTVCHID><BOOKSFROM TYPE="Date">20260401</BOOKSFROM>'
                             f'<STATENAME>{escape(c["state"])}</STATENAME><GSTREGISTRATIONNUMBER>{c["gstin"]}</GSTREGISTRATIONNUMBER></COMPANY>')
        kind = {"Group": "group", "Ledger": "ledger", "StockItem": "stockitem", "Unit": "unit", "StockGroup": "stockgroup", "Godown": "godown",
                "CostCentre": "costcentre", "VoucherType": "vouchertype", "Voucher": "voucher"}[ttype]
        out = []
        for o in sorted(self.objects[kind].values(), key=lambda o: o["alter_id"]):
            if lo is not None and (o["alter_id"] <= lo or (hi is not None and o["alter_id"] > hi)):
                continue
            out.append(self.render(kind, o, index_only))
        return self.wrap("".join(out))

    def render(self, kind, o, index_only=False):
        tag = kind.upper()
        head = f'<GUID TYPE="String">{o["guid"]}</GUID><ALTERID TYPE="Number"> {o["alter_id"]}</ALTERID>'
        if index_only:
            return f"<{tag}>{head}</{tag}>"
        f = o["fields"]
        if kind == "voucher":
            lines = "".join(f'<ALLLEDGERENTRIES.LIST><LEDGERNAME>{escape(n)}</LEDGERNAME><AMOUNT>{a:.2f}</AMOUNT>'
                            + "".join(f'<BILLALLOCATIONS.LIST><NAME>{escape(b["name"])}</NAME><BILLTYPE>{b["type"]}</BILLTYPE><AMOUNT>{b["amount"]:.2f}</AMOUNT></BILLALLOCATIONS.LIST>'
                                      for b in f["bills"] if b["ledger"] == n)
                            + "</ALLLEDGERENTRIES.LIST>" for n, a in f["lines"])
            inv = "".join(f'<ALLINVENTORYENTRIES.LIST><STOCKITEMNAME>{escape(i["item"])}</STOCKITEMNAME><RATE>{i["rate"]}</RATE><AMOUNT>{i["amount"]:.2f}</AMOUNT>'
                          f'<ACTUALQTY> {i["qty"]}</ACTUALQTY><ACCOUNTINGALLOCATIONS.LIST><LEDGERNAME>{escape(i["ledger"])}</LEDGERNAME><AMOUNT>{i["amount"]:.2f}</AMOUNT>'
                          "</ACCOUNTINGALLOCATIONS.LIST></ALLINVENTORYENTRIES.LIST>" for i in f["inventory"])
            remote = f' REMOTEID={quoteattr(f["remote_id"])}' if f["remote_id"] else ""
            return (f'<VOUCHER{remote} VCHTYPE={quoteattr(f["vtype"])}>{head}<DATE TYPE="Date">{f["date"].replace("-", "")}</DATE>'
                    f'<VOUCHERTYPENAME>{escape(f["vtype"])}</VOUCHERTYPENAME><VOUCHERNUMBER>{escape(f["number"])}</VOUCHERNUMBER>'
                    f'<PARTYLEDGERNAME>{escape(f["party"])}</PARTYLEDGERNAME><NARRATION>{escape(f["narration"])}</NARRATION>'
                    f'<ISCANCELLED>{"Yes" if f["cancelled"] else "No"}</ISCANCELLED>{lines}{inv}</VOUCHER>')
        body = f'<NAME.LIST><NAME>{escape(o["name"])}</NAME></NAME.LIST><PARENT>&#4; {escape(f.get("parent", ""))}</PARENT>' if f.get("parent") else f'<NAME.LIST><NAME>{escape(o["name"])}</NAME></NAME.LIST>'
        if kind == "ledger":
            body = f'<NAME.LIST><NAME>{escape(o["name"])}</NAME></NAME.LIST><PARENT>{escape(f.get("parent", ""))}</PARENT>'
            body += f'<OPENINGBALANCE>{f.get("opening", D0):.2f}</OPENINGBALANCE><CLOSINGBALANCE>{self.closing(o["name"]):.2f}</CLOSINGBALANCE>'
            for key, tagname in (("gstin", "PARTYGSTIN"), ("phone", "LEDGERMOBILE"), ("email", "EMAIL"), ("state", "LEDSTATENAME")):
                if f.get(key):
                    body += f"<{tagname}>{escape(f[key])}</{tagname}>"
            if f.get("address"):
                body += "<ADDRESS.LIST>" + "".join(f"<ADDRESS>{escape(a)}</ADDRESS>" for a in f["address"].split("\n")) + "</ADDRESS.LIST>"
        if kind == "stockitem":
            body += f'<BASEUNITS>{escape(f.get("unit", "Nos"))}</BASEUNITS><CLOSINGBALANCE> {f.get("qty", 0)} {escape(f.get("unit", "Nos"))}</CLOSINGBALANCE>'
            body += f'<CLOSINGVALUE>-{f.get("value", 0)}</CLOSINGVALUE>'
            if f.get("hsn"):
                body += f'<GSTDETAILS.LIST><HSNCODE>{f["hsn"]}</HSNCODE><STATEWISEDETAILS.LIST><RATEDETAILS.LIST><GSTRATEDUTYHEAD>IGST</GSTRATEDUTYHEAD><GSTRATE> {f.get("gst", 18)}</GSTRATE></RATEDETAILS.LIST></STATEWISEDETAILS.LIST></GSTDETAILS.LIST>'
        return f"<{tag} NAME={quoteattr(o['name'])}>{head}{body}</{tag}>"

    def do_import(self, root):
        created = altered = cancelled = errors = 0
        messages, last = [], ""
        for el in root.find(".//TALLYMESSAGE"):
            tag = el.tag
            try:
                if tag in ("LEDGER", "UNIT", "STOCKITEM"):
                    kind = tag.lower()
                    old = el.get("NAME")
                    name = el.findtext("NAME.LIST/NAME") or el.findtext("NAME") or old
                    existing = self.by_name(kind, old)
                    if el.get("ACTION") == "Create" and existing:
                        raise ValueError(f"{tag.title()} '{old}' already exists!")
                    if el.get("ACTION") == "Alter" and not existing:
                        raise ValueError(f"{tag.title()} '{old}' does not exist!")
                    fields = {}
                    if kind == "ledger":
                        parent = el.findtext("PARENT")
                        if not self.by_name("group", parent):
                            raise ValueError(f"Group '{parent}' does not exist!")
                        fields = {"parent": parent, "gstin": el.findtext("PARTYGSTIN") or "", "phone": el.findtext("LEDGERMOBILE") or "",
                                  "state": el.findtext("LEDSTATENAME") or "", "email": el.findtext("EMAIL") or "",
                                  "address": "\n".join(a.text or "" for a in el.iter("ADDRESS"))}
                    if kind == "stockitem":
                        unit = el.findtext("BASEUNITS")
                        if not self.by_name("unit", unit):
                            raise ValueError(f"Unit '{unit}' does not exist!")
                        fields = {"unit": unit, "hsn": el.findtext(".//HSNCODE") or ""}
                    if existing:
                        existing["name"] = name
                        existing["fields"].update(fields)
                        self.touch(existing, kind)
                        altered += 1
                    else:
                        self.add(kind, name, **fields)
                        created += 1
                elif tag == "VOUCHER":
                    rid = el.get("REMOTEID")
                    existing = self.objects["voucher"].get(rid)
                    if el.get("ACTION") == "Cancel":
                        if not existing:
                            raise ValueError("Voucher to cancel does not exist")
                        existing["fields"]["cancelled"] = True
                        self.touch(existing, "voucher")
                        cancelled += 1
                        continue
                    lines, bills, inventory = [], [], []
                    for le in el.findall("LEDGERENTRIES.LIST"):
                        name = le.findtext("LEDGERNAME")
                        if not self.by_name("ledger", name):
                            raise ValueError(f"Ledger '{name}' does not exist!")
                        lines.append((name, amt(le.findtext("AMOUNT"))))
                        for b in le.findall("BILLALLOCATIONS.LIST"):
                            bills.append({"ledger": name, "name": b.findtext("NAME"), "type": b.findtext("BILLTYPE"), "amount": amt(b.findtext("AMOUNT"))})
                    for ie in el.findall("ALLINVENTORYENTRIES.LIST"):
                        item = ie.findtext("STOCKITEMNAME")
                        if not self.by_name("stockitem", item):
                            raise ValueError(f"Stock Item '{item}' does not exist!")
                        led = ie.findtext("ACCOUNTINGALLOCATIONS.LIST/LEDGERNAME")
                        if not self.by_name("ledger", led):
                            raise ValueError(f"Ledger '{led}' does not exist!")
                        inventory.append({"item": item, "qty": ie.findtext("ACTUALQTY"), "rate": ie.findtext("RATE"), "amount": amt(ie.findtext("AMOUNT")), "ledger": led})
                    total = sum((a for _, a in lines), D0) + sum((i["amount"] for i in inventory), D0)
                    if abs(total) >= Decimal("0.01"):
                        raise ValueError(f"Voucher totals do not match! Dr/Cr differ by {total}")
                    vtype = el.findtext("VOUCHERTYPENAME")
                    if not self.by_name("vouchertype", vtype):
                        raise ValueError(f"Voucher type '{vtype}' does not exist!")
                    fields = {"vtype": vtype, "number": el.findtext("VOUCHERNUMBER") or "", "date": el.findtext("DATE"), "party": el.findtext("PARTYLEDGERNAME") or "",
                              "lines": lines, "inventory": inventory, "bills": bills, "narration": el.findtext("NARRATION") or "", "remote_id": rid, "cancelled": False}
                    fields["date"] = f"{fields['date'][:4]}-{fields['date'][4:6]}-{fields['date'][6:]}"
                    if existing:
                        existing["fields"].update(fields)
                        self.touch(existing, "voucher")
                        altered += 1
                    else:
                        self.add("voucher", fields["number"], guid=rid, **fields)
                        created += 1
                    last = str(self.alter)
            except ValueError as e:
                errors += 1
                messages.append(str(e))
        err = "".join(f"<LINEERROR>{escape(m)}</LINEERROR>" for m in messages)
        return (f"<ENVELOPE><HEADER><VERSION>1</VERSION><STATUS>1</STATUS></HEADER><BODY><DATA><IMPORTRESULT><CREATED>{created}</CREATED><ALTERED>{altered}</ALTERED>"
                f"<DELETED>0</DELETED><LASTVCHID>{last}</LASTVCHID><LASTMID>0</LASTMID><COMBINED>0</COMBINED><IGNORED>0</IGNORED><ERRORS>{errors}</ERRORS>"
                f"<CANCELLED>{cancelled}</CANCELLED><EXCEPTIONS>0</EXCEPTIONS></IMPORTRESULT>{err}</DATA></BODY></ENVELOPE>")

    # ---------------------------------------------------------------- HTTP
    def serve(self, port=0):
        tally = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8")
                reply = tally.handle(body).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/xml; charset=utf-8")
                self.send_header("Content-Length", str(len(reply)))
                self.end_headers()
                self.wfile.write(reply)

            def do_GET(self):
                reply = b"<RESPONSE>TallyPrime Server is Running</RESPONSE>"
                self.send_response(200)
                self.send_header("Content-Length", str(len(reply)))
                self.end_headers()
                self.wfile.write(reply)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server
