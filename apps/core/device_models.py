from datetime import datetime
from mongoengine import Document, StringField, ReferenceField, DateTimeField
from apps.accounts.models import User
from apps.organizations.models import Organization

class NotificationDevice(Document):
    token = StringField(required=True, unique=True, max_length=4096)
    user = ReferenceField(User, required=True)
    organization = ReferenceField(Organization, required=True)
    registered_at = DateTimeField(default=datetime.utcnow)
    refreshed_at = DateTimeField(default=datetime.utcnow)
    reminder_checked_at = DateTimeField()
    last_notification = StringField(default='')
    meta = {'collection': 'notification_devices', 'indexes': [('organization', 'user'), 'refreshed_at']}
