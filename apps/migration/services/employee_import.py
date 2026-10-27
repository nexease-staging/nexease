from apps.business.schema import SCHEMAS
from apps.business.models import BusinessRecord as Record
from apps.business.views import validate
from apps.authorization.services import AuthorizationService
from mongoengine.errors import ValidationError
FIELDS={k:v['required'] for k,v in SCHEMAS['employees']['fields'].items()};FIELDS['code']=True

def validate_employee(org,row,seen):
    try:
        d={}
        for k,spec in SCHEMAS['employees']['fields'].items():
            v=row.get(k)
            if spec['type']=='boolean':
                text=str(v if v is not None else ('true' if k=='active' else 'false')).strip().lower()
                if text not in ('true','false','yes','no','1','0',''):raise ValueError(k+' must be true or false.')
                d[k]=text in ('true','yes','1')
            elif v is not None:d[k]=str(v).strip()
        if not d.get('code'):raise ValueError('Employee code is required for duplicate-safe migration.')
        clean=validate('employees',d,org);clean['code']=clean['code'].upper();code=clean['code']
        if code in seen:raise ValueError('Duplicate employee code in file.')
        seen.add(code)
        if Record.objects(organization=org,kind='employees',key=code).first():return {'valid':False,'errors':[{'field':'code','code':'ALREADY_EXISTS','message':'Employee code exists.'}],'normalized':clean}
        return {'valid':True,'errors':[],'normalized':clean}
    except (ValueError,TypeError,ValidationError) as e:return {'valid':False,'errors':[{'field':None,'code':'INVALID_EMPLOYEE','message':str(e)}],'normalized':{}}

def import_employee(user,org,row):
    if not AuthorizationService.has_permission(user,'payroll.manage'):raise PermissionError('Employee import requires payroll.manage.')
    result=validate_employee(org,row,set())
    if not result['valid']:raise ValueError('; '.join(e['message'] for e in result['errors']))
    d=result['normalized'];return Record(organization=org,kind='employees',key=d['code'],data=d,created_by=user).save()
