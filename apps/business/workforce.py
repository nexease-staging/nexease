"""Workforce overview, full-register exports and private payslip downloads."""
from io import BytesIO, StringIO
import csv, re
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import date
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .views import permitted, workbook_response
from .models import BusinessRecord as Record
from .schema import SCHEMAS
from .print_documents import payslip_pdf

def binary(blob,mime,name):
    r=HttpResponse(blob,content_type=mime);r['Content-Disposition']='attachment; filename="'+name+'"';r['Cache-Control']='no-store';return r

@api_login_required
@require_http_methods(['GET'])
def overview(request):
    org=request.api_organization;data={}
    if permitted(request,'payroll.read'):
        data.update(employees=Record.objects(organization=org,kind='employees',data__active=True).count(),pending_leave=Record.objects(organization=org,kind='leave_requests',data__status='requested').count(),draft_payruns=Record.objects(organization=org,kind='payruns',data__status='draft').count())
    if permitted(request,'labour.read'):
        today=date.today().isoformat()
        data.update(sites=Record.objects(organization=org,kind='sites',data__active=True).count(),assignments=Record.objects(organization=org,kind='assignments',data__status='active',data__start_date__lte=today,data__end_date__gte=today).count(),pending_timesheets=Record.objects(organization=org,kind='timesheets',data__status='draft').count())
    if not data:return R.forbidden(message='Workforce permission required.',request=request)
    return R.success(data=data,request=request)

@api_login_required
@require_http_methods(['GET'])
def report(request,kind):
    if kind not in SCHEMAS or SCHEMAS[kind]['permission'] not in ('labour','payroll'):return R.not_found(message='Unknown workforce report.',request=request)
    if not permitted(request,SCHEMAS[kind]['permission']+'.read'):return R.forbidden(message='Permission denied.',request=request)
    try:
        fmt=request.GET.get('format','xlsx')
        if fmt not in ('xlsx','csv','pdf'):raise ValueError('Choose Excel, CSV or PDF.')
        fields=SCHEMAS[kind]['fields'];org=request.api_organization
        employees={str(e.id):e.data.get('name','') for e in Record.objects(organization=org,kind='employees')}
        sites={str(e.id):e.data.get('name','') for e in Record.objects(organization=org,kind='sites')}
        rows=[['Record ID']+[f['label'] for f in fields.values()]]
        for r in Record.objects(organization=org,kind=kind).order_by('created_at'):
            values=[]
            for k,f in fields.items():
                v=r.data.get(k,'')
                if f['type'] in ('employees','sites'):v=(employees if f['type']=='employees' else sites).get(str(v),v)
                values.append(v)
            rows.append([str(r.id)]+values)
        if fmt=='xlsx':return workbook_response({SCHEMAS[kind]['label'][:31]:rows},'NexEase-'+kind)
        if fmt=='csv':
            out=StringIO();writer=csv.writer(out)
            for row in rows:writer.writerow([("'"+str(v)) if str(v).lstrip().startswith(('=','+','-','@')) else v for v in row])
            return binary('\ufeff'+out.getvalue(),'text/csv; charset=utf-8','NexEase-'+kind+'.csv')
        # Vertical record cards keep wide registers readable, without dropping columns.
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from xml.sax.saxutils import escape
        styles=getSampleStyleSheet();out=BytesIO();story=[Paragraph(escape(SCHEMAS[kind]['label']),styles['Title'])]
        for row in rows[1:]:
            table=Table([[Paragraph(escape(str(k)),styles['Normal']),Paragraph(escape(str(v)),styles['Normal'])] for k,v in zip(rows[0],row)],colWidths=[190,320])
            table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.2,colors.lightgrey)]));story += [table,Spacer(1,20)]
        if len(rows)==1:story.append(Paragraph('No records.',styles['Normal']))
        SimpleDocTemplate(out).build(story)
        return binary(out.getvalue(),'application/pdf','NexEase-'+kind+'.pdf')
    except (ValueError,ValidationError) as e:return R.validation_error(message=str(e),request=request)

@api_login_required
@require_http_methods(['GET'])
def payslips(request,run_id):
    if not permitted(request,'payroll.read'):return R.forbidden(message='Payroll read permission required.',request=request)
    try:
        run=Record.objects(organization=request.api_organization,kind='payruns',id=run_id).first()
        if not run:return R.not_found(message='Payroll not found.',request=request)
        if run.data['status'] not in ('approved','paid'):raise ValueError('Approve payroll before downloading payslips for distribution.')
        eid=request.GET.get('employee_id')
        if eid:
            row=next((r for r in run.data['rows'] if r['employee_id']==eid),None)
            if not row:return R.not_found(message='Employee not in this payroll.',request=request)
            return binary(payslip_pdf(request.api_organization,run,row),'application/pdf','Payslip-'+run.key+'-'+eid+'.pdf')
        out=BytesIO()
        with ZipFile(out,'w',ZIP_DEFLATED) as archive:
            for row in run.data['rows']:
                code=re.sub(r'[^a-zA-Z0-9_-]','_',row['employee'].get('code','employee'))[:60]
                archive.writestr(code+'-'+row['employee_id']+'-'+run.key+'.pdf',payslip_pdf(request.api_organization,run,row))
        return binary(out.getvalue(),'application/zip','Payslips-'+run.key+'.zip')
    except (ValueError,ValidationError) as e:return R.validation_error(message=str(e),request=request)
