"""Read-only source suggestions. Missing tax heads and ITC are never silently assumed."""
from datetime import date, datetime, time
from django.views.decorators.http import require_GET
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.business.models import BusinessRecord
from apps.business.views import permitted
from apps.sales.models import Invoice
from apps.purchasing.models import VendorBill
from apps.business.billing import tax_heads


def candidate(document, kind, linked):
    invoice=kind=='invoice'
    details=document.billing_details if invoice else {}
    reviewed=invoice and bool(details.get('tax_reviewed')) and details.get('supply_type') in ('taxable','exempt','nil_rated','non_gst')
    cg,sg,ig=tax_heads(document) if reviewed else (None,None,None)
    number=document.invoice_number if invoice else document.bill_number
    day=document.invoice_date if invoice else document.bill_date
    data=dict(document_number=number,date=day.date().isoformat(),direction='outward' if invoice else 'inward',
        supply=details.get('supply_type','') if reviewed else '',
        party_gstin=(document.customer_gstin if invoice else document.supplier_gstin) or '',
        party_name=(document.billing_name if invoice else document.supplier_name) or '',
        place_of_supply=details.get('place_of_supply','') if invoice else '',
        hsn=', '.join(sorted({getattr(i,'hsn_code','') for i in document.items if getattr(i,'hsn_code','')})),
        taxable=f'{document.total_amount-document.tax_amount:.2f}',
        cgst=f'{cg:.2f}' if cg is not None else '',sgst=f'{sg:.2f}' if sg is not None else '',igst=f'{ig:.2f}' if ig is not None else '',
        cess='0',itc_eligible=False,source_reference=str(document.id),
        note='Source '+kind+'; aggregate tax '+f'{document.tax_amount:.2f}'+'. Confirm classification and tax heads. ITC has not been confirmed.')
    missing=[k for k in ('supply','party_name','place_of_supply','cgst','sgst','igst') if data[k]=='']
    return dict(id=str(document.id),kind=kind,number=number,data=data,missing=missing,
        linked=str(document.id) in linked,automatically_in_report=reviewed and str(document.id) not in linked)


@api_login_required
@require_GET
def review_sources(request):
    if not permitted(request,'taxation.read'):return R.forbidden(message='Taxation read permission required.',request=request)
    try:
        start=date.fromisoformat(request.GET.get('from',''));end=date.fromisoformat(request.GET.get('to',''))
        if end<start or (end-start).days>366:raise ValueError('Choose a period of at most 367 days.')
    except ValueError:return R.validation_error(message='Enter a valid date range of at most 367 days.',request=request)
    org=request.api_organization
    linked={r.data.get('source_reference') for r in BusinessRecord.objects(organization=org,kind='gst_adjustments').only('data')}
    rows=[];total=0
    for model,kind,dt,statuses in [(Invoice,'invoice','invoice_date',['ISSUED','PARTIALLY_PAID','PAID']),(VendorBill,'bill','bill_date',['POSTED','PARTIALLY_PAID','PAID'])]:
        query=model.objects(organization=org,status__in=statuses,**{dt+'__gte':datetime.combine(start,time.min),dt+'__lte':datetime.combine(end,time.max)}).order_by('-'+dt)
        total+=query.count()
        for document in query.limit(max(0,200-len(rows))) if len(rows)<200 else []:rows.append(candidate(document,kind,linked))
    return R.success(data={'sources':rows,'total':total,'truncated':total>len(rows),
        'notice':'Source suggestions are not filed returns. Classified issued sales are already included in workpapers. Purchases need tax-head and ITC review; credit/debit notes and amendments require separate review.'},request=request)
