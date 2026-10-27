from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from mongoengine.errors import ValidationError
from mongoengine.connection import get_db
from .entitlements import enabled,require,feature_for
from apps.core.services.api_response_service import APIResponseService as R
class SaaSMiddleware(MiddlewareMixin):
 def process_view(self,request,view_func,args,kwargs):
  if not enabled() or not request.path.startswith('/api/v1/'):return
  user=getattr(request,'user',None)
  if not user or not user.is_authenticated:return
  if request.path.startswith(('/api/v1/saas/','/api/v1/auth/')):return
  try:require(user.organization,feature_for(request.path),request.method not in ('GET','HEAD','OPTIONS'))
  except ValidationError as e:return R.error(code='PLAN_REQUIRED',message=str(e),status=403,request=request)
 def process_response(self,request,response):
  user=getattr(request,'user',None)
  if request.path.startswith('/api/v1/') and user and user.is_authenticated:
   # Metadata only: no request bodies, passwords or document contents.
   get_db().saas_activity.insert_one({'organization_id':str(user.organization.id),'user_id':str(user.id),'path':request.path[:300],'method':request.method,'status':response.status_code,'at':datetime.utcnow()})
  return response
