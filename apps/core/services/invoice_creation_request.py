"""Durable HTTP creation receipts; interrupted writes are held, never replayed."""
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from hashlib import sha256
import json
import logging
import re

from django.http import JsonResponse
from mongoengine.connection import get_db
from pymongo.errors import DuplicateKeyError
from apps.authorization.services import AuthorizationService
from apps.core.services.api_response_service import APIResponseService as R

_current = ContextVar('invoice_creation_request', default=None)
logger = logging.getLogger(__name__)
HOLD = 'This invoice request needs review. Do not create it again; ask an administrator to inspect invoice creation requests.'


def mark_invoice_write(invoice=None):
    key = _current.get()
    if key:
        values = {'status': 'writing', 'updated_at': datetime.now(timezone.utc)}
        if invoice is not None:
            values.update(invoice_id=str(invoice.id), invoice_number=invoice.invoice_number)
        get_db().invoice_creation_requests.update_one({'_id': key}, {'$set': values})


def _error(request, message, code='INVOICE_REQUEST_REVIEW'):
    return R.error(code=code, message=message, status=409, request=request)


def invoice_creation_request(route):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            key = request.headers.get('X-NexEase-Request-Key')
            if request.method != 'POST' or key is None:
                return view(request, *args, **kwargs)
            user, org = request.api_user, request.api_organization
            if not user.is_active or user.organization.id != org.id or not AuthorizationService.has_permission(user, 'invoices.create'):
                return R.forbidden(message='Invoice creation permission is required.', request=request)
            if not re.fullmatch(r'[A-Za-z0-9_-]{16,100}', key):
                return R.validation_error(message='Invalid invoice request key.', request=request)
            try:
                payload = json.loads(request.body or b'{}')
                numbering = json.loads(request.headers.get('X-NexEase-Numbering', 'null'))
                if not isinstance(payload, dict):
                    raise ValueError()
                fingerprint = sha256(json.dumps({'payload':payload,'numbering':numbering}, sort_keys=True, allow_nan=False).encode()).hexdigest()
            except (ValueError, TypeError, UnicodeDecodeError):
                return R.validation_error(message='Invalid invoice request body.', request=request)
            identifier = sha256(f'{org.id}:{route}:{key}'.encode()).hexdigest()
            collection = get_db().invoice_creation_requests
            previous = collection.find_one({'_id': identifier})
            if previous:
                if previous['user_id'] != str(user.id) or previous['fingerprint'] != fingerprint:
                    return _error(request, 'This request key was already used for different invoice details.', 'INVOICE_REQUEST_CONFLICT')
                if previous['status'] == 'completed':
                    response = JsonResponse(previous['response'], status=previous['http_status'])
                    response['X-NexEase-Replayed'] = 'true'
                    return response
                return _error(request, HOLD)
            # A new key must not bypass an unresolved identical submission.
            if collection.find_one({'organization_id':str(org.id), 'user_id':str(user.id), 'route':route,
                                    'fingerprint':fingerprint, 'status':{'$ne':'completed'}}):
                return _error(request, HOLD)
            now = datetime.now(timezone.utc)
            try:
                collection.insert_one({'_id':identifier, 'organization_id':str(org.id), 'user_id':str(user.id),
                    'route':route, 'fingerprint':fingerprint, 'status':'validating', 'created_at':now, 'updated_at':now})
            except DuplicateKeyError:
                return _error(request, 'This invoice request is already processing. Retry the same request shortly.', 'INVOICE_REQUEST_PENDING')
            token = _current.set(identifier)
            try:
                response = view(request, *args, **kwargs)
                if response.status_code < 400:
                    data = json.loads(response.content)
                    collection.update_one({'_id':identifier}, {'$set':{'status':'completed', 'response':data,
                        'http_status':response.status_code, 'updated_at':datetime.now(timezone.utc)}})
                    return response
                if collection.delete_one({'_id':identifier, 'status':'validating'}).deleted_count:
                    return response
                collection.update_one({'_id':identifier}, {'$set':{'status':'review_required','updated_at':datetime.now(timezone.utc)}})
                return _error(request, HOLD)
            except Exception:
                if collection.delete_one({'_id':identifier, 'status':'validating'}).deleted_count:
                    raise
                logger.exception('Invoice creation interrupted; retained for review', extra={'invoice_request_id':identifier})
                collection.update_one({'_id':identifier}, {'$set':{'status':'review_required','updated_at':datetime.now(timezone.utc)}})
                return _error(request, HOLD)
            finally:
                _current.reset(token)
        return wrapped
    return decorate


def assert_invoice_creation_complete(organization, invoice):
    if get_db().invoice_creation_requests.find_one({
        'organization_id':str(organization.id), 'invoice_id':str(invoice.id), 'status':{'$ne':'completed'}
    }):
        raise ValueError(HOLD)
