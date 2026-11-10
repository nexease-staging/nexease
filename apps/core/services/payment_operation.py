"""Durable payment retry receipts. Incomplete writes are held, never replayed.

This is a serialization/recovery boundary, not a multi-document transaction.
All financial writers must share the organization lock to participate.
"""
from contextlib import contextmanager, ExitStack
from contextvars import ContextVar
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from hashlib import sha256
import json
import re
from uuid import uuid4

from mongoengine.connection import get_db
from mongoengine.errors import ValidationError
from apps.authorization.services import AuthorizationService
from apps.saas.entitlements import org_lock

_current = ContextVar('payment_operation', default=None)
HOLD_MESSAGE = 'An earlier payment needs reconciliation. Do not pay again; ask an administrator to review payment operations.'


@contextmanager
def financial_lock(organization_id):
    with ExitStack() as stack:
        try:
            stack.enter_context(org_lock(organization_id))
        except ValidationError as exc:
            raise ValueError('Another update is running. Retry shortly with the same payment details. If it persists, ask an administrator to review the organization lock.') from exc
        yield


def serialized_financial_write(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        organization = kwargs.get('organization')
        if not organization:
            raise ValueError('Organization is required.')
        with financial_lock(organization.id):
            return fn(*args, **kwargs)
    return wrapped


def payment_write_started(payment_number):
    current = _current.get()
    if current:
        get_db().payment_operations.update_one(
            {'_id': current}, {'$set': {'status': 'writing', 'payment_number': payment_number,
                                     'updated_at': datetime.utcnow()}})


def _fingerprint(kwargs, document_arg):
    try:
        amount = Decimal(str(kwargs['amount']))
        if not amount.is_finite() or amount != amount.quantize(Decimal('0.01')):
            raise ValueError('Invalid payment amount.')
    except (InvalidOperation, TypeError) as exc:
        raise ValueError('Invalid payment amount.') from exc
    payload = {key: str(kwargs.get(key) or '').strip() for key in
               ('payment_date', 'reference_number', 'notes')}
    payload.update(document_id=str(kwargs[document_arg].id),
                   bank_account_id=str(kwargs['bank_account'].id),
                   amount=str(amount.normalize()),
                   payment_method=str(kwargs['payment_method']).strip().upper())
    return sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def payment_operation(kind, document_arg, permission):
    def decorate(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user, org = kwargs.get('user'), kwargs.get('organization')
            if not user or not user.is_active or not org or not user.organization or user.organization.id != org.id:
                raise PermissionError('Payment access denied.')
            if not AuthorizationService.has_permission(user, permission):
                raise PermissionError('Payment permission is required.')
            document, bank = kwargs.get(document_arg), kwargs.get('bank_account')
            for obj in (document, bank):
                if not obj or obj.organization.id != org.id:
                    raise PermissionError('Payment records must belong to this organization.')
            key = kwargs.pop('request_key', None)
            if key is not None and (not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,100}', key)):
                raise ValueError('Invalid payment request key.')
            # Legacy callers retain compatibility, but need a stable key for successful replay.
            key = key or uuid4().hex
            operation_id = sha256(f'{org.id}:{kind}:{key}'.encode()).hexdigest()
            fingerprint = _fingerprint(kwargs, document_arg)
            collection = get_db().payment_operations
            with financial_lock(org.id):
                previous = collection.find_one({'_id': operation_id})
                if previous:
                    if previous['user_id'] != str(user.id) or previous['fingerprint'] != fingerprint:
                        raise ValueError('This payment request key was already used for different details.')
                    if previous['status'] == 'completed':
                        from apps.sales.models import CustomerPayment
                        from apps.purchasing.models import SupplierPayment
                        model = CustomerPayment if kind == 'customer' else SupplierPayment
                        payment = model.objects(organization=org, id=previous['payment_id']).first()
                        if not payment:
                            raise ValueError(HOLD_MESSAGE)
                        document.reload()
                        return payment
                    raise ValueError(HOLD_MESSAGE)
                if collection.find_one({'organization_id': str(org.id), 'kind': kind,
                                        'document_id': str(document.id),
                                        'status': {'$in': ['validating', 'writing', 'review_required']}}):
                    raise ValueError(HOLD_MESSAGE)
                # Refresh inside the lock, before checking outstanding amounts.
                document.reload()
                bank.reload()
                now = datetime.utcnow()
                collection.insert_one({'_id': operation_id, 'organization_id': str(org.id),
                    'kind': kind, 'document_id': str(document.id), 'user_id': str(user.id),
                    'fingerprint': fingerprint, 'status': 'validating', 'created_at': now, 'updated_at': now})
                token = _current.set(operation_id)
                try:
                    payment = fn(*args, **kwargs)
                    collection.update_one({'_id': operation_id}, {'$set': {
                        'status': 'completed', 'payment_id': str(payment.id), 'updated_at': datetime.utcnow()}})
                    return payment
                except Exception as exc:
                    # Validation failures have no writes and may safely be corrected/retried.
                    clean = collection.delete_one({'_id': operation_id, 'status': 'validating'}).deleted_count
                    collection.update_one({'_id': operation_id}, {'$set': {
                        'status': 'review_required', 'updated_at': datetime.utcnow()}})
                    if not clean:
                        raise ValueError(HOLD_MESSAGE) from exc
                    raise
                finally:
                    _current.reset(token)
        return wrapped
    return decorate


def hold_payment_for_review(organization, payment):
    get_db().payment_operations.update_many(
        {'organization_id': str(organization.id), 'payment_id': str(payment.id)},
        {'$set': {'status': 'review_required', 'updated_at': datetime.utcnow()}})
