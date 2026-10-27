from datetime import datetime
from mongoengine import Document,StringField,IntField,BooleanField,DateTimeField,DictField,ListField
class Plan(Document):
    code=StringField(primary_key=True)
    name=StringField(required=True)
    price_paise=IntField(required=True,min_value=100)
    limits=DictField(default=dict)
    features=ListField(StringField(),default=list)
    published=BooleanField(default=False)
    razorpay_plan_id=StringField(default='')
    gateway_mode=StringField(default='')
    revision=IntField(default=1)
    meta={'collection':'saas_plans'}
class Membership(Document):
    gateway_mode=StringField(default='')
    organization_id=StringField(primary_key=True)
    plan=StringField(default='basic')
    status=StringField(default='inactive')
    start=DateTimeField(default=datetime.utcnow)
    end=DateTimeField(default=datetime.utcnow)
    suspended=BooleanField(default=False)
    subscription_id=StringField(default='')
    limits=DictField(default=dict)
    features=ListField(StringField(),default=list)
    updated_at=DateTimeField(default=datetime.utcnow)
    meta={'collection':'saas_memberships'}
class Checkout(Document):
    subscription_id=StringField(primary_key=True)
    organization_id=StringField(required=True)
    plan=StringField(required=True)
    price_paise=IntField(required=True)
    limits=DictField(default=dict)
    features=ListField(StringField(),default=list)
    mode=StringField(required=True)
    status=StringField(default='created')
    created_at=DateTimeField(default=datetime.utcnow)
    meta={'collection':'saas_checkouts','indexes':['organization_id']}
class PlatformOwner(Document):
    email=StringField(primary_key=True)
    password=StringField(required=True)
    totp_secret=StringField(required=True)
    active=BooleanField(default=True)
    generation=IntField(default=0)
    last_counter=IntField(default=-1)
    meta={'collection':'saas_owners'}
class OwnerAudit(Document):
    actor=StringField(required=True)
    action=StringField(required=True)
    organization_id=StringField(default='')
    reason=StringField(default='')
    details=DictField(default=dict)
    at=DateTimeField(default=datetime.utcnow)
    meta={'collection':'saas_owner_audit','indexes':['-at','organization_id']}
class AIProposal(Document):
    organization_id=StringField(required=True)
    user_id=StringField(required=True)
    request_key=StringField(required=True)
    kind=StringField(default='')
    data=DictField(default=dict)
    state=StringField(default='preparing')
    result=DictField(default=dict)
    warnings=ListField(StringField(),default=list)
    created_at=DateTimeField(default=datetime.utcnow)
    meta={'collection':'saas_ai_proposals','indexes':[{'fields':['organization_id','request_key'],'unique':True}]}
