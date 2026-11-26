"""Separate partner sessions: no access to organization accounts or owner sessions."""
import hashlib
import secrets
import time
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.views.decorators.http import require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from mongoengine.connection import get_db
from pymongo.errors import DuplicateKeyError
from apps.business.views import payload
from apps.core.services.api_response_service import APIResponseService as R
from .security import rate, owner_required, verify_totp, log


def partner_for(request):
    session = request.session.get('nexease_partner', {})
    if time.time() - session.get('at', 0) > 8 * 3600:
        return None
    return get_db().saas_partners.find_one({'_id': session.get('id'),
        'generation': session.get('generation'), 'status': {'$in': ['pending', 'approved']}})


SHORT_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'  # no 0/O, 1/I/L: easy to read aloud


def normalise_code(code):
    return ''.join(ch for ch in str(code or '').upper() if ch.isalnum())


def ensure_short_code(partner):
    """A short code such as NX7K4P2Q that people can type or say. Long codes stay valid."""
    if partner.get('short_code') or partner.get('status') != 'approved':
        return partner
    db = get_db()
    db.saas_partners.create_index('short_code', unique=True, sparse=True)
    for _ in range(20):
        code = 'NX' + ''.join(secrets.choice(SHORT_ALPHABET) for _ in range(6))
        try:
            result = db.saas_partners.update_one({'_id': partner['_id'], 'short_code': {'$exists': False}}, {'$set': {'short_code': code}})
        except DuplicateKeyError:
            continue
        if result.modified_count:
            return {**partner, 'short_code': code}
        return db.saas_partners.find_one({'_id': partner['_id']}) or partner
    raise ValueError('Could not create a referral code. Try again.')


def public_partner(row):
    return {k: row.get(k) for k in ('name', 'email', 'status', 'referral_code', 'short_code', 'email_verified')}


@sensitive_post_parameters('password')
@require_http_methods(['GET', 'POST'])
def session(request):
    if request.method == 'GET':
        partner = partner_for(request)
        return R.success(data={'partner': public_partner(partner) if partner else None}, request=request)
    try:
        data = payload(request)
        action = data.get('action')
        if action == 'logout':
            request.session.pop('nexease_partner', None)
            return R.success(data={}, request=request)
        if action not in ('register', 'login'):
            raise ValueError('Unknown partner action.')
        rate('partner-ip:' + request.META.get('REMOTE_ADDR', ''), 15)
        email = str(data.get('email', '')).strip().lower()
        if len(email) > 254:
            raise ValueError('Email is too long.')
        validate_email(email)
        rate('partner-email:' + hashlib.sha256(email.encode()).hexdigest(), 8)
        password = data.get('password', '')
        if not isinstance(password, str) or not 1 <= len(password) <= 128:
            raise ValueError('Enter a password of at most 128 characters.')
        db = get_db()
        if action == 'register':
            name = str(data.get('name', '')).strip()
            if not 1 <= len(name) <= 200:
                raise ValueError('Enter your name (up to 200 characters).')
            validate_password(password)
            # Existing operator-created partners may have no portal identity yet;
            # never claim their records merely by knowing their email address.
            db.saas_partners.create_index('email', unique=True)
            try:
                created = db.saas_partners.insert_one({'_id': secrets.token_hex(16), 'name': name, 'email': email,
                    'password': make_password(password), 'generation': 0, 'status': 'pending',
                    'created_at': datetime.utcnow()})
                from .partner_mail import queue_welcome
                queue_welcome(created.inserted_id, email)
            except DuplicateKeyError:
                pass  # Same neutral result avoids account enumeration.
            return R.success(data={'message': 'Application received. If this email is new, the owner will review it. Existing partners can sign in.'}, request=request)
        partner = db.saas_partners.find_one({'email': email})
        valid = check_password(password, partner.get('password') if partner and partner.get('password') else make_password('unused'))
        if not valid or not partner or partner['status'] not in ('pending', 'approved'):
            return R.unauthorized(message='Invalid partner credentials or account unavailable.', request=request)
        request.session.cycle_key()
        request.session['nexease_partner'] = {'id': partner['_id'], 'generation': partner['generation'], 'at': time.time()}
        return R.success(data={'partner': public_partner(partner)}, request=request)
    except (ValueError, ValidationError) as exc:
        return R.validation_error(message=' '.join(exc.messages) if isinstance(exc, ValidationError) else str(exc), request=request)


def page_number(request):
    return max(1, min(100000, int(request.GET.get('page', 1))))


@require_http_methods(['GET'])
def dashboard(request):
    partner = partner_for(request)
    if not partner or partner['status'] != 'approved':
        return R.forbidden(message='Approved partner sign-in is required.', request=request)
    try:
        page = page_number(request)
    except (ValueError, TypeError):
        return R.validation_error(message='Invalid page.', request=request)
    db = get_db()
    try:
        partner = ensure_short_code(partner)
    except ValueError:
        pass
    # Public portal always shows live records. Test activity is operator-only.
    scope = {'partner_id': partner['_id'], 'mode': 'live'}
    rows = list(db.saas_commissions.find(scope, {'_id':0, 'payment_id':1, 'paid_at':1,
        'amount_paise':1, 'percent':1, 'status':1, 'net_subscription_paise':1, 'net_refund_paise':1})
        .sort([('paid_at',-1), ('_id',1)]).skip((page-1)*25).limit(25))
    totals = list(db.saas_commissions.aggregate([{'$match':scope}, {'$group':{'_id':None,
        'review_paise':{'$sum':{'$ifNull':['$amount_paise',0]}},
        'held':{'$sum':{'$cond':[{'$eq':['$amount_paise',None]},1,0]}}}}]))
    paid = {r['commission_id']:r['amount_paise'] for r in db.saas_partner_payouts.find({**scope, 'commission_id': {'$in':['live:'+r['payment_id'] for r in rows]}})}
    for row in rows:
        row['recorded_payout_paise'] = paid.get('live:'+row['payment_id'],0)
    referrals = list(db.saas_referrals.find({'partner_id':partner['_id']}, {'_id':1, 'assigned_at':1})
        .sort('assigned_at',-1).skip((page-1)*25).limit(25))
    return R.success(data={'partner':public_partner(partner), 'entries':rows,
        'totals':totals[0] if totals else {'review_paise':0,'held':0}, 'page':page,
        'total':db.saas_commissions.count_documents(scope),
        'referral_total':db.saas_referrals.count_documents({'partner_id':partner['_id']}),
        'paid_total':sum(1 for _ in db.saas_payments.aggregate([{'$match':{'mode':'live','organization_id':{'$in':[r['_id'] for r in db.saas_referrals.find({'partner_id':partner['_id']},{'_id':1})]}}},{'$group':{'_id':'$organization_id'}}])),
        'referrals':referral_details(referrals)}, request=request)


def referral_details(referrals):
    """Business name, plan and status for the partner's own referrals. No amounts or client data."""
    from bson import ObjectId
    from apps.organizations.models import Organization
    from .models import Membership
    from .entitlements import DEFAULTS
    ids = [r['_id'] for r in referrals]
    names = {str(o.id): o.name for o in Organization.objects(id__in=[ObjectId(i) for i in ids if ObjectId.is_valid(i)]).only('id', 'name')}
    members = {m.organization_id: m for m in Membership.objects(organization_id__in=ids)}
    now = datetime.utcnow()
    out = []
    for r in referrals:
        m = members.get(r['_id'])
        live = bool(m and not m.suspended and m.status in ('active', 'trial') and m.start <= now < m.end)
        status = 'Paid' if live and m.status == 'active' and m.plan != 'free' else 'Trial' if live and m.status == 'trial' else 'Free' if live else 'Inactive'
        out.append({'reference': r['_id'], 'business': names.get(r['_id'], 'Business'), 'date': r['assigned_at'].isoformat(),
                    'plan': DEFAULTS.get(m.plan, (m.plan,))[0] if m else '', 'status': status})
    return out


@owner_required
@require_http_methods(['GET', 'POST'])
def owner_partners(request):
    db = get_db()
    if request.method == 'POST':
        data = payload(request)
        reason = str(data.get('reason', '')).strip()
        if len(reason) < 5:
            raise ValueError('Enter an approval reason of at least five characters.')
        owner = request.platform_owner
        if not check_password(str(data.get('password','')), owner.password) or not verify_totp(owner, str(data.get('code',''))):
            raise ValueError('Fresh owner password and authenticator code are required.')
        action = data.get('action')
        if action not in ('approve','reject','suspend'):
            raise ValueError('Invalid partner decision.')
        partner = db.saas_partners.find_one({'_id':str(data.get('id',''))})
        if not partner or not partner.get('password'):
            raise ValueError('Portal application not found.')
        if action == 'approve' and not partner.get('email_verified'):
            raise ValueError('The partner must verify their email before approval.')
        status = {'approve':'approved','reject':'rejected','suspend':'suspended'}[action]
        log(owner.email, 'partner:'+action, reason=reason, details={'partner_id':partner['_id']})
        db.saas_partners.update_one({'_id':partner['_id']}, {'$set':{'status':status,
            'referral_code':partner.get('referral_code') or secrets.token_hex(16),
            'approved_by':owner.email, 'updated_at':datetime.utcnow()}, '$inc':{'generation':1}})
        if status == 'approved':
            ensure_short_code({**partner, 'status': 'approved'})
        return R.success(data={'message':'Partner decision saved. Existing partner sessions were invalidated.'}, request=request)
    page = page_number(request)
    scope = {}
    if request.GET.get('id'):
        scope['_id'] = request.GET['id']
    status = request.GET.get('status','')
    if status in ('pending','approved','rejected','suspended'): scope['status'] = status
    rows = list(db.saas_partners.find(scope, {'password':0}).sort([('created_at',-1),('_id',1)]).skip((page-1)*25).limit(25))
    return R.success(data={'partners':[{**public_partner(r),'id':r['_id']} for r in rows],
        'total':db.saas_partners.count_documents(scope),'page':page}, request=request)


def resolve_referral(code, user_email):
    if not code:
        return None
    if not isinstance(code,str) or len(code)>64:
        raise ValueError('Invalid referral code.')
    partner = get_db().saas_partners.find_one({'referral_code':code.strip(), 'status':'approved'})
    if not partner and normalise_code(code).startswith('NX') and len(normalise_code(code)) == 8:
        partner = get_db().saas_partners.find_one({'short_code':normalise_code(code), 'status':'approved'})
    if not partner:
        raise ValueError('Referral code is not active. Remove it or contact your partner.')
    if partner['email'] == user_email.strip().lower():
        raise ValueError('You cannot refer your own registered email.')
    return partner['_id']
