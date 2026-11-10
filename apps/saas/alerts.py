"""IST subscription alerts in the existing worker; durable per-cycle/channel keys.

Email ambiguity is held, never automatically retried. SMTP has no idempotency
primitive: delivery exactly once cannot be guaranteed after an acceptance crash.
"""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from mongoengine.connection import get_db
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from django.core.mail import EmailMessage, get_connection
from .models import Membership

IST = ZoneInfo('Asia/Kolkata')


def as_ist(value):
    return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value).astimezone(IST)


def enqueue(*, organization, recipient, cycle, due_date, kind, title, message, now):
    for channel in ('email', 'in_app'):
        key = hashlib.sha256(f'{organization}:{recipient}:{cycle}:{due_date}:{kind}:{channel}'.encode()).hexdigest()
        try:
            get_db().subscription_alerts.update_one({'_id': key}, {'$setOnInsert': {
            'organization': str(organization), 'recipient': str(recipient),
            'cycle': cycle, 'due_date': str(due_date), 'kind': kind,
            'channel': channel, 'title': title, 'message': message,
            'status': 'pending', 'created_at': now,
        }}, upsert=True)
        except DuplicateKeyError:
            pass  # A concurrent scheduler already inserted this exact event.


def schedule(now=None, offsets=None):
    """Offsets are days BEFORE expiry; negative values mean after expiry.
    Empty production schedule is deliberate until the owner defines policy.
    Catch up missed dates only within the current membership cycle.
    """
    from apps.accounts.models import User
    from apps.authorization.models import Role
    from apps.organizations.models import Organization
    now = now or datetime.utcnow()
    offsets = offsets if offsets is not None else [int(x) for x in os.getenv('SUBSCRIPTION_ALERT_DAYS', '7,3,1').split(',') if x.strip()]
    if len(offsets) > 20 or any(abs(x) > 90 for x in offsets):
        raise ValueError('Subscription alert offsets must contain at most 20 days within +/-90.')
    today = as_ist(now).date()
    for m in Membership.objects(status__in=['active', 'trial'], suspended=False):
        org = Organization.objects(id=m.organization_id, is_active=True).first()
        if not org:
            continue
        roles = Role.objects(organization=org, name='Admin', is_system=True, is_active=True)
        recipients = list(User.objects(organization=org, role__in=list(roles), is_active=True).only('id'))
        cycle = f'{m.subscription_id or m.organization_id}:{m.start.isoformat()}:{m.end.isoformat()}'
        for offset in sorted(set(offsets), reverse=True):
            due = as_ist(m.end).date() - timedelta(days=offset)
            if not as_ist(m.start).date() <= due <= today:
                continue
            for user in recipients:
                enqueue(organization=org.id, recipient=user.id, cycle=cycle, due_date=due,
                    kind=f'renewal:{offset}', title='NexEase subscription reminder',
                    message=f'Your {m.plan} access ends on {as_ist(m.end).date().isoformat()} (IST). Open Subscription to review renewal.', now=now)


def deliver_one(now=None, send_email=None):
    from apps.accounts.models import User
    from apps.organizations.models import Organization
    from apps.core.repositories.notification_repository import NotificationRepository
    now = now or datetime.utcnow()
    db = get_db()
    # Recover in-app claims safely: Notification's unique key makes replays harmless.
    db.subscription_alerts.update_many({'status': 'sending', 'channel': 'in_app', 'claimed_at': {'$lt': now-timedelta(minutes=5)}}, {'$set': {'status': 'pending'}})
    row = db.subscription_alerts.find_one_and_update({'status': 'pending'},
        {'$set': {'status': 'sending', 'claimed_at': now}}, sort=[('created_at', 1)], return_document=ReturnDocument.AFTER)
    if not row:
        return False
    try:
        org = Organization.objects(id=row['organization'], is_active=True).first()
        user = User.objects(id=row['recipient'], organization=org, is_active=True).first() if org else None
        if not user:
            db.subscription_alerts.update_one({'_id': row['_id']}, {'$set': {'status': 'cancelled'}})
            return True
        if row['kind'].startswith('renewal:'):
            membership = Membership.objects(organization_id=row['organization'], suspended=False, status__in=['active', 'trial']).first()
            cycle = (f'{membership.subscription_id or membership.organization_id}:{membership.start.isoformat()}:{membership.end.isoformat()}' if membership else None)
            if cycle != row['cycle']:
                db.subscription_alerts.update_one({'_id': row['_id']}, {'$set': {'status': 'cancelled'}})
                return True
        if row['channel'] == 'in_app':
            NotificationRepository.create(organization=org, recipient=user, notification_type='SYSTEM',
                title=row['title'], message=row['message'], action_url='/dashboard' if row['kind']=='welcome' else '/subscription',
                background_job_key='subscription:'+row['_id'])
        elif send_email:
            send_email(row, user)
        else:
            if os.getenv('EMAIL_MODE') != 'production':
                raise ValueError('Production email delivery is not configured')
            count = EmailMessage(row['title'], row['message'],
                from_email='NexEase <nexease.contact@gmail.com>', to=[user.email],
                connection=get_connection(timeout=30)).send(fail_silently=False)
            if count != 1:
                raise ValueError('Email acceptance not confirmed')
        db.subscription_alerts.update_one({'_id': row['_id']}, {'$set': {'status': 'sent', 'sent_at': now}})
    except Exception as exc:
        # Never leak provider text, credentials or recipient details to logs.
        db.subscription_alerts.update_one({'_id': row['_id']}, {'$set': {
            'status': 'review_required', 'error_type': type(exc).__name__,
        }})
    return True
