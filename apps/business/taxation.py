"""Review workpapers, deliberately not GST portal payloads or automatic filings."""
from datetime import datetime,date,time
from decimal import Decimal
from django.views.decorators.http import require_http_methods
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.business.views import permitted,workbook_response
from apps.business.models import BusinessRecord as Record
from apps.sales.models import Invoice,CreditNote
from apps.purchasing.models import VendorBill,VendorDebitNote
from apps.business.payroll import amount,money

@api_login_required
@require_http_methods(['GET'])
def gst_report(request):
    if not permitted(request,'taxation.read'):return R.forbidden(message='Permission denied.',request=request)
    try:
        start=date.fromisoformat(request.GET.get('from',''));end=date.fromisoformat(request.GET.get('to',''))
        if end<start or (end-start).days>366:raise ValueError('Choose a period of at most 367 days.')
        org=request.api_organization;form=request.GET.get('form','GSTR-1')
        if form not in ['GSTR-1','GSTR-3B','GSTR-9']:raise ValueError('Unknown report.')
        records=[x.data for x in Record.objects(organization=org,kind='gst_adjustments') if start.isoformat()<=x.data['date']<=end.isoformat()]
        register=[['Document','Date','Direction','Category','Party GSTIN','Party','Place of supply','HSN/SAC','Value','CGST','SGST','IGST','Cess','ITC reviewed','Source reference']]
        for d in records:register.append([d['document_number'],d['date'],d['direction'],d['supply'],d['party_gstin'],d['party_name'],d['place_of_supply'],d['hsn'],*[float(amount(d.get(k,0))) for k in ['taxable','cgst','sgst','igst','cess']],'Yes' if d['itc_eligible'] else 'No',d['source_reference']])
        sources=[['Type','ID','Number','Date','Party','Taxable','Aggregate tax','Total','Review status']]
        linked={d.get('source_reference') for d in records}
        specs=[(Invoice,'invoice_date','invoice_number','billing_name',['ISSUED','PARTIALLY_PAID','PAID']),(VendorBill,'bill_date','bill_number','supplier_name',['POSTED','PARTIALLY_PAID','PAID']),(CreditNote,'credit_note_date','credit_note_number',None,['ISSUED']),(VendorDebitNote,'debit_note_date','debit_note_number',None,['ISSUED'])]
        for model,dt,num,party,statuses in specs:
            for x in model.objects(organization=org,status__in=statuses,**{dt+'__gte':datetime.combine(start,time.min),dt+'__lte':datetime.combine(end,time.max)}):
                sources.append([model.__name__,str(x.id),getattr(x,num),getattr(x,dt).date().isoformat(),getattr(x,party,'') if party else '',float(x.total_amount-x.tax_amount),float(x.tax_amount),float(x.total_amount),'Linked to register' if str(x.id) in linked else 'NEEDS CLASSIFICATION'])
        summary=[['Direction','Supply category','Value','CGST','SGST','IGST','Cess','ITC eligibility']]
        groups={}
        for d in records:
            key=(d['direction'],d['supply'],d['itc_eligible']);v=groups.setdefault(key,[Decimal(0)]*5)
            for i,k in enumerate(['taxable','cgst','sgst','igst','cess']):v[i]+=amount(d.get(k,0))
        for (direction,supply,itc),v in groups.items():summary.append([direction,supply,*map(float,v),'Reviewed eligible' if itc else 'Not confirmed'])
        notes=[['NexEase '+form+' preparation workpaper'],['Period: '+start.isoformat()+' to '+end.isoformat()],['NOT a filed return, complete statutory computation, or GST portal import file.'],['Existing invoices store aggregate tax. Reviewer must classify place of supply, tax heads, HSN/SAC and ITC in GST review register.'],['Source documents are shown separately; they are NOT silently added to reviewed totals.'],['Credit/debit notes, advances, amendments, reverse charge, imports/exports, ITC reversals/reclaims and prior-year adjustments require separate reconciliation.'],['GSTR-9 additionally requires filed-return and annual ITC reconciliation.'],['Use the current official GST utility for validation and submission.'],['https://tutorial.gst.gov.in/userguide/returns/GSTR_1.htm'],['https://tutorial.gst.gov.in/userguide/returns/GSTR3B.htm'],['https://tutorial.gst.gov.in/userguide/returns/Manual_gstr9.htm']]
        return workbook_response({'Read me':notes,'Reviewed register':register,'Reviewed summary':summary,'Source reconciliation':sources},'NexEase-'+form+'-'+start.isoformat())
    except (ValueError,TypeError) as e:return R.validation_error(message=str(e),request=request)
