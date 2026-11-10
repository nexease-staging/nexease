import csv
import io
from datetime import datetime
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from mongoengine.connection import get_db
from apps.business.views import payload
from apps.core.services.api_response_service import APIResponseService as R
from .partners import partner_for
from .security import rate, owner_required, verify_totp
from . import partner_mail
from .entitlements import org_lock
from .commissions import rebuild


@require_http_methods(['POST'])
def email_action(request):
    try:
        rate('partner-mail-ip:'+request.META.get('REMOTE_ADDR',''),10)
        data=payload(request);action=data.get('action')
        if action in ('verify','reset'):
            partner_mail.consume(str(data.get('token','')),action,data.get('password'))
            return R.success(data={'message':'Email verified.' if action=='verify' else 'Password changed. Sign in again.'},request=request)
        if action=='send_verification':
            partner=partner_for(request)
            if not partner:return R.unauthorized(message='Sign in to request verification.',request=request)
            if partner.get('email_verified'):return R.success(data={'message':'Email already verified.'},request=request)
            purpose='verify'
        elif action=='forgot_password':
            email=str(data.get('email','')).strip().lower()
            import hashlib
            from django.conf import settings
            from .security import cipher
            cipher()
            if not str(settings.FRONTEND_BASE_URL).startswith('https://'):raise ValueError('Secure frontend URL required.')
            rate('partner-reset-email:'+hashlib.sha256(email.encode()).hexdigest(),3,3600)
            partner=get_db().saas_partners.find_one({'email':email,'password':{'$exists':True},'status':{'$in':['pending','approved']}})
            purpose='reset'
        else:raise ValueError('Invalid email action.')
        if partner:
            if purpose=='verify':rate('partner-mail-account:'+partner['_id'],3,3600)
            partner_mail.request_link(partner,purpose)
        return R.success(data={'message':'If the account is eligible, an email has been queued. Check your inbox.'},request=request)
    except (ValueError,ValidationError) as exc:return R.validation_error(message=' '.join(exc.messages) if isinstance(exc,ValidationError) else str(exc),request=request)


@require_http_methods(['GET'])
def statement(request):
    partner=partner_for(request)
    if not partner or partner['status']!='approved' or not partner.get('email_verified'):
        return R.forbidden(message='Approved partner with verified email required.',request=request)
    db=get_db();scope={'partner_id':partner['_id'],'mode':'live'}
    if db.saas_commissions.count_documents(scope)>10000:return R.validation_error(message='Statement exceeds 10,000 rows. Contact support for an archive export.',request=request)
    out=io.StringIO();writer=csv.writer(out)
    writer.writerow(['Payment','Date UTC','Rate %','Net subscription paise','Net refund paise','Commission paise','Recorded payout paise','Status'])
    def safe(v):
        s='' if v is None else str(v)
        return "'"+s if s.lstrip().startswith(('=','+','-','@','\t','\r')) else s
    payouts={r['commission_id']:r['amount_paise'] for r in db.saas_partner_payouts.find(scope)}
    for row in db.saas_commissions.find(scope).sort([('paid_at',1),('_id',1)]):
        writer.writerow([safe(v) for v in [row['payment_id'],datetime.utcfromtimestamp(row['paid_at']).isoformat(),row['percent'],row.get('net_subscription_paise'),row.get('net_refund_paise'),row.get('amount_paise'),payouts.get(row['_id'],0),row['status']]])
    if request.GET.get('format') == 'pdf':
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        import textwrap
        buffer=io.BytesIO();pdf=canvas.Canvas(buffer,pagesize=A4);y=790
        def header():
            pdf.setFont('Helvetica-Bold',16);pdf.drawString(36,805,'NexEase | Partner statement')
            pdf.setFont('Helvetica',9);pdf.drawString(36,788,'Review only. Recorded payouts are external payments, not bank confirmations.')
        header();y=765
        for line in out.getvalue().splitlines():
            for part in textwrap.wrap(line,100,replace_whitespace=False) or ['']:
                if y<45:pdf.showPage();header();y=765
                pdf.setFont('Helvetica',8);pdf.drawString(36,y,part);y-=12
            y-=5
        pdf.save();response=HttpResponse(buffer.getvalue(),content_type='application/pdf')
        response['Content-Disposition']='attachment; filename="NexEase-partner-statement.pdf"'
        response['Cache-Control']='no-store'
        return response
    response=HttpResponse('\ufeff'+out.getvalue(),content_type='text/csv; charset=utf-8')
    response['Content-Disposition']='attachment; filename="NexEase-partner-statement.csv"'
    response['Cache-Control']='no-store'
    return response


@owner_required
@require_http_methods(['GET','POST'])
def payouts(request):
    db=get_db()
    if request.method=='GET':
        page=max(1,min(100000,int(request.GET.get('page',1))))
        rows=list(db.saas_partner_payouts.find({}, {'_id':0}).sort('recorded_at',-1).skip((page-1)*25).limit(25))
        for row in rows:row['recorded_at']=row['recorded_at'].isoformat()
        return R.success(data={'entries':rows,'page':page},request=request)
    data=payload(request);owner=request.platform_owner
    if not check_password(str(data.get('password','')),owner.password) or not verify_totp(owner,str(data.get('code',''))):raise ValueError('Fresh owner password and authenticator code required.')
    cid=str(data.get('commission_id',''));ref=str(data.get('reference','')).strip();reason=str(data.get('reason','')).strip()
    if not 3<=len(ref)<=120 or not 5<=len(reason)<=500:raise ValueError('Enter the external payment reference and audit reason.')
    row=db.saas_commissions.find_one({'_id':cid})
    if not row:raise ValueError('Commission not found.')
    with org_lock(row['organization_id']):
        old=db.saas_partner_payouts.find_one({'_id':cid})
        if old:
            if old['reference']!=ref:raise ValueError('A payout is already recorded for this commission.')
            return R.success(data={'message':'This payout was already recorded.'},request=request)
        rebuild(row['organization_id'],row['mode'])
        row=db.saas_commissions.find_one({'_id':cid})
        partner=db.saas_partners.find_one({'_id':row['partner_id'],'status':'approved','email_verified':True})
        if not partner or row.get('amount_paise') is None or row['amount_paise']<=0:raise ValueError('Approved verified partner and positive GST-reviewed commission required.')
        if data.get('amount_paise')!=row['amount_paise']:raise ValueError('Amount changed or does not match the reviewed commission. Review again.')
        db.saas_partner_payouts.insert_one({'_id':cid,'commission_id':cid,'partner_id':row['partner_id'],'mode':row['mode'],
            'amount_paise':row['amount_paise'],'reference':ref,'reason':reason,'recorded_by':owner.email,'recorded_at':datetime.utcnow()})
    return R.success(data={'message':'External payout recorded. NexEase did not initiate a bank transfer.'},request=request)
