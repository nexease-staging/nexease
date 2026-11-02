from django.views.decorators.http import require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.core.services import user_mailbox_service as mailbox
from apps.business.views import payload
from apps.saas.security import rate

@sensitive_post_parameters('password')
@api_login_required
@require_http_methods(['GET','POST','DELETE'])
def mailbox_api(request):
    user,org=request.api_user,request.api_organization
    try:
        if request.method=='GET':return R.success(data=mailbox.status(user,org),request=request)
        if request.method=='DELETE':
            mailbox.disconnect(user,org)
            return R.success(data=mailbox.status(user,org),message='Mailbox disconnected.',request=request)
        rate('mailbox-connect:'+str(user.id),5,300)
        body=payload(request)
        data=mailbox.connect(user,org,body.get('provider'),body.get('password'))
        return R.success(data=data,message='Mailbox authenticated. Documents will use your registered email.',request=request)
    except ValueError as error:return R.validation_error(message=str(error),request=request)
