import json
from unittest.mock import patch, Mock
from django.test import SimpleTestCase, RequestFactory, override_settings
from apps.core.services.device_notification_service import reminder_items
from apps.core.api.v1.device_views import notification_device_api
from apps.accounts.services import AuthenticationService

class DeviceNotificationTests(SimpleTestCase):
    def test_reminders_respect_permissions(self):
        data={'alerts':{'overdue_invoices':4,'overdue_bills':3,'out_of_stock_items':2}}
        with patch('apps.core.services.device_notification_service.AuthorizationService.has_permission',side_effect=lambda u,p:p=='inventory.read'):
            self.assertEqual(reminder_items(Mock(),data),[('Out of stock',2,'/inventory')])
    def test_zero_counts_do_not_notify(self):
        with patch('apps.core.services.device_notification_service.AuthorizationService.has_permission',return_value=True):
            self.assertEqual(reminder_items(Mock(),{'alerts':{}}),[])
    def test_device_delete_is_scoped_to_current_user_and_organization(self):
        request=RequestFactory().delete('/api/v1/notifications/device/',data=json.dumps({'token':'a'*50}),content_type='application/json')
        request.api_user=Mock()
        # Test handler directly; the shared decorator is covered by API authentication tests.
        handler=notification_device_api.__wrapped__
        with patch('apps.core.api.v1.device_views.NotificationDevice') as devices:
            response=handler(request)
            self.assertEqual(response.status_code,200)
            devices.objects.assert_called_once_with(token='a'*50,user=request.api_user,organization=request.api_user.organization)
    @override_settings(NEXEASE_MOBILE_ENABLED=True)
    def test_native_login_has_persistent_expiry(self):
        request=RequestFactory().post('/login',HTTP_ORIGIN='https://localhost')
        from unittest.mock import MagicMock
        request.session=MagicMock()
        AuthenticationService.login(request,Mock(id='u1'))
        request.session.set_expiry.assert_called_once_with(2592000)
    @override_settings(NEXEASE_MOBILE_ENABLED=True)
    def test_web_login_keeps_default_expiry(self):
        request=RequestFactory().post('/login',HTTP_ORIGIN='https://example.test')
        from unittest.mock import MagicMock
        request.session=MagicMock()
        AuthenticationService.login(request,Mock(id='u1'))
        request.session.set_expiry.assert_not_called()

    def test_invalid_device_token_is_rejected(self):
        request=RequestFactory().post('/api/v1/notifications/device/',data=json.dumps({'token':'bad'}),content_type='application/json')
        request.api_user=Mock()
        with patch('apps.core.api.v1.device_views.NotificationDevice') as devices:
            self.assertEqual(notification_device_api.__wrapped__(request).status_code,400)
            devices.objects.assert_not_called()
    def test_device_endpoint_requires_login(self):
        with patch('apps.core.api.decorators.APIOrganizationContextService.resolve',side_effect=PermissionError('Sign in')):
            self.assertEqual(notification_device_api(RequestFactory().get('/api/v1/notifications/device/')).status_code,401)

    def test_worker_delivers_only_to_matching_active_tenant(self):
        from types import SimpleNamespace
        from datetime import datetime
        from apps.core.services.device_notification_service import dispatch_once
        import sys
        organization=SimpleNamespace(id='org-a',is_active=True)
        user=SimpleNamespace(id='user-a',is_active=True,organization=organization)
        device=SimpleNamespace(id='device',user=user,organization=organization,registered_at=datetime.utcnow(),refreshed_at=datetime.utcnow(),reminder_checked_at=datetime.utcnow(),last_notification='',token='private-token',update=Mock(),delete=Mock())
        notice=SimpleNamespace(id='notice',is_read=False,action_url='/invoices',title='Invoice',background_job_key=None)
        messaging=SimpleNamespace(Message=Mock(return_value='message'),Notification=Mock(),AndroidConfig=Mock(),AndroidNotification=Mock(),send=Mock(),UnregisteredError=type('UnregisteredError',(Exception,),{}))
        module=SimpleNamespace(messaging=messaging)
        with patch.dict('os.environ',{'NEXEASE_PUSH_ENABLED':'true'}),patch.dict(sys.modules,{'firebase_admin':module}),patch('apps.core.services.device_notification_service.firebase_app'),patch('apps.core.services.device_notification_service.NotificationDevice') as devices,patch('apps.core.services.device_notification_service.Notification') as notifications,patch('apps.core.services.device_notification_service.AuthorizationService.has_permission',return_value=True):
            devices.objects.side_effect=[[device],Mock(first=Mock(return_value=device))]
            notifications.objects.return_value.order_by.return_value.limit.return_value=[notice]
            self.assertEqual(dispatch_once(),1)
            notifications.objects.assert_called_once_with(organization=organization,recipient=user,created_at__gte=device.registered_at)
            messaging.send.assert_called_once()
            device.update.assert_called_once_with(set__last_notification='notice')
            # A device whose stored tenant differs from the user's current tenant is removed.
            messaging.send.reset_mock()
            device.organization=SimpleNamespace(id='org-b',is_active=True)
            devices.objects.side_effect=[[device]]
            self.assertEqual(dispatch_once(),0)
            messaging.send.assert_not_called()
            device.delete.assert_called_once()
