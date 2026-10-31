from .numbering import incoming
"""Direct draft billing; invoice creation does not imply stock dispatch."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError,NotUniqueError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.authorization.services import AuthorizationService
from apps.sales.models import Customer,Invoice,InvoiceItem
from apps.products.models import Product,Category
from apps.inventory.models import Inventory,Warehouse
from apps.business.views import payload,audit
from apps.business.payroll import amount,money
from apps.core.services.notification_service import NotificationService

def text(d,k,required=False,limit=200):
    value=d.get(k,'')
    if not isinstance(value,str) or len(value)>limit:raise ValueError(k+' is invalid.')
    value=value.strip()
    if required and not value:raise ValueError(k+' is required.')
    return value

@api_login_required
@require_http_methods(['POST'])
def direct_invoice(request):
    org=request.api_organization;user=request.api_user
    if not AuthorizationService.has_permission(user,'invoices.create'):return R.forbidden(message='Permission denied.',request=request)
    try:
        p=payload(request);number=incoming(org,'Invoice',text(p,'invoice_number',False,50));c=p.get('customer');items=p.get('items');warehouse_id=p.get('warehouse_id')
        if not isinstance(c,dict) or not isinstance(items,list) or not 1<=len(items)<=100:raise ValueError('Customer and 1–100 line items are required.')
        if Invoice.objects(organization=org,invoice_number=number).first():raise ValueError('Invoice number already exists.')
        when=datetime.fromisoformat(text(p,'invoice_date',True));due=datetime.fromisoformat(p['due_date']) if p.get('due_date') else None
        if due and due<when:raise ValueError('Due date precedes invoice date.')
        code=text(c,'code',False,50).upper();name=text(c,'name',True)
        customer=Customer.objects(organization=org,id=c['id'],is_active=True).first() if c.get('id') else (Customer.objects(organization=org,code=code).first() if code else None)
        if c.get('id') and not customer:raise ValueError('Selected customer is not available.')
        if not customer and not code:code=incoming(org,'Customer','')
        if not customer and not AuthorizationService.has_permission(user,'customers.create'):raise PermissionError('Creating a new customer requires customers.create.')
        for x in items:
            if not text(x,'sku',False,50):x['sku']='AUTO-'+uuid4().hex[:12].upper()
            if not x.get('unit'):x['unit']='PCS'
        sku_keys=[text(x,'sku',True,50).upper() for x in items]
        if len(sku_keys)!=len(set(sku_keys)):raise ValueError('Combine duplicate SKUs into a single line.')
        normalized=[]
        for raw in items:
            sku=text(raw,'sku',True,50).upper();itemname=text(raw,'name',True);unit=text(raw,'unit',True,30)
            product=Product.objects(organization=org,sku=sku).first()
            if product and not product.is_active:raise ValueError('Inactive product: '+sku)
            if not product and not AuthorizationService.has_permission(user,'products.create'):raise PermissionError('Creating a new product requires products.create.')
            qty=amount(raw.get('quantity'), 'Quantity');price=amount(raw.get('unit_price'),'Price');rate=amount(raw.get('tax_rate',0),'Tax rate','100');discount=amount(raw.get('discount',0),'Discount')
            if any(v!=v.quantize(Decimal('.01')) for v in [price,rate,discount]):raise ValueError('Price, tax rate and discount support at most two decimal places.')
            if qty<=0 or qty!=qty.quantize(Decimal('.01')):raise ValueError('Quantity must be positive with at most two decimal places.')
            subtotal=Decimal(money(qty*price))
            if discount>subtotal:raise ValueError('Discount exceeds line amount.')
            tax=Decimal(money((subtotal-discount)*rate/100))
            item_type=product.item_type if product else raw.get('item_type','goods');hsn=product.hsn_code if product else raw.get('hsn_code','')
            Product(item_type=item_type,hsn_code=hsn).clean()
            normalized.append(dict(item_type=item_type,hsn_code=hsn,item_name=itemname,sku=sku,name=itemname,unit=unit,product=product,quantity=qty,unit_price=price,tax_rate=rate,discount=discount,line_subtotal=subtotal,line_tax=tax,line_total=subtotal-discount+tax))
        warehouse=Warehouse.objects(organization=org,id=warehouse_id,is_active=True).first() if warehouse_id else None
        if warehouse_id and not warehouse:raise ValueError('Warehouse not found.')
        if customer and not customer.is_active:raise ValueError('Customer is inactive.')
        if 'billing_details' in p:
            from .billing import clean_details
            preview=[]
            for n in normalized:
                prod=n['product'] or Product(name=n['name'],unit=n['unit'],item_type=n['item_type'],hsn_code=n['hsn_code'])
                preview.append(InvoiceItem(product=prod,item_name=n['name'],item_type=n['item_type'],hsn_code=n['hsn_code'],unit=n['unit'],quantity=n['quantity'],unit_price=n['unit_price'],tax_rate=n['tax_rate']))
            clean_details(p['billing_details'],org,preview)
        warnings=['Direct invoice without sales order. Stock dispatch requires separate review.'];new_records=[]
        if not customer:
            customer=Customer(organization=org,code=code,name=name,billing_address=text(c,'address',limit=500),gstin=text(c,'gstin',limit=20),state=text(c,'state',limit=100),email=text(c,'email',limit=254) or None,phone=text(c,'phone',limit=30)).save();new_records.append('Customer '+code)
        invoice_items=[]
        for n in normalized:
            product=n.pop('product');sku=n.pop('sku');name=n.pop('name');unit=n.pop('unit')
            if not product:
                category=Category.objects(organization=org,name='Pending review').first()
                if not category:category=Category(organization=org,name='Pending review',description='Automatically created masters awaiting review.').save()
                product=Product(organization=org,sku=sku,name=name,unit=unit,item_type=n['item_type'],hsn_code=n['hsn_code'],category=category,selling_price=n['unit_price']).save();new_records.append('Product '+sku)
            if warehouse and product.item_type=="goods":
                stock=Inventory.objects(organization=org,warehouse=warehouse,product=product).first();available=stock.quantity-stock.reserved_quantity if stock else Decimal(0)
                if available<n['quantity']:warnings.append('Insufficient available stock: '+sku)
            invoice_items.append(InvoiceItem(product=product,unit=unit,**n))
        from .billing import clean_details,settings
        details={**settings(org),**clean_details(p['billing_details'],org,invoice_items)} if 'billing_details' in p else {}
        goods=any(i.item_type=='goods' for i in invoice_items)
        total=sum(x.line_total for x in invoice_items)
        invoice=Invoice(billing_details=details,organization=org,invoice_number=number,customer=customer,invoice_date=when,due_date=due,items=invoice_items,subtotal=sum(x.line_subtotal for x in invoice_items),tax_amount=sum(x.line_tax for x in invoice_items),discount_amount=sum(x.discount for x in invoice_items),total_amount=total,balance_due=total,billing_name=customer.name,billing_address=customer.billing_address,billing_state=customer.state,customer_gstin=customer.gstin,created_by=user,notes=('DIRECT ENTRY: pending stock review. ' if goods else 'SERVICE INVOICE: no stock movement. ')+text(p,'notes',limit=700),direct_entry=True,stock_review_required=goods).save()
        audit(request,'direct_invoice',invoice.id,'create')
        NotificationService.create_notification(organization=org,recipient=user,notification_type='SYSTEM',title='Review direct invoice '+invoice.invoice_number,message=(' '.join(warnings)+' New records: '+', '.join(new_records))[:1000],severity='WARNING',resource_type='invoice',resource_id=str(invoice.id),action_url='/invoices')
        return R.success(data={'id':str(invoice.id),'invoice_number':invoice.invoice_number,'status':'DRAFT','warnings':warnings,'new_records':new_records},request=request)
    except PermissionError as e:return R.forbidden(message=str(e),request=request)
    except (ValueError,TypeError,ValidationError,NotUniqueError) as e:return R.validation_error(message=str(e),request=request)
