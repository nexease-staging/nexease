import os,time,hmac,hashlib,base64,struct,json
from functools import wraps
from datetime import datetime,timedelta
from cryptography.fernet import Fernet
from django.contrib.auth.hashers import check_password
from mongoengine.connection import get_db
from pymongo import ReturnDocument
from mongoengine.errors import ValidationError
from .models import PlatformOwner,OwnerAudit
from apps.core.services.api_response_service import APIResponseService as R

def cipher():
 key=os.getenv('OWNER_ENCRYPTION_KEY','')
 if not key:raise ValueError('OWNER_ENCRYPTION_KEY is not configured.')
 return Fernet(key.encode())

def totp(secret,counter):
 key=base64.b32decode(secret+'='*((8-len(secret)%8)%8));d=hmac.new(key,struct.pack('>Q',counter),hashlib.sha1).digest();o=d[-1]&15
 return str((struct.unpack('>I',d[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)

def verify_totp(owner,code):
 if not isinstance(code,str) or len(code)!=6:return False
 secret=cipher().decrypt(owner.totp_secret.encode()).decode();now=int(time.time())//30
 for c in [now-1,now,now+1]:
  if c>owner.last_counter and hmac.compare_digest(totp(secret,c),code):
   return bool(PlatformOwner.objects(email=owner.email,last_counter__lt=c).update_one(set__last_counter=c))
 return False

def rate(key,maximum=10,seconds=300):
 bucket=int(time.time())//seconds
 d=get_db().saas_rate.find_one_and_update({'_id':key+':'+str(bucket)},{'$inc':{'n':1},'$set':{'expires':datetime.utcnow()+timedelta(seconds=seconds*2)}},upsert=True,return_document=ReturnDocument.AFTER)
 get_db().saas_rate.create_index('expires',expireAfterSeconds=0)
 if d['n']>maximum:raise ValueError('Too many attempts. Try again later.')

def log(owner,action,org='',reason='',details=None):
 OwnerAudit(actor=str(owner),action=action,organization_id=str(org),reason=reason[:500],details=details or {}).save()

def current_owner(request):
 s=request.session.get('nexease_owner',{})
 if not s or time.time()-s.get('at',0)>1800:return None
 o=PlatformOwner.objects(email=s.get('email'),active=True,generation=s.get('generation')).first()
 return o

def owner_required(fn):
 @wraps(fn)
 def wrapped(request,*args,**kwargs):
  owner=current_owner(request)
  if not owner:return R.unauthorized(message='Owner sign-in with authenticator code is required.',request=request)
  request.platform_owner=owner
  try:return fn(request,*args,**kwargs)
  except (ValueError,TypeError,KeyError,ValidationError) as e:return R.validation_error(message=str(e),request=request)
 return wrapped
