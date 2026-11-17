"""Encrypted partner email outbox. Ambiguous SMTP sends are held for review."""
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.core import signing
from django.core.mail import EmailMessage, get_connection
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from mongoengine.connection import get_db
from pymongo import ReturnDocument
from .security import cipher


def partner_url():
    base = str(settings.FRONTEND_BASE_URL).rstrip('/')
    if not base.startswith('https://'):
        raise ValueError('Secure frontend URL is required for partner email.')
    return base + '/partners'


def issue_link(partner, purpose, welcome=False):
    if purpose not in ('verify', 'reset'):
        raise ValueError('Invalid link purpose.')
    base = partner_url()
    nonce = secrets.token_urlsafe(32)
    digest = hashlib.sha256(nonce.encode()).hexdigest()
    now = datetime.utcnow()
    identity = {'_id': partner['_id'], 'generation': partner['generation'], 'email': partner['email']}
    if welcome:
        identity.update({'email_verified': {'$ne': True}, '$or': [
            {'verify_digest': {'$exists': False}}, {'verify_expires': {'$lte': now}}]})
    result = get_db().saas_partners.update_one(identity, {'$set': {
        purpose+'_digest': digest, purpose+'_expires': now + timedelta(hours=1)}})
    if not result.matched_count:
        return None
    token = signing.dumps({'id': partner['_id'], 'email': partner['email'], 'nonce': nonce,
                           'purpose': purpose, 'generation': partner['generation']}, salt='partner-links-v1')
    return digest, base + '?' + urlencode({'token': token, 'purpose': purpose})


def request_link(partner, purpose):
    key = cipher()
    link = issue_link(partner, purpose)
    if not link:
        raise ValueError('Partner account changed. Sign in again.')
    digest, url = link
    now = datetime.utcnow()
    message = ('Verify your email' if purpose=='verify' else 'Reset your password') + ' using this link. It expires in one hour.\n' + url
    get_db().partner_mail.insert_one({'_id':digest,'partner_id':partner['_id'],'email':partner['email'],'purpose':purpose,'generation':partner['generation'],
        'payload':key.encrypt(json.dumps({'subject':'NexEase partner '+purpose,'message':message}).encode()).decode(),'status':'pending','created_at':now})


def consume(token, purpose, password=None):
    from django.core.signing import BadSignature
    try:data=signing.loads(token,salt='partner-links-v1',max_age=3600)
    except BadSignature:raise ValueError('This link is invalid or expired. Request another.')
    if purpose not in ('verify','reset') or data.get('purpose')!=purpose:raise ValueError('Invalid link purpose.')
    update={'$unset':{purpose+'_digest':'',purpose+'_expires':''}}
    if purpose=='reset':
        if not isinstance(password,str) or len(password)>128:raise ValueError('Invalid password.')
        validate_password(password)
        update['$set']={'password':make_password(password)}
        update['$inc']={'generation':1}
    else:update['$set']={'email_verified':True}
    row=get_db().saas_partners.find_one_and_update({'_id':data.get('id'),'email':data.get('email'),'generation':data.get('generation'),
        'status':{'$in':['pending','approved']},purpose+'_digest':hashlib.sha256(str(data.get('nonce','')).encode()).hexdigest(),purpose+'_expires':{'$gt':datetime.utcnow()}},update)
    if not row:raise ValueError('This link was used, replaced or expired. Request another.')


def queue_welcome(partner_id, email):
    get_db().partner_mail.update_one({'_id':'welcome:'+partner_id},{'$setOnInsert':{
        'partner_id':partner_id,'email':email,'purpose':'welcome','status':'pending','created_at':datetime.utcnow(),
    }},upsert=True)


def welcome_message(partner):
    message = 'Your partner application has been received. Commissions are 20% on the first subscription payment and 10% on renewals, excluding GST, subject to review.'
    link = issue_link(partner, 'verify', welcome=True) if not partner.get('email_verified') else None
    if link:
        message += '\n\nOpen this link and select Confirm to verify your email. The link expires in one hour.\n' + link[1]
    elif not partner.get('email_verified'):
        message += '\n\nUse your latest verification email, or sign in to request a fresh link.'
    return {'subject': 'Welcome to NexEase partners', 'message': message + '\n\nPartner portal\n' + partner_url()}


def deliver_one(send=None):
    db=get_db()
    if send is None and settings.EMAIL_MODE!='production':return False
    row=db.partner_mail.find_one_and_update({'status':'pending'},{'$set':{'status':'sending','claimed_at':datetime.utcnow()}},sort=[('created_at',1)],return_document=ReturnDocument.AFTER)
    if not row:return False
    try:
        partner=db.saas_partners.find_one({'_id':row['partner_id'],'email':row['email'],'status':{'$in':['pending','approved']}})
        if not partner or (row['purpose']!='welcome' and (partner.get('generation')!=row['generation'] or partner.get(row['purpose']+'_digest')!=row['_id'] or partner.get(row['purpose']+'_expires',datetime.min)<=datetime.utcnow())):
            db.partner_mail.update_one({'_id':row['_id']},{'$set':{'status':'cancelled'},'$unset':{'payload':''}});return True
        data=(welcome_message(partner) if row['purpose']=='welcome' else json.loads(cipher().decrypt(row['payload'].encode())))
        if send:send(row['email'],data)
        else:
            count=EmailMessage(data['subject'],data['message'],from_email='NexEase <nexease.contact@gmail.com>',to=[row['email']],connection=get_connection(timeout=30)).send(fail_silently=False)
            if count!=1:raise ValueError('Email acceptance not confirmed')
        db.partner_mail.update_one({'_id':row['_id']},{'$set':{'status':'sent'},'$unset':{'payload':''}})
    except Exception as exc:
        db.partner_mail.update_one({'_id':row['_id']},{'$set':{'status':'review_required','error_type':type(exc).__name__}})
    return True
