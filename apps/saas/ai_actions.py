"""Explicit AI action allowlist. All mutations still use normal domain validators."""
import json
from apps.business.schema import SCHEMAS
RECORD_KINDS={'employee':'employees','site':'sites','assignment':'assignments','attendance':'attendance','timesheet':'timesheets','leave_request':'leave_requests'}
EXTRA_PERMISSIONS={k:SCHEMAS[v]['permission']+'.manage' for k,v in RECORD_KINDS.items()}
EXTRA_PERMISSIONS.update(category='products.create',product='products.create',purchase_order='purchase_orders.create')
EXTRA_FIELDS=sorted({k for kind in RECORD_KINDS.values() for k in SCHEMAS[kind]['fields']}|{'name','category_id','item_type','hsn_code','unit','sku','selling_price','cost_price','supply_type','place_of_supply','po_number','po_date','service_from','service_to','site_name'})

def confirm_extended(request,proposal):
    from apps.business.views import records
    from apps.products.services.product_api_service import ProductAPIService
    from apps.products.services.category_api_service import CategoryAPIService
    from apps.business.views import audit
    from .models import AIProposal
    from apps.core.services.api_response_service import APIResponseService as R
    d=proposal.data;f=d['fields'];kind=d['kind'];org=request.api_organization
    if kind in RECORD_KINDS:
        target=RECORD_KINDS[kind];body={}
        for k,spec in SCHEMAS[target]['fields'].items():
            v=f.get(k,'')
            if spec['type']=='boolean':
                if v not in ('true','false',''):raise ValueError(k+' must be true or false.')
                v=v=='true'
            body[k]=v
        if kind in ('employee','site') and not body.get('code'):body['code']='AI-'+str(proposal.id)[-16:].upper()
    elif kind=='category':body={'name':f.get('name',''),'description':f.get('description','')}
    else:body={k:f.get(k,'') for k in ('name','sku','category_id','unit','description','selling_price','cost_price','item_type','hsn_code')};body['item_type']=body['item_type'] or 'goods';body['sku']=body['sku'] or 'AI-'+str(proposal.id)[-16:].upper()
    if not AIProposal.objects(id=proposal.id,state='review').update_one(set__state='committing'):raise ValueError('Proposal already processing.')
    try:
        if kind in RECORD_KINDS:
            original=request.body;request._body=json.dumps({'data':body}).encode()
            try:response=records(request,kind=target)
            finally:request._body=original
            result=json.loads(response.content)
            if response.status_code>=400:raise ValueError(result.get('error',{}).get('message','Entry validation failed.'))
            saved=result.get('data',{})
        else:
            service=CategoryAPIService.create_category if kind=='category' else ProductAPIService.create_product
            obj=service(organization=org,payload=body);saved={'id':str(obj.id),'name':obj.name};audit(request,kind,obj.id,'ai-create')
        proposal.reload();proposal.state='saved';proposal.result=saved;proposal.save()
    except Exception as e:
        # Do not blindly retry a potentially partially committed creation.
        proposal.reload();proposal.state='needs_review';proposal.result={'message':str(e),'reference':body.get('code',body.get('sku',body.get('name','')))};proposal.save()
    return R.success(data={'id':str(proposal.id),'state':proposal.state,'kind':kind,'data':proposal.data,'warnings':proposal.warnings,'result':proposal.result},request=request)
