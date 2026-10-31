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
        from .billing import tax_heads
        linked_ids={d.get('source_reference') for d in records}
        hsn_rows=[['Invoice','Date','Party type','Goods / Service','HSN/SAC','Unit','Quantity','GST rate','Taxable value','CGST','SGST/UTGST','IGST']]
        for inv in Invoice.objects(organization=org,status__in=['ISSUED','PARTIALLY_PAID','PAID'],invoice_date__gte=datetime.combine(start,time.min),invoice_date__lte=datetime.combine(end,time.max)):
            d=inv.billing_details
            if not d.get('tax_reviewed') or str(inv.id) in linked_ids:continue
            cg,sg,ig=tax_heads(inv)
            records.append(dict(document_number=inv.invoice_number,date=inv.invoice_date.date().isoformat(),direction='outward',supply=d['supply_type'],party_gstin=inv.customer_gstin or '',party_name=inv.billing_name,place_of_supply=d.get('place_of_supply',''),hsn=', '.join(sorted({i.hsn_code for i in inv.items})),taxable=str(inv.total_amount-inv.tax_amount),cgst=str(cg),sgst=str(sg),igst=str(ig),cess='0',itc_eligible=False,source_reference=str(inv.id)))
            for line in inv.items:
                tax=Decimal(str(line.line_tax));lc=Decimal(money(tax/2)) if d.get('supplier_state')==d.get('place_of_supply') else Decimal(0)
                hsn_rows.append([inv.invoice_number,inv.invoice_date.date().isoformat(),'B2B' if inv.customer_gstin else 'B2C',line.item_type,line.hsn_code,line.unit,float(line.quantity),float(line.tax_rate),float(line.line_subtotal-line.discount),float(lc),float(tax-lc) if lc else 0,float(tax) if d.get('supplier_state')!=d.get('place_of_supply') else 0])
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
        hsn_summary=[['Party type','Goods / Service','HSN/SAC','Unit','GST rate','Quantity','Taxable value','CGST','SGST/UTGST','IGST']]
        hsn_groups={}
        for row in hsn_rows[1:]:
            key=(row[2],row[3],row[4],row[5],row[7]);values=hsn_groups.setdefault(key,[Decimal(0)]*5)
            for i,column in enumerate((6,8,9,10,11)):values[i]+=Decimal(str(row[column]))
        for key,values in hsn_groups.items():hsn_summary.append([*key,*map(float,values)])
        outward=[['GSTR-3B review row','Taxable / supply value','CGST','SGST/UTGST','IGST','Cess']]
        mapped={};mapping={'taxable':'3.1(a) Taxable outward','nil_rated':'3.1(c) Nil rated / exempt','exempt':'3.1(c) Nil rated / exempt','non_gst':'3.1(e) Non-GST outward','zero_rated':'3.1(b) Zero rated outward'}
        for d in records:
            if d['direction']!='outward' or d['supply'] not in mapping:continue
            values=mapped.setdefault(mapping[d['supply']],[Decimal(0)]*5)
            for i,k in enumerate(('taxable','cgst','sgst','igst','cess')):values[i]+=amount(d.get(k,0))
        for key,values in sorted(mapped.items()):outward.append([key,*map(float,values)])
        notes=[['NexEase '+form+' preparation workpaper'],['Period: '+start.isoformat()+' to '+end.isoformat()],['NOT a filed return, complete statutory computation, or GST portal import file.'],['Classified issued invoices are included automatically. Legacy/unclassified documents require GST review. Manual entries with a matching source ID replace that invoice in this workpaper; enter the complete reviewed amount.'],['Source documents are shown separately; they are NOT silently added to reviewed totals.'],['Credit/debit notes, advances, amendments, reverse charge, imports/exports, ITC reversals/reclaims and prior-year adjustments require separate reconciliation.'],['GSTR-9 additionally requires filed-return and annual ITC reconciliation.'],['Use the current official GST utility for validation and submission.'],['https://tutorial.gst.gov.in/userguide/returns/GSTR_1.htm'],['https://tutorial.gst.gov.in/userguide/returns/GSTR3B.htm'],['https://tutorial.gst.gov.in/userguide/returns/Manual_gstr9.htm']]
        return workbook_response({'Read me':notes,'Reviewed register':register,'Reviewed summary':summary,'Source reconciliation':sources,'HSN SAC invoice lines':hsn_rows,'HSN SAC summary':hsn_summary,'3B outward review':outward},'NexEase-'+form+'-'+start.isoformat())
    except (ValueError,TypeError) as e:return R.validation_error(message=str(e),request=request)
