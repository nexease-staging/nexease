"""Per-user authenticated document sender; never accept a caller supplied From address."""
import os, smtplib, ssl
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken
from django.core.mail.backends.smtp import EmailBackend
from mongoengine.connection import get_db

PROVIDERS={'gmail':('smtp.gmail.com',587),'outlook':('smtp.office365.com',587),'yahoo':('smtp.mail.yahoo.com',587)}

def cipher():
    secret=os.getenv('MAILBOX_ENCRYPTION_KEY','')
    if not secret:
        raise ValueError('The owner must configure MAILBOX_ENCRYPTION_KEY before connecting mailboxes.')
    try:return Fernet(secret.encode())
    except ValueError:raise ValueError('MAILBOX_ENCRYPTION_KEY must be a valid Fernet key.')

def scope(user,org):return {'user_id':str(user.id),'organization_id':str(org.id)}
def get_mailbox(user,org):return get_db().user_mailboxes.find_one(scope(user,org))
def status(user,org):
    row=get_mailbox(user,org)
    connected=bool(row and row['email']==user.email.strip().lower())
    from .email_verification import verified
    return {'verified':verified(user),'connected':connected,'email':user.email,'provider':row['provider'] if connected else '', 'configured':bool(os.getenv('MAILBOX_ENCRYPTION_KEY'))}

def connect(user,org,provider,password):
    if provider not in PROVIDERS:raise ValueError('Choose Gmail, Microsoft 365 or Yahoo.')
    if not isinstance(password,str) or not 1<=len(password)<=512:raise ValueError('Enter an app password or a provider-approved SMTP credential.')
    if provider in ('gmail','yahoo'):password=password.replace(' ','')
    encrypted=cipher().encrypt(password.encode()).decode()
    email=user.email.strip().lower();host,port=PROVIDERS[provider]
    try:
        with smtplib.SMTP(host,port,timeout=20) as smtp:
            smtp.ehlo();smtp.starttls(context=ssl.create_default_context());smtp.ehlo();smtp.login(email,password)
    except (smtplib.SMTPException,OSError):
        raise ValueError('Mailbox authentication failed. Check the registered email, provider and app password. Some Microsoft accounts require OAuth and cannot use this connection.')
    get_db().user_mailboxes.create_index([('organization_id',1),('user_id',1)],unique=True)
    get_db().user_mailboxes.update_one(scope(user,org),{'$set':{'email':email,'provider':provider,'secret':encrypted,'updated_at':datetime.utcnow()}},upsert=True)
    return status(user,org)

def disconnect(user,org):get_db().user_mailboxes.delete_one(scope(user,org))

def delivery_options(user,org):
    row=get_mailbox(user,org)
    if not row or row['email']!=user.email.strip().lower():
        from .email_verification import verified
        from django.conf import settings
        if not verified(user):raise ValueError('Verify your email in Settings → My email before sharing documents.')
        return {'from_email':settings.DEFAULT_FROM_EMAIL,'reply_to':[user.email.strip().lower()]}
    try:password=cipher().decrypt(row['secret'].encode()).decode()
    except InvalidToken:raise ValueError('Mailbox credentials cannot be decrypted. Reconnect your mailbox in Settings.')
    host,port=PROVIDERS[row['provider']]
    backend=EmailBackend(alias='user-mailbox',host=host,port=port,username=row['email'],password=password,use_tls=True,use_ssl=False,timeout=30,fail_silently=False)
    return {'from_email':row['email'],'reply_to':[row['email']],'connection':backend}
