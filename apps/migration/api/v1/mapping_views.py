from .employee_access import employee_migration_access
from datetime import datetime
import json
from apps.core.api.decorators import api_login_required
from apps.authorization.services import AuthorizationService
from apps.core.services.api_response_service import APIResponseService as R
from apps.migration.services.migration_api_service import MigrationAPIService
from apps.migration.services.migration_schema_service import MigrationSchemaService

@api_login_required
@employee_migration_access
def mapping_api(request,batch_id):
    if not AuthorizationService.has_permission(request.api_user,'migration.validate'):return R.forbidden(message='Permission denied.',request=request)
    try:
        batch=MigrationAPIService.get_batch(organization=request.api_organization,batch_id=batch_id)
        schema=MigrationSchemaService.get_schema(batch.migration_type)
        if request.method=='GET':return R.success(data={'schema':schema,'mapping':batch.mapping},request=request)
        if request.method!='PATCH':return R.method_not_allowed(message='Use GET or PATCH.',request=request)
        if batch.status not in ('CREATED','UPLOADED','VALIDATED','FAILED'):raise ValueError('Mapping is locked while processing or after import.')
        p=json.loads(request.body);mapping=p.get('mapping',{})
        if not isinstance(mapping,dict) or any(k not in schema['fields'] or not isinstance(v,str) or len(v)>200 for k,v in mapping.items()):raise ValueError('Invalid target-to-source mapping.')
        mapped=[v for v in mapping.values() if v]
        if len(mapped)!=len(set(mapped)):raise ValueError('A source column cannot be mapped twice.')
        updated=batch.__class__.objects(id=batch.id,organization=request.api_organization,status=batch.status,updated_at=batch.updated_at).modify(new=True,set__updated_at=datetime.utcnow(),set__mapping={k:v for k,v in mapping.items() if v},set__status='UPLOADED' if batch.upload_id else 'CREATED',set__validation_result={},set__valid_rows=0,set__invalid_rows=0)
        if not updated:raise ValueError('Batch changed; reload first.')
        return R.success(data={'migration':MigrationAPIService.serialize_batch(updated)},request=request)
    except LookupError:return R.not_found(message='Batch not found.',request=request)
    except (ValueError,TypeError) as e:return R.validation_error(message=str(e),request=request)
