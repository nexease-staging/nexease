from datetime import datetime

from mongoengine import (
    DateTimeField,
    Document,
    ReferenceField,
    StringField,
    ValidationError,
)

from apps.accounts.models import User

from apps.organizations.models import (
    Organization,
)
import hashlib
import hmac

from django.conf import settings

class AuthenticationAuditLog(Document):

    event_type = StringField(
        required=True,
        choices=(
            "LOGIN_SUCCESS",
            "LOGIN_FAILED",
            "LOGIN_BLOCKED",
            "LOGOUT",
            "LOGOUT_ALL",
        ),
    )

    user = ReferenceField(
        User,
        required=False,
        null=True,
    )

    organization = ReferenceField(
        Organization,
        required=False,
        null=True,
    )

    identifier = StringField(
        required=False,
        max_length=255,
    )

    ip_address = StringField(
        required=False,
        max_length=100,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    integrity_hash = StringField(
        required=True,
        null=True,
        max_length=64,
    )

    meta = {
        "collection":
            "authentication_audit_logs",

        "indexes": [
            "organization",
            "event_type",
            "identifier",
            "ip_address",
            "-created_at",
        ],
    }

    def _build_integrity_payload(
        self,
    ):
        user_reference = (
            self._data.get("user")
        )

        organization_reference = (
            self._data.get(
                "organization"
            )
        )

        user_id = (
            str(
                getattr(
                    user_reference,
                    "id",
                    getattr(
                        user_reference,
                        "pk",
                        "",
                    ),
                )
            )
            if user_reference
            else ""
        )

        organization_id = (
            str(
                getattr(
                    organization_reference,
                    "id",
                    getattr(
                        organization_reference,
                        "pk",
                        "",
                    ),
                )
            )
            if organization_reference
            else ""
        )

        created_at_value = (
            self.created_at
            .replace(
                microsecond=(
                    self.created_at.microsecond
                    // 1000
                    *
                    1000
                )
            )
            .isoformat()

            if self.created_at
            else ""
        )

        return "|".join(
            [
                self.event_type
                or "",

                user_id,

                organization_id,

                self.identifier
                or "",

                self.ip_address
                or "",

                created_at_value,
            ]
        )


    def generate_integrity_hash(
        self,
    ):
        payload = (
            self._build_integrity_payload()
            .encode(
                "utf-8"
            )
        )

        secret = (
            str(
                settings.SECRET_KEY
            )
            .encode(
                "utf-8"
            )
        )

        return hmac.new(
            secret,
            payload,
            hashlib.sha256,
        ).hexdigest()


    def verify_integrity(
        self,
    ):
        if not self.integrity_hash:
            return False

        expected_hash = (
            self.generate_integrity_hash()
        )

        return hmac.compare_digest(
            self.integrity_hash,
            expected_hash,
        )


    def save(
        self,
        *args,
        **kwargs,
    ):
        # ==================================================
        # IMMUTABILITY
        # ==================================================

        if self.pk:

            existing = (
                AuthenticationAuditLog.objects(
                    id=self.pk
                )
                .first()
            )

            if existing:

                raise ValueError(
                    "Authentication audit logs "
                    "are immutable."
                )

        # ==================================================
        # HASH NEW RECORD
        # ==================================================

        if not self.created_at:
            self.created_at = (
                datetime.utcnow()
            )

        self.integrity_hash = (
            self.generate_integrity_hash()
        )

        return super().save(
            *args,
            **kwargs,
        )