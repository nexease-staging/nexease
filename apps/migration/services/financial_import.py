"""Additional migration types. One payment allocation per row, unique reference required."""
from datetime import datetime
from mongoengine.errors import ValidationError
from decimal import Decimal
from apps.business.payroll import amount
from apps.sales.models import Invoice, CustomerPayment
from apps.purchasing.models import PurchaseOrder, VendorBill, SupplierPayment
from apps.finance.models import BankAccount
TYPES={'VENDOR_BILLS','CUSTOMER_PAYMENTS','SUPPLIER_PAYMENTS'}
FIELDS={
 'VENDOR_BILLS':{'purchase_order_number':True,'supplier_invoice_number':True,'bill_date':True,'due_date':False,'notes':False},
 'CUSTOMER_PAYMENTS':{'invoice_number':True,'amount':True,'payment_method':True,'bank_account_id':True,'payment_date':True,'reference_number':True,'notes':False},
 'SUPPLIER_PAYMENTS':{'bill_number':True,'amount':True,'payment_method':True,'bank_account_id':True,'payment_date':True,'reference_number':True,'notes':False},
}
def validate_financial(org,kind,row,seen):
    errors=[];d={}
    try:
        for k,required in FIELDS[kind].items():
            v=str(row.get(k,'') or '').strip()
            if required and not v:raise ValueError(k+' is required.')
            if len(v)>1000:raise ValueError(k+' is too long.')
            d[k]=v
            if k.endswith('_date') and v:datetime.fromisoformat(v)
        key=d.get('reference_number') or d.get('supplier_invoice_number')
        if key in seen:raise ValueError('Duplicate reference in file.')
        seen.add(key)
        if kind=='VENDOR_BILLS':
            po=PurchaseOrder.objects(organization=org,po_number=d['purchase_order_number']).first()
            if not po or po.status!='RECEIVED':raise ValueError('Purchase order must exist and be fully received.')
            if d['due_date'] and d['due_date']<d['bill_date']:raise ValueError('Due date precedes bill date.')
            exists=VendorBill.objects(organization=org,supplier=po.supplier,supplier_invoice_number=d['supplier_invoice_number']).first()
            if exists:return {'valid':False,'errors':[{'field':None,'code':'ALREADY_EXISTS','message':'Vendor bill exists.'}],'normalized':d}
        else:
            model=Invoice if kind=='CUSTOMER_PAYMENTS' else VendorBill
            number='invoice_number' if kind=='CUSTOMER_PAYMENTS' else 'bill_number'
            doc=model.objects(organization=org,**{number:d[number]}).first()
            statuses=['ISSUED','PARTIALLY_PAID'] if kind=='CUSTOMER_PAYMENTS' else ['POSTED','PARTIALLY_PAID']
            if not doc or doc.status not in statuses:raise ValueError('Referenced document must be posted/issued and unpaid.')
            value=amount(d['amount'])
            if value<=0 or value>doc.balance_due:raise ValueError('Payment amount exceeds balance or is zero.')
            if d['payment_method'] not in ('CASH','BANK_TRANSFER','UPI','CHEQUE','CARD','OTHER'):raise ValueError('Invalid payment method.')
            if not BankAccount.objects(organization=org,id=d['bank_account_id'],is_active=True).first():raise ValueError('Active bank account ID not found.')
            pm=CustomerPayment if kind=='CUSTOMER_PAYMENTS' else SupplierPayment
            if pm.objects(organization=org,reference_number=key).first():return {'valid':False,'errors':[{'field':None,'code':'ALREADY_EXISTS','message':'Payment reference exists.'}],'normalized':d}
    except (ValueError,TypeError,ValidationError) as e:errors.append({'field':None,'code':'INVALID_ROW','message':str(e)})
    return {'valid':not errors,'errors':errors,'normalized':d}

def import_financial(user,org,kind,d):
    from apps.purchasing.services.vendor_bill_service import VendorBillService
    from apps.purchasing.services.supplier_payment_service import SupplierPaymentService
    from apps.sales.services.payment_service import PaymentService
    # Revalidate after queued jobs; never trust a saved validation snapshot.
    result=validate_financial(org,kind,d,set())
    if not result['valid']:raise ValueError('; '.join(x['message'] for x in result['errors']))
    if kind=='VENDOR_BILLS':
        po=PurchaseOrder.objects(organization=org,po_number=d['purchase_order_number']).first()
        return VendorBillService.generate_from_purchase_order(user=user,organization=org,purchase_order=po,supplier_invoice_number=d['supplier_invoice_number'],bill_date=datetime.fromisoformat(d['bill_date']),due_date=datetime.fromisoformat(d['due_date']) if d.get('due_date') else None,notes=d.get('notes',''))
    kwargs=dict(user=user,organization=org,amount=d['amount'],payment_method=d['payment_method'],bank_account=BankAccount.objects(organization=org,id=d['bank_account_id']).first(),payment_date=datetime.fromisoformat(d['payment_date']),reference_number=d['reference_number'],notes=d.get('notes',''))
    if kind=='CUSTOMER_PAYMENTS':return PaymentService.record_invoice_payment(invoice=Invoice.objects(organization=org,invoice_number=d['invoice_number']).first(),**kwargs)
    return SupplierPaymentService.record_bill_payment(vendor_bill=VendorBill.objects(organization=org,bill_number=d['bill_number']).first(),**kwargs)
