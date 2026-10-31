from .numbering import incoming
from datetime import datetime
from decimal import Decimal
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError,NotUniqueError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.authorization.services import AuthorizationService
from apps.products.models import Product,Category
from apps.purchasing.models import Supplier,PurchaseOrder,PurchaseOrderItem,VendorBill,VendorBillItem
from apps.business.views import payload,audit
from apps.business.direct_entry import text
from apps.business.payroll import amount,money
from apps.core.services.notification_service import NotificationService

@api_login_required
@require_http_methods(['POST'])
def quick_purchase(request):
    org=request.api_organization;user=request.api_user
    try:
        p=payload(request);kind=p.get('kind');is_bill=kind=='bill'
        if kind not in ('bill','purchase_order'):raise ValueError('Choose bill or purchase_order.')
        permission='bills.create' if is_bill else 'purchase_orders.create'
        if not AuthorizationService.has_permission(user,permission):raise PermissionError('Permission denied.')
        number=incoming(org,'VendorBill' if is_bill else 'PurchaseOrder',text(p,'number',False,50));when=datetime.fromisoformat(text(p,'date',True));supplier_data=p.get('supplier');raw_items=p.get('items')
        if not isinstance(supplier_data,dict) or not isinstance(raw_items,list) or not 1<=len(raw_items)<=100:raise ValueError('Supplier and 1–100 lines required.')
        code=text(supplier_data,'code',True,50).upper();name=text(supplier_data,'name',True)
        supplier=Supplier.objects(organization=org,code=code).first()
        if supplier and not supplier.is_active:raise ValueError('Supplier is inactive.')
        if not supplier and not AuthorizationService.has_permission(user,'suppliers.create'):raise PermissionError('suppliers.create is required for a new supplier.')
        model=VendorBill if is_bill else PurchaseOrder;numberfield='bill_number' if is_bill else 'po_number'
        if model.objects(organization=org,**{numberfield:number}).first():raise ValueError('Document number already exists.')
        sku_keys=[text(x,'sku',True,50).upper() for x in raw_items]
        if len(sku_keys)!=len(set(sku_keys)):raise ValueError('Combine duplicate SKUs into a single line.')
        normalized=[]
        for raw in raw_items:
            sku=text(raw,'sku',True,50).upper();name_p=text(raw,'name',True);unit=text(raw,'unit',True,30)
            product=Product.objects(organization=org,sku=sku).first()
            if product and not product.is_active:raise ValueError('Product is inactive.')
            if not product and not AuthorizationService.has_permission(user,'products.create'):raise PermissionError('products.create is required for a new product.')
            item_type=product.item_type if product else raw.get('item_type','goods');hsn=product.hsn_code if product else raw.get('hsn_code','')
            Product(item_type=item_type,hsn_code=hsn).clean()
            qty=amount(raw.get('quantity'));price=amount(raw.get('unit_price'));rate=amount(raw.get('tax_rate',0),maximum='100');discount=amount(raw.get('discount',0))
            if any(v!=v.quantize(Decimal('.01')) for v in [price,rate,discount]):raise ValueError('Price, tax rate and discount support at most two decimal places.')
            if qty<=0 or qty!=qty.quantize(Decimal('.01')):raise ValueError('Quantity must be positive with at most two decimals.')
            sub=Decimal(money(qty*price))
            if discount>sub:raise ValueError('Discount exceeds line subtotal.')
            tax=Decimal(money((sub-discount)*rate/100))
            normalized.append((product,sku,name_p,unit,item_type,hsn,dict(quantity=qty,unit_price=price,tax_rate=rate,discount=discount),sub,tax,sub-discount+tax))
        created=[]
        if not supplier:
            supplier=Supplier(organization=org,code=code,name=name,address=text(supplier_data,'address',limit=500),gstin=text(supplier_data,'gstin',limit=20)).save();created.append('Supplier '+code)
        items=[];subtotal=tax_total=discount_total=total=Decimal(0)
        for product,sku,name_p,unit,item_type,hsn,values,sub,tax,line in normalized:
            if not product:
                category=Category.objects(organization=org,name='Pending review').first() or Category(organization=org,name='Pending review').save()
                product=Product(organization=org,sku=sku,name=name_p,unit=unit,item_type=item_type,hsn_code=hsn,category=category,cost_price=values['unit_price']).save();created.append('Product '+sku)
            values.update(product=product)
            if is_bill:values.update(line_subtotal=sub,line_tax=tax,line_total=line);items.append(VendorBillItem(**values))
            else:values.update(subtotal=sub,tax_amount=tax,total=line);items.append(PurchaseOrderItem(**values))
            subtotal+=sub;tax_total+=tax;discount_total+=values['discount'];total+=line
        kwargs=dict(organization=org,supplier=supplier,items=items,subtotal=subtotal,tax_amount=tax_total,discount_amount=discount_total,total_amount=total,created_by=user,notes='Quick entry: review source document, masters and receipt.')
        if is_bill:kwargs.update(bill_number=number,bill_date=when,balance_due=total,supplier_name=supplier.name,supplier_gstin=supplier.gstin,supplier_address=supplier.address)
        else:kwargs.update(po_number=number,order_date=when.date())
        doc=model(**kwargs).save();audit(request,kind,doc.id,'create')
        NotificationService.create_notification(organization=org,recipient=user,notification_type='SYSTEM',title='Review '+(doc.bill_number if is_bill else doc.po_number),message=('Quick purchase entry. '+('Bill has no purchase order; review receipt and accounting. ' if is_bill else '')+'New masters: '+', '.join(created))[:1000],severity='WARNING',resource_type=kind,resource_id=str(doc.id),action_url='/vendor-bills' if is_bill else '/purchase-orders')
        return R.success(data={'number':doc.bill_number if is_bill else doc.po_number,'id':str(doc.id),'status':'DRAFT','new_records':created},request=request)
    except PermissionError as e:return R.forbidden(message=str(e),request=request)
    except (ValueError,TypeError,ValidationError,NotUniqueError) as e:return R.validation_error(message=str(e),request=request)
