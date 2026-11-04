"""Existing-product stock actions. Tenant-scoped resolution, permissions and ledger writes."""
from decimal import Decimal, InvalidOperation

def resolve_stock(org, data):
    from apps.products.models import Product
    from apps.inventory.models import Warehouse
    f=data['fields']; warnings=[]; questions=[]
    products=Product.objects(organization=org,is_active=True)
    if f.get('product_id'):
        matches=list(products.filter(id=f['product_id']))
    elif f.get('sku'):
        matches=list(products.filter(sku__iexact=f['sku'].strip()))
    else:
        name=f.get('product_name') or f.get('name') or (data['items'][0].get('name','') if len(data['items'])==1 else '')
        f['product_name']=name
        matches=list(products.filter(name__iexact=name.strip())) if name else []
        if not matches and name:matches=list(products.filter(sku__iexact=name.strip()))
    if len(matches)==1:
        product=matches[0]
        if (f.get('sku') and f['sku'].strip().casefold()!=product.sku.casefold()) or (f.get('product_name') and f['product_name'].strip().casefold() not in (product.name.casefold(),product.sku.casefold())):
            questions.append('Product details conflict. Choose one exact existing product name or SKU again.')
        if product.item_type=='service':questions.append('This product is a service and cannot hold stock.')
        else:f.update(product_id=str(product.id),product_name=product.name,sku=product.sku)
    else:
        f['product_id']='';questions.append('Choose an exact existing product name or SKU; no product will be created.')
    warehouses=Warehouse.objects(organization=org,is_active=True)
    if f.get('warehouse_id'):matches=list(warehouses.filter(id=f['warehouse_id']))
    elif f.get('warehouse_name'):matches=list(warehouses.filter(name__iexact=f['warehouse_name'].strip())) or list(warehouses.filter(code__iexact=f['warehouse_name'].strip()))
    else:matches=list(warehouses.limit(2))
    if len(matches)==1:
        f.update(warehouse_id=str(matches[0].id),warehouse_name=matches[0].name)
        warnings.append('Warehouse: '+matches[0].name+'. Verify before confirming.')
    else:
        f['warehouse_id']='';questions.append('Choose the warehouse for this stock movement.')
    try:
        qty=Decimal(f.get('quantity_change') or '')
        if not qty.is_finite() or qty==0 or qty!=qty.quantize(Decimal('.01')):raise ValueError()
    except (ValueError,InvalidOperation):questions.append('Supply a nonzero stock change with at most two decimal places (positive adds, negative removes).')
    data['questions']=questions
    return warnings

def confirm_stock(request,proposal):
    from apps.inventory.models import Inventory,Product,Warehouse,StockMovement
    from apps.inventory.services.inventory_service import InventoryService
    from apps.saas.models import AIProposal
    from apps.core.services.api_response_service import APIResponseService as R
    org=request.api_organization;data=proposal.data;f=data['fields']
    resolve_stock(org,data)
    if data['questions']:raise ValueError(' '.join(data['questions']))
    product=Product.objects(organization=org,id=f['product_id'],is_active=True).first()
    warehouse=Warehouse.objects(organization=org,id=f['warehouse_id'],is_active=True).first()
    InventoryService._check_permission(request.api_user,'inventory.adjust')
    InventoryService._check_organization(request.api_user,org)
    InventoryService._validate_product(product,org);InventoryService._validate_warehouse(warehouse,org)
    qty=Decimal(f['quantity_change'])
    inventory=Inventory.objects(organization=org,product=product,warehouse=warehouse).first()
    if not inventory:
        if qty<0:raise ValueError('Cannot remove stock from an empty warehouse.')
        # Initial row creation follows the same permission as the ordinary inventory screen.
        InventoryService._check_permission(request.api_user,'inventory.create')
    if inventory and inventory.quantity+qty<inventory.reserved_quantity:raise ValueError('Stock cannot fall below reserved quantity.')
    stable=str(proposal.id)
    if StockMovement.objects(organization=org,reference_type='AI_STOCK',reference_id=stable).first():raise ValueError('A stock movement already exists for this request. Check stock history.')
    if not AIProposal.objects(id=proposal.id,state='review').update_one(set__state='committing'):raise ValueError('This request is already processing.')
    try:
        if not inventory:
            inventory=InventoryService.create_inventory(user=request.api_user,organization=org,product=product,warehouse=warehouse,quantity=0)
        inventory=InventoryService.adjust_quantity(user=request.api_user,organization=org,inventory_id=str(inventory.id),quantity_change=qty,reference_type='AI_STOCK',reference_id=stable,notes=f.get('notes') or 'AI stock change confirmed by user')
        proposal.reload();proposal.state='saved';proposal.result={'inventory_id':str(inventory.id),'product':product.name,'warehouse':warehouse.name,'change':str(qty),'quantity':str(inventory.quantity),'message':'Stock updated and recorded in the stock ledger.'};proposal.save()
    except Exception:
        proposal.reload();proposal.state='needs_review';proposal.result={'message':'Stock processing was interrupted. Check the ledger before retrying.','reference':stable};proposal.save()
        raise
    return R.success(data={'id':str(proposal.id),'state':proposal.state,'kind':proposal.kind,'data':proposal.data,'warnings':proposal.warnings,'result':proposal.result},request=request)

def parse_stock_command(text):
    """Fast, unambiguous add/remove commands; other language stays with the model."""
    import re
    match=re.fullmatch(r'\s*(add|increase|remove|reduce)\s+(.+?)\s+(\d+(?:\.\d{1,2})?)\s*(?:qty|quantity|units?|pieces?|pcs)?\s+(?:in|to|from)\s+(?:the\s+)?stock(?:\s+(?:at|in)\s+(.+?))?\s*[.!]?\s*',text,re.I)
    if not match:return None
    action,name,qty,warehouse=match.groups()
    if any(x in name.lower() for x in (' and ',' then ',';',' to ')):return None
    if Decimal(qty)<=0:return None
    return {'product_name':name.strip(),'quantity_change':('-' if action.lower() in ('remove','reduce') else '')+qty,'warehouse_name':(warehouse or '').strip()}
