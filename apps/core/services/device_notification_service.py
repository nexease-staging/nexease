"""FCM delivery worker. Firebase credentials stay on the server, never in the APK."""
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from apps.core.device_models import NotificationDevice
from apps.core.notification_models import Notification
from apps.core.services.notification_service import NotificationService
from apps.authorization.services import AuthorizationService
from apps.finance.services.main_dashboard_service import MainDashboardService

logger = logging.getLogger(__name__)

def reminder_items(user, dashboard):
    rules = [('invoices.read', 'overdue_invoices', 'Overdue invoices', '/invoices', None),
             ('bills.read', 'overdue_bills', 'Overdue supplier bills', '/vendor-bills', None),
             ('inventory.read', 'out_of_stock_items', 'Out of stock', '/inventory', None)]
    return [(title, int(dashboard.get('alerts', {}).get(key, 0)), url)
            for permission, key, title, url, _ in rules
            if AuthorizationService.has_permission(user, permission)
            and int(dashboard.get('alerts', {}).get(key, 0)) > 0]

def create_reminders(user, now=None):
    now = now or datetime.utcnow()
    # At most one reminder per category per user per six-hour window.
    bucket = int(now.replace(tzinfo=timezone.utc).timestamp()) // (6 * 3600)
    prefix = f'device-reminder:{user.id}:{bucket}:'
    if Notification.objects(organization=user.organization, recipient=user, background_job_key__startswith=prefix).first():
        return
    if not any(AuthorizationService.has_permission(user, p) for p in ('invoices.read','bills.read','inventory.read')):
        return
    dashboard = MainDashboardService.get_dashboard(user=user, organization=user.organization)
    for title, count, url in reminder_items(user, dashboard):
        NotificationService.create_notification(organization=user.organization, recipient=user,
            notification_type='SYSTEM', severity='WARNING', title=title,
            message=f'{count} items need your attention. Open NexEase to review.', action_url=url,
            background_job_key=prefix+url.strip('/'))

def firebase_app():
    import firebase_admin
    from firebase_admin import credentials
    try:
        return firebase_admin.get_app('nexease-notifications')
    except ValueError:
        raw = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        credential = credentials.Certificate(json.loads(raw)) if raw else credentials.ApplicationDefault()
        return firebase_admin.initialize_app(credential, {'httpTimeout': 15}, name='nexease-notifications')

def dispatch_once():
    if os.getenv('NEXEASE_PUSH_ENABLED', '').lower() != 'true':
        return 0
    from firebase_admin import messaging
    app = firebase_app()
    now = datetime.utcnow()
    sent = 0
    reminded = set()
    devices = NotificationDevice.objects(refreshed_at__gte=now-timedelta(days=30))
    for device in devices:
        try:
            user = device.user
            if not user.is_active or not device.organization.is_active or str(user.organization.id) != str(device.organization.id):
                device.delete()
                continue
            if not device.reminder_checked_at or device.reminder_checked_at < now-timedelta(hours=6):
                if str(user.id) not in reminded:
                    create_reminders(user, now)
                    reminded.add(str(user.id))
                device.update(set__reminder_checked_at=now)
            query = Notification.objects(organization=device.organization, recipient=user,
                created_at__gte=device.registered_at).order_by('id')
            if device.last_notification:
                query = query.filter(id__gt=ObjectId(device.last_notification))
            for notification in query.limit(100):
                # Recheck the current owner before every send, including concurrent logout/reassignment.
                if not NotificationDevice.objects(id=device.id, user=user, registered_at=device.registered_at).first():
                    break
                if notification.is_read:
                    device.update(set__last_notification=str(notification.id))
                    continue
                url = notification.action_url or '/home'
                if not url.startswith('/') or url.startswith('//'):
                    url = '/home'
                permission = {'/invoices':'invoices.read', '/vendor-bills':'bills.read', '/inventory':'inventory.read'}.get(url)
                if permission and not AuthorizationService.has_permission(user, permission):
                    device.update(set__last_notification=str(notification.id))
                    continue
                title = notification.title if (notification.background_job_key or '').startswith('device-reminder:') else 'NexEase business alert'
                # Keep lock-screen payload generic; detailed notifications stay authenticated in-app.
                message = messaging.Message(token=device.token,
                    notification=messaging.Notification(title=title, body='You have an update. Open NexEase to review.'),
                    data={'url':url,'notification_id':str(notification.id)},
                    android=messaging.AndroidConfig(ttl=timedelta(hours=6), notification=messaging.AndroidNotification(channel_id='nexease-business', icon='ic_stat_nexease', tag=str(notification.id))))
                messaging.send(message, app=app)
                device.update(set__last_notification=str(notification.id))
                sent += 1
        except messaging.UnregisteredError:
            device.delete()
        except Exception:
            # Do not log tokens, notification contents or service-account credentials.
            logger.warning('Device notification delivery failed; retrying next cycle.')
    return sent
