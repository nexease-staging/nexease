import json
import os
from datetime import datetime
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as Response
from apps.core.device_models import NotificationDevice

@api_login_required
def notification_device_api(request):
    user = request.api_user
    if request.method == 'GET':
        return Response.success(data={'push_enabled': os.getenv('NEXEASE_PUSH_ENABLED', '').lower() == 'true'}, request=request)
    if request.method not in ('POST', 'DELETE'):
        return Response.method_not_allowed(message='Use GET, POST or DELETE.', request=request)
    try:
        data = json.loads(request.body or '{}')
        token = data.get('token') if isinstance(data, dict) else None
        if not isinstance(token, str) or not 20 <= len(token) <= 4096 or any(c.isspace() for c in token):
            raise ValueError('Invalid device token.')
    except (ValueError, TypeError):
        return Response.validation_error(message='Invalid device token.', request=request)
    if request.method == 'DELETE':
        NotificationDevice.objects(token=token, user=user, organization=user.organization).delete()
    else:
        # A device can only have one recipient. Reassignment never carries old deliveries.
        now = datetime.utcnow()
        existing = NotificationDevice.objects(token=token).first()
        if existing and str(existing.user.id) == str(user.id) and str(existing.organization.id) == str(user.organization.id):
            existing.update(set__refreshed_at=now)
        else:
            NotificationDevice.objects(token=token).update_one(upsert=True, set__user=user,
                set__organization=user.organization, set__registered_at=now, set__refreshed_at=now,
                set__last_notification='', unset__reminder_checked_at=1)
    return Response.success(data={'registered': request.method == 'POST'}, request=request)
