"""Tenant-scoped Sandbox IRP integration: e-invoices for tax invoices and credit notes.

Supported documents
* Tax invoices (INV) and credit notes (CRN) issued from NexEase.
* Supply categories: B2B, SEZ with/without payment (SEZWP/SEZWOP) and exports with/without payment
  (EXPWP/EXPWOP). SEZ and export supplies always carry IGST (zero for "without payment", i.e. under LUT/bond).

Rules carried here
* 30-day reporting window: a business with aggregate turnover of ₹10 crore or more cannot report a document
  to the IRP more than 30 days after its date. When the workspace says it is in that band, NexEase blocks the
  submission with a clear message (the IRP would reject it anyway); every document shows the days left.
* A request is claimed before it is sent; a timeout leaves it "pending" for recovery, never a blind resend.
* Automatic IRN (optional): the background worker registers newly issued B2B invoices one at a time.
"""
import base64
import hashlib
import json
import logging
import os
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from cryptography.fernet import Fernet, InvalidToken
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db
from mongoengine.errors import ValidationError

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.saas.entitlements import has_einvoice, org_lock
from apps.sales.models import CreditNote, Invoice
from .gst_provider import NoRedirect, configuration, request_json
from .models import BusinessRecord
from .views import audit, payload, permitted

log = logging.getLogger(__name__)
PREFIX = '/gst/compliance/e-invoice/tax-payer'
GSTIN = r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]'
IRN = r'[a-fA-F0-9]{64}'
ELIGIBLE = ('ISSUED', 'PARTIALLY_PAID', 'PAID')
CATEGORIES = {
    'B2B': 'Business to business',
    'SEZWP': 'SEZ with payment of IGST',
    'SEZWOP': 'SEZ without payment (LUT/bond)',
    'EXPWP': 'Export with payment of IGST',
    'EXPWOP': 'Export without payment (LUT/bond)',
}
REPORTING_DAYS = 30
BULK_LIMIT = 25
UNITS = {'PIECE': 'PCS', 'PIECES': 'PCS', 'PC': 'PCS', 'NOS': 'NOS', 'UNIT': 'UNT', 'UNITS': 'UNT', 'KG': 'KGS', 'L': 'LTR',
         'BOX': 'BOX', 'PACK': 'PAC', 'BOTTLE': 'BTL', 'SHEET': 'SHT', 'SQFT': 'SQF', 'MTR': 'MTR', 'SET': 'SET'}


def cipher():
    try:
        return Fernet(os.environ.get('EINVOICE_ENCRYPTION_KEY', '').encode())
    except ValueError:
        raise ValueError('Configure EINVOICE_ENCRYPTION_KEY on the backend.') from None


def registration(org):
    record = BusinessRecord.objects(organization=org, kind='gst_settings', key='registration').first()
    return record.data if record else {}


def settings_key(org, env):
    return f'{org.id}:{env}'


def environment():
    return os.getenv('GST_SANDBOX_ENV', 'test').strip().lower()


def saved_settings(org, env=None):
    return get_db().nexease_einvoice_settings.find_one({'_id': settings_key(org, env or environment())}) or {}


def call(base, path, headers, body=None, method=None):
    raw = json.dumps(body).encode() if body is not None else None
    req = Request(base+path, data=raw, method=method, headers={'Accept': 'application/json', 'Content-Type': 'application/json', **headers})
    try:
        with build_opener(NoRedirect()).open(req, timeout=20) as response:
            data = json.loads(response.read(524288))
    except HTTPError as exc:
        raise ValueError(f'Sandbox request returned HTTP {exc.code}. Check live access and provider logs.') from None
    except (URLError, OSError, ValueError):
        raise ValueError('Sandbox response could not be verified. Check the portal before submitting again.') from None
    if not isinstance(data, dict):
        raise ValueError('Unexpected Sandbox response.')
    return data


def unwrap(result):
    data = result
    for _ in range(4):
        if str(data.get('code', 200)) not in ('200', '201') or str(data.get('status_cd', data.get('Status', 1))) in ('0', 'false', 'False'):
            ref = str(result.get('transaction_id', ''))
            suffix = f' Reference: {ref}.' if re.fullmatch(r'[a-fA-F0-9-]{8,64}', ref) else ''
            detail = _error_text(data)
            raise ValueError('IRP rejected the request.' + (f' {detail}' if detail else ' Review the provider transaction.') + suffix)
        child = data.get('data', data.get('Data'))
        if isinstance(child, str) and child.startswith('{'):
            try:
                child = json.loads(child)
            except ValueError:
                raise ValueError('Invalid Sandbox response data.') from None
        if not isinstance(child, dict):
            return data
        data = child
    return data


def _error_text(data):
    """Short, safe error detail from an IRP/NIC failure payload (codes and messages only)."""
    for key in ('ErrorDetails', 'error_details', 'errors'):
        rows = data.get(key)
        if isinstance(rows, list) and rows:
            parts = []
            for r in rows[:3]:
                if isinstance(r, dict):
                    code, msg = str(r.get('ErrorCode', r.get('error_code', ''))), str(r.get('ErrorMessage', r.get('error_message', '')))
                    parts.append(f'{code} {msg}'.strip()[:160])
            return '; '.join(p for p in parts if p)
    msg = data.get('message') or data.get('error_message')
    return str(msg)[:200] if isinstance(msg, str) else ''


def session(org, seller_gstin, *, eway=False):
    key, secret, env = configuration()
    saved = get_db().nexease_einvoice_settings.find_one({'_id': settings_key(org, env)})
    if not saved or saved['gstin'] != seller_gstin:
        raise ValueError('An administrator must connect IRP credentials for the invoice seller GSTIN.')
    base = 'https://api.sandbox.co.in' if env == 'live' else 'https://test-api.sandbox.co.in'
    version = 'EWAY_SANDBOX_API_VERSION' if eway else 'EINVOICE_SANDBOX_API_VERSION'
    headers = {'x-api-key': key, 'x-api-version': os.getenv(version, '1.0.0'), 'x-source': 'primary'}
    token_key = ('nx-eway:' if eway else 'nx-irp:')+hashlib.sha256((key+saved['credentials']).encode()).hexdigest()
    token = cache.get(token_key)
    if not token:
        try:
            credentials = json.loads(cipher().decrypt(saved['credentials'].encode()))
        except (InvalidToken, ValueError):
            raise ValueError('IRP credentials cannot be read. Verify the encryption key or reconnect.') from None
        auth = request_json(base+'/authenticate', {'x-api-key': key, 'x-api-secret': secret}, None)
        jwt = unwrap(auth).get('access_token')
        if not jwt:
            raise ValueError('Sandbox API authentication did not return an access token.')
        auth_route = '/gst/compliance/e-way-bill/tax-payer/authenticate' if eway else PREFIX+'/authenticate?force=false'
        data = unwrap(call(base, auth_route, {**headers, 'authorization': jwt}, {
            'gstin': seller_gstin, 'username': credentials['username'],
            'password': base64.b64encode(credentials['password'].encode()).decode().rstrip('='),
        }))
        token = data.get('access_token') or data.get('AuthToken') or data.get('auth_token')
        if not isinstance(token, str) or not token or '\r' in token or '\n' in token:
            raise ValueError('IRP authentication did not return an access token.')
        cache.set(token_key, token, 5*3600)
    return base, {**headers, 'authorization': token}, saved


def money(value):
    return Decimal(str(value)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def require_text(value, label, minimum, maximum):
    value = str(value or '').strip()
    if not minimum <= len(value) <= maximum:
        raise ValueError(f'Enter {label} ({minimum}–{maximum} characters).')
    return value


def pin(value):
    if not re.fullmatch(r'[1-9][0-9]{5}', str(value)):
        raise ValueError('Enter a valid six-digit PIN code for the seller and buyer.')
    return int(value)


def gst_unit(value):
    unit = str(value or '').upper().strip()
    unit = UNITS.get(unit, unit)
    if not re.fullmatch(r'[A-Z]{3}', unit):
        raise ValueError('Use a three-letter GST unit code for each goods line (e.g. PCS, KGS, LTR).')
    return unit


# ---------------------------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------------------------

def _invoice_lines(inv):
    rows = []
    for i in inv.items:
        rows.append(dict(name=(i.item_name or i.product.name), service=i.item_type == 'service', hsn=i.hsn_code or '', unit=i.unit,
                         qty=money(i.quantity), price=money(i.unit_price), gross=money(i.line_subtotal), disc=money(i.discount),
                         tax=money(i.line_tax), rate=money(i.tax_rate), total=money(i.line_total)))
    return rows


def _credit_lines(cn):
    rows = []
    for i in cn.items:
        p = i.product
        rows.append(dict(name=p.name, service=p.item_type == 'service', hsn=p.hsn_code or '', unit=p.unit,
                         qty=money(i.quantity), price=money(i.unit_price), gross=money(i.line_subtotal), disc=money(i.discount),
                         tax=money(i.line_tax), rate=money(i.tax_rate), total=money(i.line_total)))
    return rows


def _export_details(export):
    export = export if isinstance(export, dict) else {}
    country = str(export.get('country', '')).upper().strip()
    if not re.fullmatch(r'[A-Z]{2}', country):
        raise ValueError('Enter the two-letter destination country code for the export (e.g. AE, US).')
    out = {'CntCode': country}
    currency = str(export.get('currency', '')).upper().strip()
    if currency:
        if not re.fullmatch(r'[A-Z]{3}', currency):
            raise ValueError('Enter a three-letter currency code (e.g. USD).')
        out['ForCur'] = currency
    port = str(export.get('port', '')).upper().strip()
    if port:
        if not re.fullmatch(r'[A-Z0-9]{2,10}', port):
            raise ValueError('Enter the port code in letters and digits (e.g. INNSA1).')
        out['Port'] = port
    bill = str(export.get('shipping_bill', '')).strip()
    when = str(export.get('shipping_bill_date', '')).strip()
    if bool(bill) != bool(when):
        raise ValueError('Enter both the shipping bill number and date, or neither.')
    if bill:
        if not re.fullmatch(r'[0-9A-Za-z]{1,20}', bill):
            raise ValueError('Shipping bill number can have up to 20 letters or digits.')
        out.update(ShipBNo=bill, ShipBDt=date.fromisoformat(when).strftime('%d/%m/%Y'))
    return out


def _compose(*, typ, number, doc_date, lines, totals, category, reg, seller, gstin, buyer, pos, export=None, reference=None):
    """Build and validate an IRP v1.1 document. `totals` = (subtotal, discount, tax, total) as stored."""
    if category not in CATEGORIES:
        raise ValueError('Choose a supply category: B2B, SEZ or export.')
    if reg.get('registration') != 'regular' or gstin != reg.get('gstin') or not re.fullmatch(GSTIN, gstin or ''):
        raise ValueError('Document seller GSTIN must match the workspace regular GST registration.')
    if not re.fullmatch(r'[1-9A-Z][A-Z0-9/-]{0,15}', number or ''):
        raise ValueError('IRP document number must be uppercase, at most 16 characters, and not start with 0, / or -.')
    export_supply = category.startswith('EXP')
    sez = category.startswith('SEZ')
    without_payment = category.endswith('WOP')
    if export_supply:
        buyer, pos, buyer_state = 'URP', '96', '96'
    else:
        if not re.fullmatch(GSTIN, buyer or ''):
            raise ValueError('B2B and SEZ e-invoices need the buyer GSTIN.')
        if sez:
            pos = buyer[:2]
        if not re.fullmatch(r'[0-9]{2}', pos or ''):
            raise ValueError('Enter the place-of-supply state code on the document.')
        buyer_state = buyer[:2]
        if category == 'B2B' and gstin[:2] == pos and buyer[:2] != pos:
            raise ValueError('Review seller, buyer and place-of-supply states before generating the IRN.')
    all_igst = export_supply or sez or gstin[:2] != pos
    rows = []
    taxable = cgst = sgst = igst = discount = Decimal(0)
    for index, i in enumerate(lines, 1):
        if not re.fullmatch(r'[0-9]{6}' if i['service'] else r'[0-9]{4}(?:[0-9]{2}){0,2}', i['hsn']):
            raise ValueError('Review HSN/SAC on every line.')
        base = i['gross'] - i['disc']
        if base < 0 or money(i['qty']*i['price']) != i['gross'] or money(base*i['rate']/100) != i['tax'] or money(base+i['tax']) != i['total']:
            raise ValueError('Line amounts do not reconcile. Review prices, discounts and GST.')
        if without_payment and i['tax']:
            raise ValueError(f'{CATEGORIES[category]} must carry no GST. Use 0% on every line, or choose the "with payment" category.')
        inter = i['tax'] if all_igst else Decimal(0)
        half = money(i['tax']/2) if not all_igst else Decimal(0)
        other = i['tax']-half if not all_igst else Decimal(0)
        row = {'SlNo': str(index), 'PrdDesc': i['name'][:300], 'IsServc': 'Y' if i['service'] else 'N', 'HsnCd': i['hsn'],
               'Qty': float(i['qty']), 'UnitPrice': float(i['price']), 'TotAmt': float(i['gross']), 'Discount': float(i['disc']),
               'AssAmt': float(base), 'GstRt': float(i['rate']), 'IgstAmt': float(inter), 'CgstAmt': float(half), 'SgstAmt': float(other),
               'TotItemVal': float(base+i['tax'])}
        if not i['service']:
            row['Unit'] = gst_unit(i['unit'])
        rows.append(row)
        taxable += base; cgst += half; sgst += other; igst += inter; discount += i['disc']
    subtotal, disc_total, tax_total, grand = (money(x) for x in totals)
    total = taxable+cgst+sgst+igst
    if not rows or discount != disc_total or taxable+discount != subtotal or cgst+sgst+igst != tax_total or total != grand:
        raise ValueError('Document totals do not reconcile with the IRP payload.')
    if sez and not without_payment and not igst:
        raise ValueError('SEZ supply with payment needs IGST on the lines. Choose "without payment" for LUT/bond supplies.')
    buyer_block = {'Gstin': buyer, 'LglNm': require_text(seller['buyer_name'], 'buyer legal name', 3, 100),
                   'Addr1': require_text(seller['buyer_address'], 'buyer billing address', 1, 100),
                   'Loc': require_text(seller['buyer_city'], 'buyer city', 1, 50),
                   'Pin': 999999 if export_supply else pin(seller['buyer_pin']), 'Stcd': buyer_state, 'Pos': pos}
    document = {
        'Version': '1.1',
        'TranDtls': {'TaxSch': 'GST', 'SupTyp': category, 'RegRev': 'N', 'IgstOnIntra': 'Y' if (sez and gstin[:2] == pos and igst) else 'N'},
        'DocDtls': {'Typ': typ, 'No': number, 'Dt': doc_date.strftime('%d/%m/%Y')},
        'SellerDtls': {'Gstin': gstin, 'LglNm': require_text(reg.get('legal_name'), 'seller legal name', 3, 100),
                       'Addr1': require_text(seller.get('address'), 'seller address', 1, 100),
                       'Loc': require_text(seller.get('city'), 'seller city', 1, 50), 'Pin': pin(seller.get('pincode')), 'Stcd': gstin[:2]},
        'BuyerDtls': buyer_block,
        'ItemList': rows,
        'ValDtls': {'AssVal': float(taxable), 'CgstVal': float(cgst), 'SgstVal': float(sgst), 'IgstVal': float(igst), 'TotInvVal': float(total)},
    }
    if export_supply:
        document['ExpDtls'] = _export_details(export)
    if reference:
        document['RefDtls'] = {'PrecDocDtls': [reference]}
    return document


def build_document(inv, reg, seller, category='B2B', export=None):
    d = inv.billing_details or {}
    if inv.status not in ELIGIBLE or not d.get('tax_reviewed') or d.get('supply_type') != 'taxable':
        raise ValueError('Choose an issued, reviewed GST tax invoice.')
    if d.get('supplier_state') != (d.get('supplier_gstin') or '')[:2]:
        raise ValueError('Review the seller state on the invoice before generating the IRN.')
    if not category.startswith('EXP') and getattr(inv, 'billing_country', 'India').strip().lower() not in ('india', 'in'):
        raise ValueError('Choose an export category for an invoice billed outside India.')
    parties = dict(seller, buyer_name=inv.billing_name, buyer_address=inv.billing_address, buyer_city=inv.billing_city, buyer_pin=inv.billing_pincode)
    return _compose(typ='INV', number=inv.invoice_number, doc_date=inv.invoice_date, lines=_invoice_lines(inv),
                    totals=(inv.subtotal, inv.discount_amount, inv.tax_amount, inv.total_amount), category=category, reg=reg,
                    seller=parties, gstin=d.get('supplier_gstin', ''), buyer=(inv.customer_gstin or '').upper(), pos=d.get('place_of_supply', ''),
                    export=export)


def build_credit_document(cn, reg, seller, export=None):
    if cn.status != 'ISSUED':
        raise ValueError('Choose an issued credit note.')
    inv = cn.invoice
    if not inv:
        raise ValueError('Link the credit note to its original invoice before registering it with the IRP.')
    d = inv.billing_details or {}
    if d.get('supply_type') != 'taxable':
        raise ValueError('Only credit notes against GST tax invoices are reported to the IRP.')
    original = (inv.einvoice or {}).get('document') or {}
    category = (original.get('TranDtls') or {}).get('SupTyp', 'B2B')
    export = export or ({'country': original.get('ExpDtls', {}).get('CntCode', '')} if category.startswith('EXP') else None)
    parties = dict(seller, buyer_name=inv.billing_name, buyer_address=inv.billing_address, buyer_city=inv.billing_city, buyer_pin=inv.billing_pincode)
    reference = {'InvNo': inv.invoice_number, 'InvDt': inv.invoice_date.strftime('%d/%m/%Y')}
    return _compose(typ='CRN', number=cn.credit_note_number, doc_date=cn.credit_note_date, lines=_credit_lines(cn),
                    totals=(cn.subtotal, cn.discount_amount, cn.tax_amount, cn.total_amount), category=category, reg=reg,
                    seller=parties, gstin=d.get('supplier_gstin', ''), buyer=(inv.customer_gstin or '').upper(), pos=d.get('place_of_supply', ''),
                    export=export, reference=reference)


def saved_result(result, document):
    data = unwrap(result)
    irn = data.get('Irn', '')
    qr = data.get('SignedQRCode', '')
    doc = document['DocDtls']
    expected = hashlib.sha256((document['SellerDtls']['Gstin']+financial_year(doc['Dt'])+doc['Typ']+doc['No']).encode()).hexdigest()
    if not re.fullmatch(IRN, str(irn)) or irn.lower() != expected or not isinstance(qr, str) or not 1 <= len(qr) <= 4096:
        raise ValueError('IRP response did not match this document. Verify it in the IRP before proceeding.')
    status = str(data.get('Status', 'ACT')).upper()
    if status not in ('ACT', 'ACTIVE', 'CNL', 'CANCELLED'):
        raise ValueError('IRP returned an unrecognized document status.')
    return {'status': 'cancelled' if status in ('CNL', 'CANCELLED') else 'registered', 'irn': irn, 'qr': qr,
            'ack_no': str(data.get('AckNo', ''))[:30], 'ack_date': str(data.get('AckDt', ''))[:40]}


def financial_year(value):
    when = datetime.strptime(value, '%d/%m/%Y')
    start = when.year-(when.month < 4)
    return f'{start}-{str(start+1)[-2:]}'


# ---------------------------------------------------------------------------------------------
# Deadlines
# ---------------------------------------------------------------------------------------------

def ist_today():
    return (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date()


def days_left(doc_date, today=None):
    """Days remaining to report a document to the IRP (negative once the 30-day window has passed)."""
    d = doc_date.date() if isinstance(doc_date, datetime) else doc_date
    return REPORTING_DAYS - ((today or ist_today()) - d).days


def check_window(prefs, doc_date, number):
    if prefs.get('turnover_10cr') and days_left(doc_date) < 0:
        raise ValueError(f'{number} is more than {REPORTING_DAYS} days old. With turnover of ₹10 crore or more, the IRP does not accept it any more. '
                         'Issue a fresh document dated today if the supply needs an e-invoice.')


# ---------------------------------------------------------------------------------------------
# Processing (shared by single, bulk and automatic generation)
# ---------------------------------------------------------------------------------------------

def _load(org, kind, doc_id):
    model = CreditNote if kind == 'credit_note' else Invoice
    try:
        return model.objects(organization=org, id=doc_id).first()
    except ValidationError:
        return None


def _doc_number(kind, obj):
    return obj.credit_note_number if kind == 'credit_note' else obj.invoice_number


def _doc_date(kind, obj):
    return obj.credit_note_date if kind == 'credit_note' else obj.invoice_date


def _seller_gstin(kind, obj):
    inv = obj.invoice if kind == 'credit_note' else obj
    return ((inv.billing_details or {}) if inv else {}).get('supplier_gstin', '')


def process(org, kind, obj, action, data, *, env, reg, prefs, actor=None):
    """Run one IRP action for an invoice or credit note. Call under org_lock. Returns the updated object."""
    old = obj.einvoice or {}
    status = old.get('status')
    number = _doc_number(kind, obj)
    if old and old.get('environment') != env:
        raise ValueError('This document has an IRP record in another environment. Use a different document for live testing.')
    if kind == 'invoice' and action == 'generate' and obj.eway_status:
        raise ValueError('Resolve the linked e-way bill before submitting an e-invoice.')
    if kind == 'invoice' and action == 'cancel' and obj.eway_status:
        raise ValueError('Resolve or cancel the linked e-way bill before cancelling the IRN.')
    if action == 'generate' and status:
        raise ValueError('This document already has an IRP record. Recover a pending request instead of submitting again.')
    if action == 'recover' and status != 'pending':
        raise ValueError('This document is not pending recovery.')
    if action in ('cancel', 'check-cancellation') and status not in ('registered', 'cancel_pending'):
        raise ValueError('An active IRN is required.')
    if action == 'cancel' and status == 'cancel_pending':
        raise ValueError('Check the cancellation outcome before retrying.')
    if action == 'generate':
        if kind == 'credit_note' and obj.status != 'ISSUED':
            raise ValueError('Choose an issued credit note.')
        if kind == 'invoice' and obj.status not in ELIGIBLE:
            raise ValueError('Choose an issued invoice.')
        check_window(prefs, _doc_date(kind, obj), number)
        from apps.saas.provider_guard import reserve_einvoice
        reserve_einvoice(org, obj.id, env)
    base, headers, seller = session(org, _seller_gstin(kind, obj))
    category = str(data.get('category') or 'B2B').upper()
    if old:
        document = old.get('document')
    elif kind == 'credit_note':
        document = build_credit_document(obj, reg, seller, data.get('export'))
    else:
        document = build_document(obj, reg, seller, category, data.get('export'))
    route = PREFIX+'/invoice'
    model = type(obj)
    if kind == 'invoice' and action == 'generate' and data.get('transport') is not None:
        from .ewaybill import transport
        if not isinstance(data['transport'], dict) or any(i['IsServc'] == 'Y' for i in document['ItemList']):
            raise ValueError('Combined generation requires a goods-only invoice and transport details.')
        if document['TranDtls']['SupTyp'].startswith('EXP') or document['BuyerDtls']['Stcd'] != document['BuyerDtls']['Pos'] or \
                (obj.billing_details or {}).get('shipping_address') not in ('', None, obj.billing_address):
            raise ValueError('Use the portal for exports or a separate ship-to address or state.')
        document['EwbDtls'] = {k: v for k, v in transport(data['transport']).items() if v != ''}
    if action == 'generate':
        guard = dict(id=obj.id, organization=org, status=obj.status, updated_at=obj.updated_at, einvoice__status__exists=False)
        update = dict(set__einvoice={'status': 'pending', 'environment': env, 'document': document}, set__updated_at=datetime.utcnow())
        if kind == 'invoice':
            guard['eway_status__in'] = ['', None]
            update['set__eway_status'] = 'pending' if 'EwbDtls' in document else ''
        if not model.objects(**guard).update_one(**update):
            raise ValueError('Document changed. Reload it before submitting.')
        if 'EwbDtls' in document:
            from .ewaybill import key_for
            get_db().nexease_eway_bills.update_one({'_id': key_for(org, env, 'invoice', str(obj.id))}, {'$setOnInsert': {
                'organization_id': str(org.id), 'environment': env, 'kind': 'invoice', 'source_id': str(obj.id),
                'document': number, 'status': 'pending', 'created_at': datetime.utcnow()}}, upsert=True)
        reply = call(base, route, headers, document)
        result = saved_result(reply, document)
    elif action in ('recover', 'check-cancellation'):
        doc = document['DocDtls']
        query = urlencode(dict(document_type=doc['Typ'], document_number=doc['No'], document_date=doc['Dt']))
        reply = call(base, route+'?'+query, headers)
        result = saved_result(reply, document)
    else:
        reason = str(data.get('reason', ''))
        remarks = require_text(data.get('remarks'), 'cancellation remarks', 3, 100)
        if reason not in ('1', '2', '3', '4'):
            raise ValueError('Select a cancellation reason.')
        irn = old['irn']
        obj.update(set__einvoice={**old, 'status': 'cancel_pending'})
        reply = unwrap(call(base, route+'/'+irn+'/cancel', headers, {'Irn': irn, 'CnlRsn': reason, 'CnlRem': remarks}))
        if reply.get('Irn') != irn or not reply.get('CancelDate'):
            raise ValueError('IRP cancellation could not be verified. Check the cancellation outcome.')
        result = {**old, 'status': 'cancelled', 'cancel_date': str(reply['CancelDate'])[:40]}
    if kind == 'invoice' and 'EwbDtls' in document and action in ('generate', 'recover'):
        from .ewaybill import key_for, response_fields
        key = key_for(org, env, 'invoice', str(obj.id))
        ewb_status = 'pending'; ewb = {}
        try:
            ewb = response_fields(unwrap(reply)); ewb_status = 'generated'
        except ValueError:
            pass
        coll = get_db().nexease_eway_bills
        existing = coll.find_one({'_id': key})
        if existing and existing['status'] in ('portal_recorded', 'portal_cancelled'):
            ewb_status = '' if existing['status'] == 'portal_cancelled' else existing['status']
        else:
            coll.update_one({'_id': key}, {'$set': {
                **ewb, 'organization_id': str(org.id), 'environment': env, 'kind': 'invoice', 'source_id': str(obj.id),
                'document': number, 'status': ewb_status}, '$setOnInsert': {'created_at': datetime.utcnow()}}, upsert=True)
        obj.update(set__eway_status=ewb_status)
    obj.update(set__einvoice={**result, 'environment': env, 'document': document})
    obj.reload()
    return obj


# ---------------------------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------------------------

def public(obj, kind='invoice', prefs=None):
    data = obj.einvoice or {}
    doc_date = _doc_date(kind, obj)
    left = days_left(doc_date)
    document = data.get('document') or {}
    customer = obj.billing_name if kind == 'invoice' else (obj.invoice.billing_name if obj.invoice else (obj.customer.name if obj.customer else ''))
    row = {'id': str(obj.id), 'kind': kind, 'number': _doc_number(kind, obj), 'date': doc_date.date().isoformat(),
           'customer': customer, 'invoice_status': obj.status, 'total': f'{money(obj.total_amount):f}',
           'category': (document.get('TranDtls') or {}).get('SupTyp', ''),
           'days_left': left if not data.get('status') else None,
           'late': bool(not data.get('status') and left < 0 and (prefs or {}).get('turnover_10cr')),
           **{k: data[k] for k in ('status', 'irn', 'ack_no', 'ack_date', 'environment', 'cancel_date') if k in data}}
    if kind == 'credit_note':
        row['invoice_number'] = obj.invoice.invoice_number if obj.invoice else ''
        row['invoice_irn'] = ((obj.invoice.einvoice or {}).get('irn', '')) if obj.invoice else ''
    else:
        row['export'] = getattr(obj, 'billing_country', 'India').strip().lower() not in ('india', 'in', '')
        auto = get_db().nexease_einvoice_auto.find_one({'_id': str(obj.id)})
        if auto and not data.get('status'):
            row['auto_error'] = auto.get('error', '')[:300]
    return row


def _listing(request, org, env, reg, prefs):
    from mongoengine.queryset.visitor import Q
    search = request.GET.get('search', '').strip()[:50]
    tab = request.GET.get('kind', 'invoice')
    if tab == 'credit_note':
        query = CreditNote.objects(organization=org, status__in=['ISSUED', 'CANCELLED'])
        if search:
            query = query.filter(credit_note_number__icontains=search)
        rows = [public(x, 'credit_note', prefs) for x in query.order_by('-credit_note_date').limit(100)
                if (x.invoice and (x.invoice.billing_details or {}).get('supply_type') == 'taxable') or (x.einvoice or {}).get('status')]
    else:
        query = Invoice.objects(organization=org, status__in=[*ELIGIBLE, 'CANCELLED'])
        if search:
            query = query.filter(invoice_number__icontains=search)
        query = query.filter(Q(customer_gstin__ne='') | Q(einvoice__status__exists=True) | Q(billing_country__nin=['India', 'india', 'IN', '']))
        rows = [public(x, 'invoice', prefs) for x in query.order_by('-invoice_date').limit(100)]
    open_rows = [r for r in rows if not r.get('status') and r['invoice_status'] not in ('CANCELLED',)]
    summary = {
        'to_register': len(open_rows),
        'due_soon': sum(1 for r in open_rows if r['days_left'] is not None and 0 <= r['days_left'] <= 5),
        'late': sum(1 for r in open_rows if r['days_left'] is not None and r['days_left'] < 0),
        'pending': sum(1 for r in rows if r.get('status') in ('pending', 'cancel_pending')),
    }
    return rows, summary


@api_login_required
@require_http_methods(['GET', 'POST'])
def einvoices(request):
    org = request.api_organization
    if not has_einvoice(org) or not permitted(request, 'invoices.read'):
        return R.forbidden(message='E-invoicing requires an active Pro plan and invoice access.', request=request)
    admin = permitted(request, 'organizations.update')
    try:
        env = environment()
        reg = registration(org)
        saved = saved_settings(org, env)
        prefs = {'turnover_10cr': bool(saved.get('turnover_10cr')), 'auto_generate': bool(saved.get('auto_generate'))}
        if request.method == 'GET':
            rows, summary = _listing(request, org, env, reg, prefs)
            return R.success(data={'records': rows, 'summary': summary,
                'configured': bool(saved and saved.get('gstin') == reg.get('gstin')), 'gstin': reg.get('gstin', ''), 'environment': env,
                'preferences': prefs, 'categories': CATEGORIES, 'reporting_days': REPORTING_DAYS, 'bulk_limit': BULK_LIMIT,
                'can_configure': admin, 'can_issue': permitted(request, 'invoices.issue'), 'can_cancel': permitted(request, 'invoices.cancel')},
                request=request)
        data = payload(request)
        action = data.get('action')
        if action == 'configure':
            if not admin:
                return R.forbidden(message='Organization administrator required.', request=request)
            _, _, env = configuration()
            gstin = reg.get('gstin', '')
            if reg.get('registration') != 'regular' or not re.fullmatch(GSTIN, gstin):
                raise ValueError('Set a regular seller GSTIN under Taxation first.')
            fields = {k: require_text(data.get(k), k, 1, n) for k, n in [('username', 100), ('address', 100), ('city', 50), ('pincode', 6)]}
            password = data.get('password')
            if not isinstance(password, str) or not 1 <= len(password) <= 200:
                raise ValueError('Enter the IRP API password.')
            pin(fields['pincode'])
            credentials = cipher().encrypt(json.dumps({'username': fields.pop('username'), 'password': password}).encode()).decode()
            with org_lock(org.id):
                get_db().nexease_einvoice_settings.update_one({'_id': settings_key(org, env)}, {'$set': {**fields, 'gstin': gstin, 'credentials': credentials}}, upsert=True)
            audit(request, 'einvoice', org.id, 'configure')
            return R.success(data={'configured': True}, request=request)
        if action == 'preferences':
            if not admin:
                return R.forbidden(message='Organization administrator required.', request=request)
            if not saved:
                raise ValueError('Connect IRP credentials first.')
            update = {}
            if 'turnover_10cr' in data:
                update['turnover_10cr'] = bool(data['turnover_10cr'])
            if 'auto_generate' in data:
                update['auto_generate'] = bool(data['auto_generate'])
                if update['auto_generate'] and not saved.get('auto_generate'):
                    update['auto_since'] = datetime.utcnow()
            get_db().nexease_einvoice_settings.update_one({'_id': settings_key(org, env)}, {'$set': update})
            audit(request, 'einvoice', org.id, 'preferences')
            return R.success(data={'preferences': {**prefs, **{k: v for k, v in update.items() if k != 'auto_since'}}}, request=request)
        if action == 'generate-bulk':
            if not permitted(request, 'invoices.issue'):
                return R.forbidden(message='Invoice issue permission required.', request=request)
            if data.get('confirm') is not True:
                raise ValueError('Review and confirm this IRP action.')
            ids = data.get('ids')
            kind = data.get('kind', 'invoice')
            if kind not in ('invoice', 'credit_note') or not isinstance(ids, list) or not 1 <= len(ids) <= BULK_LIMIT:
                raise ValueError(f'Select between 1 and {BULK_LIMIT} documents.')
            results = []
            for doc_id in ids:
                with org_lock(org.id):
                    obj = _load(org, kind, str(doc_id))
                    if not obj:
                        results.append({'id': str(doc_id), 'ok': False, 'message': 'Document not found.'})
                        continue
                    try:
                        obj = process(org, kind, obj, 'generate', {'category': 'B2B'}, env=env, reg=reg, prefs=prefs)
                        results.append({'id': str(obj.id), 'number': _doc_number(kind, obj), 'ok': True, 'status': obj.einvoice.get('status')})
                        audit(request, 'einvoice', obj.id, 'generate')
                    except (ValueError, ValidationError) as exc:
                        results.append({'id': str(obj.id), 'number': _doc_number(kind, obj), 'ok': False, 'message': str(exc)})
            return R.success(data={'results': results, 'registered': sum(1 for r in results if r['ok'])}, request=request)
        if action not in ('generate', 'recover', 'cancel', 'check-cancellation'):
            raise ValueError('Choose a valid e-invoice action.')
        if not permitted(request, 'invoices.cancel' if action in ('cancel', 'check-cancellation') else 'invoices.issue'):
            return R.forbidden(message='Invoice issue or cancellation permission required.', request=request)
        if data.get('confirm') is not True:
            raise ValueError('Review and confirm this IRP action.')
        kind = data.get('kind', 'invoice')
        if kind not in ('invoice', 'credit_note'):
            raise ValueError('Choose an invoice or a credit note.')
        with org_lock(org.id):
            obj = _load(org, kind, data.get('id'))
            if not obj:
                return R.not_found(message='Document not found.', request=request)
            obj = process(org, kind, obj, action, data, env=env, reg=reg, prefs=prefs)
            get_db().nexease_einvoice_auto.delete_one({'_id': str(obj.id)})
            audit(request, 'einvoice', obj.id, action)
        return R.success(data=public(obj, kind, prefs), request=request)
    except (ValueError, ValidationError) as exc:
        return R.validation_error(message=str(exc), request=request)


@api_login_required
@require_http_methods(['GET'])
def einvoice_pdf(request, invoice_id):
    from django.http import HttpResponse
    from .print_documents import invoice_pdf
    org = request.api_organization
    if not has_einvoice(org) or not permitted(request, 'invoices.read'):
        return R.forbidden(message='E-invoicing requires an active Pro plan and invoice access.', request=request)
    try:
        inv = Invoice.objects(organization=org, id=invoice_id).first()
    except ValidationError:
        inv = None
    if not inv:
        return R.not_found(message='Invoice not found.', request=request)
    response = HttpResponse(invoice_pdf(inv), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="NexEase-Invoice.pdf"'
    return response


# ---------------------------------------------------------------------------------------------
# Automatic IRN (background worker queue)
# ---------------------------------------------------------------------------------------------

def deliver_one():
    """Register one newly issued B2B invoice for a workspace that turned on automatic IRN.

    Only invoices issued after the option was turned on are picked. A failure is parked in
    nexease_einvoice_auto with its message, so the queue never retries blindly; the invoice then waits for
    a person on the E-invoices screen (manual generate clears the parked error).
    """
    from apps.organizations.models import Organization
    env = environment()
    db = get_db()
    for saved in db.nexease_einvoice_settings.find({'auto_generate': True, '_id': {'$regex': f':{re.escape(env)}$'}}).limit(50):
        org = Organization.objects(id=saved['_id'].split(':')[0]).first()
        if not org or not has_einvoice(org):
            continue
        reg = registration(org)
        if saved.get('gstin') != reg.get('gstin'):
            continue
        since = saved.get('auto_since') or datetime.utcnow()
        parked = [x['_id'] for x in db.nexease_einvoice_auto.find({'organization_id': str(org.id)}, {'_id': 1})]
        candidates = Invoice.objects(organization=org, status__in=list(ELIGIBLE), issued_at__gte=since, customer_gstin__ne='',
                                     einvoice__status__exists=False).order_by('issued_at').limit(20)
        for inv in candidates:
            if str(inv.id) in parked or inv.eway_status or (inv.billing_details or {}).get('supply_type') != 'taxable':
                continue
            prefs = {'turnover_10cr': bool(saved.get('turnover_10cr'))}
            try:
                with org_lock(org.id):
                    process(org, 'invoice', inv, 'generate', {'category': 'B2B'}, env=env, reg=reg, prefs=prefs)
            except Exception as exc:  # noqa: BLE001 - parked for a person to review
                message = str(exc) if isinstance(exc, (ValueError, ValidationError)) else 'Automatic IRN failed. Generate it from the E-invoices screen.'
                db.nexease_einvoice_auto.update_one({'_id': str(inv.id)}, {'$set': {'organization_id': str(org.id), 'error': message[:300], 'at': datetime.utcnow()}}, upsert=True)
                log.info('Automatic IRN parked for %s: %s', inv.invoice_number, message)
            return
