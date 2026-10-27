import json
from functools import wraps
from mongoengine.errors import ValidationError
from apps.migration.models import MigrationBatch
from apps.authorization.services import AuthorizationService
from apps.core.services.api_response_service import APIResponseService as R

def employee_migration_access(view):
    @wraps(view)
    def wrapped(request,*args,**kwargs):
        kind=kwargs.get('migration_type');bid=kwargs.get('batch_id') or (args[0] if args else None)
        if bid:
            try:
                b=MigrationBatch.objects(id=bid,organization=request.api_organization).first()
                if b:kind=b.migration_type
            except ValidationError:pass
        if request.method=='POST' and not bid and request.content_type=='application/json':
            try:
                p=json.loads(request.body)
                if isinstance(p,dict):kind=p.get('migration_type',kind)
            except ValueError:pass
        if str(kind).upper()=='EMPLOYEES' and not AuthorizationService.has_permission(request.api_user,'payroll.read' if request.method=='GET' else 'payroll.manage'):return R.forbidden(message='Employee migration requires payroll access.',request=request)
        return view(request,*args,**kwargs)
    return wrapped
