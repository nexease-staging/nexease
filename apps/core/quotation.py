"""Public quotation inbox: durable outbox, bounded inputs and server-side recipient."""
import os, uuid
from datetime import datetime
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from mongoengine.connection import get_db
from apps.business.views import payload
from apps.saas.security import rate
from apps.core.services.api_response_service import APIResponseService as R

@require_POST
def quotation(request):
    try:
        if len(request.body)>12000:raise ValueError('Message is too long.')
        from apps.accounts.login_rate_limit_service import LoginRateLimitService
        rate('quotation:'+str(LoginRateLimitService.get_client_ip(request)),5,3600)
        p=payload(request)
        if p.get('website'):raise ValueError('Unable to accept this request.')
        if p.get('consent') is not True:raise ValueError('Please agree to be contacted about this enquiry.')
        d={}
        for key,limit in [('name',100),('email',254),('phone',30),('business',200),('service',100),('message',4000)]:
            value=p.get(key,'')
            if not isinstance(value,str) or len(value)>limit:raise ValueError('Invalid '+key)
            d[key]=value.strip()
        if not d['name'] or not d['message']:raise ValueError('Enter your name and requirements.')
        validate_email(d['email'])
        key=str(uuid.uuid4())
        get_db().nexease_quotations.insert_one({'_id':key,**d,'status':'pending','attempts':0,'created_at':datetime.utcnow()})
        return R.success(data={'reference':key},message='Enquiry received. NexEase will contact you.',request=request)
    except (ValueError,ValidationError) as e:return R.validation_error(message=str(e),request=request)

def deliver_one():
    from datetime import timedelta
    from pymongo import ReturnDocument
    from django.core.mail import EmailMessage
    from django.conf import settings
    from django.core.mail import get_connection
    db=get_db().nexease_quotations;now=datetime.utcnow()
    # SMTP acknowledgement is not an exactly-once protocol. Ambiguous sends
    # remain visible for review rather than automatically duplicating emails.
    item=db.find_one_and_update({'status':{'$in':['pending','retry']},'attempts':{'$lt':3},'$or':[{'next_at':{'$exists':False}},{'next_at':{'$lte':now}}]}, {'$set':{'status':'sending','started_at':now},'$inc':{'attempts':1}},return_document=ReturnDocument.AFTER)
    if not item:return
    try:
        if os.getenv('EMAIL_MODE','development')!='production':raise ValueError('Production email is not enabled.')
        recipient=os.getenv('CONTACT_EMAIL','nexease.contact@gmail.com')
        validate_email(recipient)
        body='\n'.join(k.title()+': '+item[k] for k in ('name','email','phone','business','service','message'))+'\nReference: '+item['_id']
        sent=EmailMessage(subject='NexEase quotation enquiry',body=body,to=[recipient],reply_to=[item['email']],connection=get_connection(timeout=30)).send(fail_silently=False)
        if sent!=1:raise ValueError('Email provider did not accept the enquiry.')
        db.update_one({'_id':item['_id']},{'$set':{'status':'sent','sent_at':datetime.utcnow()},'$unset':{'last_error':''}})
    except Exception as exc:
        db.update_one({'_id':item['_id']},{'$set':{'status':'failed' if item['attempts']>=3 else 'retry','next_at':now+timedelta(minutes=5),'last_error':type(exc).__name__}})
