"""Email-ownership verification. Never treats a verified address as SMTP authorization."""

import hashlib, secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.core import signing
from django.core.mail import EmailMessage
from mongoengine.connection import get_db
from apps.accounts.models import User

SALT = "nexease.document-sender.v1"


def address(user):
    return user.email.strip().lower()


def scope(user):
    return {"_id": str(user.id) + ":" + str(user.organization.id)}


def verified(user):
    row = get_db().verified_senders.find_one(scope(user))
    return bool(row and row.get("email") == address(user) and row.get("verified_at"))


def request_link(user, origin=""):
    if verified(user):
        return
    allowed = getattr(settings, "FRONTEND_ORIGINS", [])
    base = (
        origin
        if origin in allowed and origin.startswith("https://")
        else str(getattr(settings, "FRONTEND_BASE_URL", "")).rstrip("/")
    )
    if not base.startswith("https://"):
        raise ValueError(
            "Configure a secure frontend address before email verification."
        )
    nonce = secrets.token_urlsafe(32)
    token = signing.dumps(
        {
            "user": str(user.id),
            "organization": str(user.organization.id),
            "email": address(user),
            "nonce": nonce,
        },
        salt=SALT,
    )
    digest = hashlib.sha256(nonce.encode()).hexdigest()
    get_db().verified_senders.update_one(
        scope(user),
        {
            "$set": {
                "email": address(user),
                "token_digest": digest,
                "requested_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24),
            },
            "$unset": {"verified_at": ""},
        },
        upsert=True,
    )
    link = base + "/verify-email?" + urlencode({"token": token})
    try:
        sent = EmailMessage(
            subject="Verify your NexEase email",
            body="Confirm ownership of your email to share NexEase documents.\n\n"
            + link
            + "\n\nThis single-use link expires in 24 hours. If you did not request it, ignore this email.",
            to=[address(user)],
        ).send(fail_silently=False)
        if sent != 1:
            raise ValueError(
                "Verification email could not be sent. Check system email configuration."
            )
    except Exception:
        get_db().verified_senders.update_one(
            {**scope(user), "token_digest": digest}, {"$unset": {"token_digest": ""}}
        )
        raise


def confirm(token):
    try:
        data = signing.loads(token, salt=SALT, max_age=24 * 3600)
    except signing.BadSignature:
        raise ValueError(
            "This verification link is invalid or expired. Request a new link."
        )
    user = User.objects(
        id=data.get("user"), organization=data.get("organization"), is_active=True
    ).first()
    if not user or address(user) != data.get("email"):
        raise ValueError(
            "Your email address has changed. Request a new verification link."
        )
    digest = hashlib.sha256(str(data.get("nonce", "")).encode()).hexdigest()
    result = get_db().verified_senders.update_one(
        {
            **scope(user),
            "email": address(user),
            "token_digest": digest,
            "expires_at": {"$gt": datetime.utcnow()},
        },
        {"$set": {"verified_at": datetime.utcnow()}, "$unset": {"token_digest": ""}},
    )
    if result.modified_count != 1:
        raise ValueError(
            "This link was already used or replaced. Check your sender status or request a new link."
        )
