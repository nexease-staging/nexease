"""Persistent, tenant-scoped cost guard. Claims never auto-expire into duplicate calls."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from uuid import uuid4
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from mongoengine.connection import get_db

IST = ZoneInfo('Asia/Kolkata')

class ProviderGuardError(ValueError):
    pass


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def month_key(now):
    aware = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
    return aware.astimezone(IST).strftime('%Y-%m')


def meter(org_id, feature, limit, now=None):
    period = month_key(now or utc_now())
    row = get_db().provider_usage.find_one({'_id': f'{org_id}:{feature}:{period}'}) or {}
    return {'used': row.get('used', 0), 'limit': max(0, int(limit)), 'period': period}


def guarded_call(*, org_id, feature, identity, limit, call, now=None, ttl_days=30):
    """Cache hits cost no quota. Failed/ambiguous paid attempts retain quota.

    A process crash leaves a pending claim for operator reconciliation. No lease
    takeover: a hung provider may still complete and must not be billed twice.
    """
    now = now or utc_now()
    org_id = str(org_id)
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    key = f'{org_id}:{feature}:{digest}'
    db = get_db()
    cached = db.provider_results.find_one({'_id': key, 'expires_at': {'$gt': now}})
    if cached:
        return cached['result']
    token = uuid4().hex
    try:
        db.provider_claims.insert_one({'_id': key, 'token': token, 'at': now})
    except DuplicateKeyError:
        raise ProviderGuardError('This lookup is already processing. Retry shortly; if it persists, contact support.')
    try:
        # Recheck after claim acquisition in case another process just finished.
        cached = db.provider_results.find_one({'_id': key, 'expires_at': {'$gt': now}})
        if cached:
            return cached['result']
        uid = f'{org_id}:{feature}:{month_key(now)}'
        try:
            db.provider_usage.update_one({'_id': uid}, {'$setOnInsert': {'used': 0}}, upsert=True)
        except DuplicateKeyError:
            pass  # Another identity initialized this month's counter concurrently.
        if int(limit) <= 0 or not db.provider_usage.find_one_and_update(
            {'_id': uid, 'used': {'$lt': int(limit)}}, {'$inc': {'used': 1}},
            return_document=ReturnDocument.AFTER,
        ):
            raise ProviderGuardError('Monthly lookup allowance reached. Upgrade your plan or contact NexEase for additional credits.')
        result = call()
        db.provider_results.update_one({'_id': key}, {'$set': {
            'result': result, 'expires_at': now + timedelta(days=ttl_days),
        }}, upsert=True)
        return result
    finally:
        db.provider_claims.delete_one({'_id': key, 'token': token})


def reserve_einvoice(org, invoice_id, environment, now=None):
    """Call under org_lock. Keep pending/failed reservations for safe IRP recovery."""
    from .entitlements import state
    now = now or utc_now()
    db = get_db()
    key = f'{org.id}:{environment}:{invoice_id}'
    if db.saas_einvoice_usage.find_one({'_id': key}):
        return
    membership = state(org)
    limit = membership.limits.get('einvoices', 0) if membership else 0
    period = month_key(now)
    used = db.saas_einvoice_usage.count_documents({'organization_id':str(org.id),'period':period})
    if used >= limit:
        raise ProviderGuardError('Monthly e-invoice allowance reached. Contact NexEase for additional credits.')
    db.saas_einvoice_usage.insert_one({'_id':key,'organization_id':str(org.id),'period':period,'invoice_id':str(invoice_id),'environment':environment,'at':now})
