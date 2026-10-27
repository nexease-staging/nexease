import hashlib
import secrets

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from django.contrib.auth.password_validation import (
    validate_password,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)

from apps.accounts.models import User
from apps.accounts.password_reset_models import (
    PasswordResetToken,
)
from apps.accounts.services import (
    AuthenticationService,
)


class PasswordResetError(Exception):
    pass


class PasswordResetService:
    TOKEN_BYTES = 32
    TOKEN_LIFETIME_MINUTES = 30

    @staticmethod
    def normalize_email(value):
        return (
            str(value or "")
            .strip()
            .lower()
        )

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def now():
        return datetime.now(
            timezone.utc
        )

    @classmethod
    def create_reset_token(
        cls,
        *,
        email,
    ):
        normalized_email = (
            cls.normalize_email(email)
        )

        if not normalized_email:
            return None

        user = User.objects(
            email=normalized_email,
            is_active=True,
        ).first()

        # Public forgot-password endpoints must
        # not reveal whether an email exists.
        if not user:
            return None

        now = cls.now()

        # Atomically advance the user's password-reset
        # generation. Under concurrent requests, each
        # request receives a distinct generation number.
        updated_user = (
            User.objects(
                id=user.id,
                is_active=True,
            )
            .modify(
                new=True,
                inc__password_reset_generation=1,
                set__updated_at=now,
            )
        )

        if not updated_user:
            return None

        user = updated_user

        generation = (
            user.password_reset_generation
        )

        # Older unused token records can still be marked
        # used for cleanup and auditing. Generation
        # validation below is the authoritative
        # concurrency protection.
        PasswordResetToken.objects(
            user=user,
            used_at=None,
        ).update(
            set__used_at=now,
        )

        raw_token = secrets.token_urlsafe(
            cls.TOKEN_BYTES
        )

        token_hash = cls.hash_token(
            raw_token
        )

        expires_at = (
            now
            +
            timedelta(
                minutes=(
                    cls
                    .TOKEN_LIFETIME_MINUTES
                )
            )
        )

        token_record = PasswordResetToken(
            user=user,
            token_hash=token_hash,
            generation=generation,
            created_at=now,
            expires_at=expires_at,
        )

        token_record.save()

        # Clean up any unused token records belonging
        # to older reset generations. Generation is the
        # authoritative concurrency guard; this update
        # keeps the persisted token state consistent
        # with that guard.
        PasswordResetToken.objects(
            user=user,
            used_at=None,
            generation__lt=User.objects(id=user.id).only("password_reset_generation").get().password_reset_generation,
        ).update(
            set__used_at=cls.now(),
        )

        return {
            "user": user,
            "token": raw_token,
            "expires_at": expires_at,
        }

    @classmethod
    def get_valid_token_record(
        cls,
        *,
        token,
    ):
        raw_token = str(
            token or ""
        ).strip()

        if not raw_token:
            raise PasswordResetError(
                "This password reset link is invalid or has expired."
            )

        token_hash = cls.hash_token(
            raw_token
        )

        token_record = (
            PasswordResetToken.objects(
                token_hash=token_hash,
            )
            .first()
        )

        if not token_record:
            raise PasswordResetError(
                "This password reset link is invalid or has expired."
            )

        if token_record.used_at is not None:
            raise PasswordResetError(
                "This password reset link is invalid or has expired."
            )

        user = token_record.user

        if (
            not user
            or
            not user.is_active
        ):
            raise PasswordResetError(
                "This password reset link is invalid or has expired."
            )

        current_generation = (
            User.objects(
                id=user.id,
                is_active=True,
            )
            .only(
                "password_reset_generation"
            )
            .first()
        )

        if (
            not current_generation
            or
            token_record.generation
            !=
            current_generation.password_reset_generation
        ):
            raise PasswordResetError(
                "This password reset link is invalid or has expired."
            )

        now = cls.now()

        expires_at = (
            token_record.expires_at
        )

        # MongoEngine may return a naive UTC
        # datetime depending on connection
        # timezone settings. Normalize it before
        # comparing with the aware UTC `now`.
        if (
            expires_at.tzinfo
            is
            None
        ):
            expires_at = (
                expires_at.replace(
                    tzinfo=timezone.utc
                )
            )

        if expires_at <= now:
            raise PasswordResetError(
                "This password reset link is invalid or has expired."
            )

        return token_record

    @classmethod
    def reset_password(
        cls,
        *,
        token,
        new_password,
    ):
        token_record = (
            cls.get_valid_token_record(
                token=token,
            )
        )

        user = token_record.user

        if (
            not user
            or
            not user.is_active
        ):
            raise PasswordResetError(
                "This password reset link is invalid or has expired."
            )

        try:
            validate_password(
                new_password,
                user=user,
            )

        except DjangoValidationError as error:
            raise PasswordResetError(
                " ".join(
                    error.messages
                )
            ) from error

        # Change the password first.
        user.set_password(
            new_password
        )

        user.save()

        now = cls.now()

        # Consume every currently unused reset
        # token belonging to this user. This also
        # prevents any concurrently issued older
        # link from remaining valid.
        PasswordResetToken.objects(
            user=user,
            used_at=None,
        ).update(
            set__used_at=now,
        )

        sessions_revoked = (
            AuthenticationService
            .revoke_user_sessions(
                user
            )
        )

        return {
            "user": user,
            "sessions_revoked": (
                sessions_revoked
            ),
        }