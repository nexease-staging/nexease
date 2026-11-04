"""Public calendar: general GST rules plus explicit owner-maintained deadline overrides."""
import json,os
from datetime import datetime,date,timedelta
from zoneinfo import ZoneInfo
from django.views.decorators.http import require_http_methods
from apps.core.services.api_response_service import APIResponseService as R
IST=ZoneInfo('Asia/Kolkata')
GSTR1='https://tutorial.gst.gov.in/downloads/news/creative_faqs_on_gstr1a_fo_cr25785.pdf'
QRMP='https://tutorial.gst.gov.in/offlineutilities/returns/QRMP_Advisory.pdf'
GSTR3='https://sgst.uk.gov.in/return-payment/'

def calendar_rows(today=None):
    today=today or datetime.now(IST).date();rows=[]
    # Two monthly cycles remain visible, including elapsed dates in the current month.
    for offset in (0,1):
        month=today.month+offset;year=today.year+(month-1)//12;month=(month-1)%12+1
        period=(date(year,month,1)-timedelta(days=1)).strftime('%Y-%m')
        for name,day,scheme,url in [('GSTR-1',11,'Monthly',GSTR1),('GSTR-3B',20,'Monthly',GSTR3)]:
            rows.append(dict(id=name+'-'+period,title=name,category='GST',period=period,applies_to=scheme+' filers',due_at=f'{year:04}-{month:02}-{day:02}T23:59:59+05:30',source_url=url,status='standard',note='General rule; verify official extensions and applicability.'))
    # Quarter-specific rows, never monthly recurrence for a quarterly return.
    for delta in range(5):
        index=today.month-1+delta;year=today.year+index//12;month=index%12+1
        if month not in (1,4,7,10):continue
        end=date(year,month,1)-timedelta(days=1);period=f'{end.year}-Q{(end.month-1)//3+1}'
        for title,day,applies in [('GSTR-1',13,'QRMP quarterly filers'),('GSTR-3B',22,'QRMP 22nd-day state group (including Maharashtra)'),('GSTR-3B',24,'QRMP 24th-day state group')]:
            rows.append(dict(id=f'{title}-{period}-{day}',title=title,category='GST',period=period,applies_to=applies,due_at=f'{year:04}-{month:02}-{day:02}T23:59:59+05:30',source_url=QRMP,status='standard',note='Quarterly general rule; use only your applicable state group.'))
    # Explicit IDs replace baseline rows, permitting official extensions without silent rollover.
    extra=json.loads(os.getenv('NEXEASE_DEADLINES_JSON','[]'))
    if not isinstance(extra,list) or len(extra)>200:raise ValueError('Invalid calendar configuration.')
    for row in extra:
        required=('id','title','category','period','applies_to','due_at','source_url','verified_on')
        if not isinstance(row,dict) or any(not isinstance(row.get(k),str) or not row[k] or len(row[k])>500 for k in required):raise ValueError('Invalid calendar row.')
        due=datetime.fromisoformat(row['due_at']);date.fromisoformat(row['verified_on'])
        if due.tzinfo is None or not row['source_url'].startswith('https://'):raise ValueError('Calendar dates need a timezone and HTTPS source.')
        clean={k:row[k] for k in required};clean.update(status='verified',note=str(row.get('note',''))[:500]);rows=[r for r in rows if r['id']!=clean['id']];rows.append(clean)
    return sorted(rows,key=lambda x:datetime.fromisoformat(x['due_at']))

@require_http_methods(['GET'])
def deadlines(request):
    try:return R.success(data={'timezone':'Asia/Kolkata','rows':calendar_rows(),'notice':'General GST dates are guidance, not confirmation of current extensions. Only rows with an owner-verified source are labelled verified. TDS, payroll, ITR and ROC dates appear after the owner adds verified, applicable deadlines.'},request=request)
    except (ValueError,TypeError):return R.validation_error(message='Compliance calendar configuration needs review. Contact NexEase.',request=request)
