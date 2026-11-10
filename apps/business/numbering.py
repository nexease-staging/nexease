"""Atomic organisation-scoped reference sequences. Internal IDs are unchanged."""
import json,re
from contextvars import ContextVar
from uuid import uuid4
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from mongoengine import signals,ValidationError
from mongoengine.connection import get_db
from django.http import JsonResponse
choice=ContextVar('nexease_number_choice',default=None)
REGISTRY={'Employee':('code','EMP-'),'Site':('code','SITE-'),'Customer':('code','CUST-'),'Supplier':('code','SUP-'),'Product':('sku','SKU-'),'Warehouse':('code','WH-'),'SalesOrder':('so_number','SO-'),'Invoice':('invoice_number','INV-'),'PurchaseOrder':('po_number','PO-'),'GoodsReceipt':('grn_number','GRN-'),'VendorBill':('bill_number','BILL-'),'CustomerPayment':('payment_number','PAY-'),'SupplierPayment':('payment_number','SPAY-'),'SalesReturn':('return_number','SR-'),'PurchaseReturn':('return_number','PR-'),'CreditNote':('credit_note_number','CN-'),'VendorDebitNote':('debit_note_number','DN-'),'StockTransfer':('transfer_number','TRF-'),'BankTransfer':('transfer_number','BT-'),'BankTransaction':('transaction_number','BTX-'),'BankStatement':('statement_number','BST-'),'JournalEntry':('journal_number','JE-')}
# Reservations are never recycled: a failed save must remain explainable.
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from mongoengine.base import get_document
owned = ContextVar('nexease_owned_numbers', default=None)


def financial_year(value=None):
    value = value or datetime.now(timezone.utc)
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if isinstance(value, datetime) and value.tzinfo is not None:
        value = value.astimezone(ZoneInfo('Asia/Kolkata'))
    if not isinstance(value, date):
        raise ValueError('A valid document date is required.')
    year = value.year if value.month >= 4 else value.year - 1
    return f'{year}-{str(year + 1)[-2:]}'


def settings(org, kind, document_date=None):
    db = get_db(); key = str(org.id) + ':' + kind
    d = db.nexease_numbering.find_one({'_id': key}) or {}
    annual = kind == 'Invoice' and d.get('financial_year', False) is True
    fy = financial_year(document_date) if annual else None
    counter = db.nexease_numbering.find_one({'_id': key + ':' + fy}) if annual else d
    prefix = d.get('prefix', REGISTRY[kind][1]); padding = d.get('padding', 5)
    next_number = (counter or {}).get('next', 1)
    rendered = prefix + (fy[2:] + '/' if annual else '')
    return {'kind': kind, 'mode': d.get('mode', 'automatic'), 'prefix': prefix,
            'next': next_number, 'padding': padding, 'financial_year': annual,
            'period': fy, 'preview': rendered + str(next_number).zfill(padding)}


def configure(org, kind, mode, prefix, next_number, padding, annual=False):
    if (kind not in REGISTRY or mode not in ('automatic', 'manual')
        or not re.fullmatch(r'[A-Z0-9._/-]{0,20}', prefix)
        or not 1 <= next_number <= 999999999 or not 1 <= padding <= 12
        or not isinstance(annual, bool) or (annual and kind != 'Invoice')):
        raise ValueError('Invalid numbering settings.')
    from apps.saas.entitlements import org_lock
    with org_lock(org.id):
        db = get_db(); key = str(org.id) + ':' + kind
        update = {'$set': {'mode': mode, 'prefix': prefix, 'padding': padding, 'financial_year': annual}}
        if not annual:
            update['$max'] = {'next': next_number}
        db.nexease_numbering.update_one({'_id': key}, update, upsert=True)
        if annual:
            db.nexease_numbering.update_one({'_id': key + ':' + financial_year()},
                                           {'$max': {'next': next_number}}, upsert=True)


def allocate(org, kind, manual=None, document_date=None):
    db = get_db(); key = str(org.id) + ':' + kind
    try:
        db.nexease_numbering.update_one({'_id': key}, {'$setOnInsert': {
            'next': 1, 'mode': 'automatic', 'prefix': REGISTRY[kind][1], 'padding': 5}}, upsert=True)
    except DuplicateKeyError:
        pass
    config = settings(org, kind, document_date)
    counter_key = key + ':' + config['period'] if config['financial_year'] else key
    if config['financial_year']:
        try:
            db.nexease_numbering.update_one({'_id': counter_key}, {'$setOnInsert': {'next': 1}}, upsert=True)
        except DuplicateKeyError:
            pass
    for attempt in range(1000):
        if manual is not None:
            number = str(manual).strip().upper()
            if not re.fullmatch(r'[A-Z0-9][A-Z0-9._/-]{0,49}', number):
                raise ValueError('Use 1–50 letters, digits, dots, slashes, underscores or hyphens.')
        else:
            d = db.nexease_numbering.find_one_and_update({'_id': counter_key}, {'$inc': {'next': 1}}, return_document=ReturnDocument.BEFORE)
            number = config['prefix'] + (config['period'][2:] + '/' if config['financial_year'] else '') + str(d['next']).zfill(config['padding'])
        reservation_id = key + ':' + number
        try:
            db.nexease_number_reservations.insert_one({'_id': reservation_id,
                'organization_id': str(org.id), 'kind': kind, 'number': number,
                'financial_year': financial_year(document_date) if kind == 'Invoice' else None,
                'mode': 'manual' if manual is not None else 'automatic',
                'status': 'reserved', 'reserved_at': datetime.now(timezone.utc)})
        except DuplicateKeyError:
            if manual is not None:
                raise ValueError('Number is already used or reserved.')
            continue
        # Older documents may predate reservations. Do not offer their numbers again.
        if kind == 'Invoice':
            existing = get_document(kind).objects(organization=org, **{REGISTRY[kind][0]: number}).first()
            if existing:
                db.nexease_number_reservations.update_one({'_id': reservation_id}, {'$set': {
                    'status': 'attached', 'document_id': str(existing.id), 'legacy': True}})
                if manual is not None:
                    raise ValueError('Number already exists in this organisation.')
                continue
        owned.set({**(owned.get() or {}), reservation_id: True})
        return number
    raise ValueError('Choose a higher next number.')


def incoming(org, kind, value, document_date=None):
    p = choice.get()
    if p and p.get('kind') == kind:
        return str(p.get('number', '')).strip().upper() if p.get('mode') == 'manual' else 'TEMP-' + uuid4().hex[:20]
    if kind == 'Invoice':
        normalized = str(value or '').strip().upper()
        if normalized and (owned.get() or {}).get(str(org.id) + ':' + kind + ':' + normalized):
            return normalized
        return allocate(org, kind, value or None, document_date=document_date)
    return value or allocate(org, kind)


def apply_number(sender, document, **kwargs):
    p = choice.get(); kind = sender.__name__; org = getattr(document, 'organization', None)
    if not document._created or kind not in REGISTRY or not org:
        return
    if kind != 'Invoice' and (not p or p.get('kind') != kind):
        return
    field = REGISTRY[kind][0]
    if field not in document._fields:
        return
    when = getattr(document, 'invoice_date', None) if kind == 'Invoice' else None
    current = getattr(document, field, '') or ''
    reservation_id = str(org.id) + ':' + kind + ':' + current
    # Retrying validation on the same object must not allocate another number.
    if getattr(document, '_nexease_reserved_number', None) == current:
        return
    if kind == 'Invoice' and not (p and p.get('kind') == kind) and (owned.get() or {}).get(reservation_id):
        document._nexease_reserved_number = current
        return
    manual = (p.get('number', '') if p.get('mode') == 'manual' else None) if p and p.get('kind') == kind else current or None
    try:
        for _ in range(100):
            number = allocate(org, kind, manual, document_date=when)
            if not sender.objects(organization=org, **{field: number}).first():
                setattr(document, field, number)
                document._nexease_reserved_number = number
                return
            if manual is not None:
                raise ValueError('Number already exists in this organisation.')
        raise ValueError('Choose a higher next number.')
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def attach_number(sender, document, created=False, **kwargs):
    if not created or sender.__name__ not in REGISTRY:
        return
    kind = sender.__name__; org = getattr(document, 'organization', None)
    if kind == 'Invoice':
        from apps.core.services.invoice_creation_request import mark_invoice_write
        mark_invoice_write(document)
    if kind != 'Invoice' and not getattr(document, '_nexease_reserved_number', None):
        return
    field = REGISTRY[kind][0]
    if not org or field not in document._fields:
        return
    number = getattr(document, field)
    key = str(org.id) + ':' + kind + ':' + number
    get_db().nexease_number_reservations.update_one({'_id': key}, {'$set': {
        'organization_id': str(org.id), 'kind': kind, 'number': number,
        'status': 'attached', 'document_id': str(document.id), 'attached_at': datetime.now(timezone.utc)}}, upsert=True)
    remaining = dict(owned.get() or {}); remaining.pop(key, None); owned.set(remaining)


signals.pre_save.connect(apply_number, weak=False)
signals.post_save.connect(attach_number, weak=False)
class NumberingMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        p=None
        try:
            if request.headers.get('X-NexEase-Numbering'):
                p=json.loads(request.headers['X-NexEase-Numbering'])
                if not isinstance(p,dict) or p.get('kind') not in REGISTRY or p.get('mode') not in ('automatic','manual'):raise ValueError()
        except (ValueError,TypeError):return JsonResponse({'message':'Invalid numbering preference.'},status=400)
        token=choice.set(p)
        reservation_token=owned.set({})
        try:return self.get_response(request)
        finally:
            choice.reset(token)
            owned.reset(reservation_token)
