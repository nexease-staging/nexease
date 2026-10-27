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
def settings(org,kind):
    d=get_db().nexease_numbering.find_one({'_id':str(org.id)+':'+kind}) or {}
    return {'kind':kind,'mode':d.get('mode','automatic'),'prefix':d.get('prefix',REGISTRY[kind][1]),'next':d.get('next',1),'padding':d.get('padding',5)}
def allocate(org,kind,manual=None):
    db=get_db();key=str(org.id)+':'+kind
    try:db.nexease_numbering.update_one({'_id':key},{'$setOnInsert':{'next':1,'mode':'automatic','prefix':REGISTRY[kind][1],'padding':5}},upsert=True)
    except DuplicateKeyError:pass
    for attempt in range(1000):
        if manual is not None:
            number=str(manual).strip().upper()
            if not re.fullmatch(r'[A-Z0-9][A-Z0-9._/-]{0,49}',number):raise ValueError('Use 1–50 letters, digits, dots, slashes, underscores or hyphens.')
        else:
            d=db.nexease_numbering.find_one_and_update({'_id':key},{'$inc':{'next':1}},return_document=ReturnDocument.BEFORE);number=d['prefix']+str(d['next']).zfill(d['padding'])
        try:db.nexease_number_reservations.insert_one({'_id':key+':'+number});return number
        except DuplicateKeyError:
            if manual is not None:raise ValueError('Number is already used or reserved.')
    raise ValueError('Choose a higher next number.')
def incoming(org,kind,value):
    p=choice.get()
    if p and p.get('kind')==kind:return str(p.get('number','')).strip().upper() if p.get('mode')=='manual' else 'TEMP-'+uuid4().hex[:20]
    return value or allocate(org,kind)
def apply_number(sender,document,**kwargs):
    p=choice.get();kind=sender.__name__;org=getattr(document,'organization',None)
    if not document._created or not p or p.get('kind')!=kind or kind not in REGISTRY or not org:return
    field=REGISTRY[kind][0]
    if field not in document._fields:return
    try:
        for _ in range(100):
            number=allocate(org,kind,p.get('number','') if p.get('mode')=='manual' else None)
            if not sender.objects(organization=org,**{field:number}).first():setattr(document,field,number);return
            if p.get('mode')=='manual':raise ValueError('Number already exists in this organisation.')
        raise ValueError('Choose a higher next number.')
    except ValueError as e:raise ValidationError(str(e))
signals.pre_save.connect(apply_number,weak=False)
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
        try:return self.get_response(request)
        finally:choice.reset(token)
