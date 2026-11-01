from datetime import datetime
from mongoengine import Document, ReferenceField, StringField, DictField, IntField, DateTimeField
from apps.organizations.models import Organization
from apps.accounts.models import User

class BusinessRecord(Document):
    organization = ReferenceField(Organization, required=True)
    kind = StringField(required=True)
    key = StringField(required=True, max_length=100)
    data = DictField(default=dict)
    revision = IntField(default=1)
    created_by = ReferenceField(User, required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    meta = {'collection':'nexease_business_records','indexes':[{'fields':['organization','kind','key'],'unique':True}, ('organization','kind','-created_at')]}

class BusinessAudit(Document):
    organization = ReferenceField(Organization, required=True)
    actor = ReferenceField(User, required=True)
    kind = StringField(required=True)
    record_id = StringField(required=True)
    action = StringField(required=True)
    details = DictField(default=dict)
    at = DateTimeField(default=datetime.utcnow)
    meta = {'collection':'nexease_business_audit','indexes':[('organization','-at')]}
