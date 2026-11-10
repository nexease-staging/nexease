"""Owner-approved referrals and review-only commission accruals in integer paise.

No bank transfer is initiated here. The calculation base is verified subscription
receipts excluding verified GST, less refunds excluding their verified GST.
Missing or stale tax evidence holds the calculation; payouts remain review-only.
"""
from datetime import datetime
from mongoengine.connection import get_db
from .entitlements import org_lock

FIRST_PERCENT = 20
RENEWAL_PERCENT = 10


def commission_paise(amount_paise, refunded_paise, percent):
    if any(type(x) is not int for x in (amount_paise, refunded_paise, percent)):
        raise ValueError('Amounts and percentage must be integers.')
    if amount_paise < 0 or not 0 <= refunded_paise <= amount_paise or percent not in (20, 10):
        raise ValueError('Invalid commission calculation.')
    # Positive integer arithmetic, rounded half-up to the nearest paise.
    return ((amount_paise - refunded_paise) * percent + 50) // 100


def net_commission_base(receipt):
    """Require reviewed tax evidence matching this exact gross/refund snapshot."""
    gross = receipt['amount_paise']
    refund = receipt.get('refunded_paise', 0)
    tax = get_db().saas_payment_tax.find_one({'_id': receipt['mode'] + ':' + str(receipt['_id'])})
    if not tax or tax.get('gross_paise') != gross or tax.get('refunded_paise') != refund:
        raise ValueError('Verified GST breakdown required for this payment and refund.')
    gst, refund_gst = tax['gst_paise'], tax['refund_gst_paise']
    validate_tax(gross, refund, gst, refund_gst)
    return gross - gst, refund - refund_gst


def validate_tax(gross, refund, gst, refund_gst):
    if any(type(x) is not int for x in (gross, refund, gst, refund_gst)):
        raise ValueError('Tax amounts must be integer paise.')
    if not (0 <= gst <= gross and 0 <= refund <= gross and 0 <= refund_gst <= min(gst, refund)):
        raise ValueError('Invalid GST breakdown.')
    if refund - refund_gst > gross - gst:
        raise ValueError('Net refund exceeds net subscription amount.')
    if refund == gross and refund_gst != gst:
        raise ValueError('A full refund must reverse all recorded GST.')


def record_tax(payment_id, mode, gst_paise, refund_gst_paise, source, actor, reason):
    """Operator-reviewed invoice evidence; never infer GST from a price or rate."""
    from .models import OwnerAudit
    if mode not in ('test', 'live') or not source.strip() or len(reason.strip()) < 5:
        raise ValueError('Mode, source invoice reference and audit reason are required.')
    db = get_db()
    receipt = db.saas_payments.find_one({'_id': payment_id, 'mode': mode})
    if not receipt:
        raise ValueError('Verified payment not found.')
    with org_lock(receipt['organization_id']):
        receipt = db.saas_payments.find_one({'_id': payment_id, 'mode': mode})
        gross, refund = receipt['amount_paise'], receipt.get('refunded_paise', 0)
        validate_tax(gross, refund, gst_paise, refund_gst_paise)
        evidence = {'gross_paise': gross, 'refunded_paise': refund, 'gst_paise': gst_paise,
                    'refund_gst_paise': refund_gst_paise, 'source': source.strip(),
                    'actor': actor, 'reviewed_at': datetime.utcnow()}
        OwnerAudit(actor=actor, action='commission:tax-review', organization_id=receipt['organization_id'],
                   reason=reason, details={'payment_id': payment_id, 'mode': mode, **evidence}).save()
        db.saas_payment_tax.update_one({'_id': mode + ':' + payment_id}, {'$set': evidence}, upsert=True)
        rebuild(receipt['organization_id'], mode)


def approve_partner(partner_id, name, email, actor):
    from django.core.validators import validate_email
    import re
    if not re.fullmatch(r'[A-Za-z0-9_-]{3,64}', partner_id):
        raise ValueError('Use a 3–64 character partner ID containing letters, digits, hyphens or underscores.')
    if not name.strip() or len(name) > 200:
        raise ValueError('Enter a partner name of at most 200 characters.')
    validate_email(email)
    get_db().saas_partners.update_one({'_id': partner_id}, {'$set': {
        'name': name.strip(), 'email': email.strip().lower(), 'status': 'approved',
        'approved_by': actor, 'updated_at': datetime.utcnow(),
    }}, upsert=True)


def attach_referral(organization_id, partner_id, actor):
    """Owner-only attribution before checkout; immutable once assigned."""
    from apps.organizations.models import Organization
    from .models import Checkout
    organization_id = str(organization_id)
    if not Organization.objects(id=organization_id).first():
        raise ValueError('Organization not found.')
    db = get_db()
    with org_lock(organization_id):
        if not db.saas_partners.find_one({'_id': partner_id, 'status': 'approved'}):
            raise ValueError('An approved partner is required.')
        prior = db.saas_referrals.find_one({'_id': organization_id})
        if prior:
            if prior['partner_id'] == partner_id:
                return
            raise ValueError('This organization already has a referral partner.')
        if Checkout.objects(organization_id=organization_id).first() or db.saas_payments.find_one({'organization_id': organization_id}):
            raise ValueError('Referrals must be assigned before the first checkout. Historical attribution requires review.')
        db.saas_referrals.insert_one({'_id': organization_id, 'partner_id': partner_id,
                                     'assigned_by': actor, 'assigned_at': datetime.utcnow()})


def rebuild(organization_id, mode):
    """Rebuild deterministic review entries after verified receipts/refunds.

    Serializes with checkout/referral changes. Sort by provider payment date, not
    webhook arrival, and isolate sandbox from live. _id prevents replay duplicates.
    """
    organization_id = str(organization_id)
    if mode not in ('test', 'live'):
        raise ValueError('Invalid gateway mode.')
    db = get_db()
    with org_lock(organization_id):
        referral = db.saas_referrals.find_one({'_id': organization_id})
        if not referral:
            return 0
        receipts = list(db.saas_payments.find({'organization_id': organization_id, 'mode': mode}).sort([('paid_at', 1), ('_id', 1)]))
        # Missing provider timestamps cannot establish first-payment ordering.
        if any(type(row.get('paid_at')) is not int for row in receipts):
            raise ValueError('Verified payment dates are required for commission review.')
        for index, receipt in enumerate(receipts):
            percent = FIRST_PERCENT if index == 0 else RENEWAL_PERCENT
            try:
                net, net_refund = net_commission_base(receipt)
                amount = commission_paise(net, net_refund, percent)
                status, hold_reason = 'review_required', ''
            except ValueError as exc:
                net = net_refund = amount = None
                status, hold_reason = 'tax_review_required', str(exc)
            db.saas_commissions.update_one({'_id': mode + ':' + str(receipt['_id'])}, {'$set': {
                'organization_id': organization_id, 'partner_id': referral['partner_id'],
                'payment_id': str(receipt['_id']), 'subscription_id': receipt['subscription_id'],
                'mode': mode, 'percent': percent, 'amount_paise': amount,
                'receipt_paise': receipt['amount_paise'], 'refunded_paise': receipt.get('refunded_paise', 0),
                'paid_at': receipt['paid_at'], 'status': status, 'hold_reason': hold_reason,
                'net_subscription_paise': net, 'net_refund_paise': net_refund,
                'basis': 'subscription_excluding_gst_less_net_refunds', 'updated_at': datetime.utcnow(),
            }}, upsert=True)
        return len(receipts)
