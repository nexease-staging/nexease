from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMessage


class PasswordResetEmailError(Exception):
    pass


class PasswordResetEmailService:
    @staticmethod
    def get_frontend_base_url():
        base_url = str(
            getattr(
                settings,
                "FRONTEND_BASE_URL",
                "",
            )
            or ""
        ).strip()

        if not base_url:
            raise PasswordResetEmailError(
                "FRONTEND_BASE_URL is not configured."
            )

        return base_url.rstrip("/")

    @classmethod
    def build_reset_url(
        cls,
        *,
        token,
    ):
        encoded_token = quote(
            str(token),
            safe="",
        )

        return (
            f"{cls.get_frontend_base_url()}"
            f"/reset-password"
            f"?token={encoded_token}"
        )

    @classmethod
    def send_reset_email(
        cls,
        *,
        user,
        token,
        expires_at=None,
    ):
        if not user or not user.email:
            raise PasswordResetEmailError(
                "A valid user email is required."
            )

        reset_url = cls.build_reset_url(
            token=token,
        )

        first_name = str(
            getattr(
                user,
                "first_name",
                "",
            )
            or ""
        ).strip()

        greeting = (
            f"Hello {first_name},"
            if first_name
            else
            "Hello,"
        )

        expiry_text = "30 minutes"

        subject = (
            "Reset your Django IMS password"
        )

        body = (
            f"{greeting}\n\n"
            "We received a request to reset "
            "the password for your Django IMS "
            "account.\n\n"
            "Use the link below to choose a "
            "new password:\n\n"
            f"{reset_url}\n\n"
            f"This link expires in {expiry_text} "
            "and can be used only once.\n\n"
            "If you did not request a password "
            "reset, you can ignore this email. "
            "Your password will remain unchanged."
            "\n\n"
            "Django IMS"
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=(
                settings.DEFAULT_FROM_EMAIL
            ),
            to=[
                user.email,
            ],
        )

        try:
            sent_count = email.send(
                fail_silently=False,
            )

        except Exception as error:
            raise PasswordResetEmailError(
                "Password reset email could not "
                "be sent."
            ) from error

        if sent_count != 1:
            raise PasswordResetEmailError(
                "Password reset email could not "
                "be sent."
            )

        return {
            "sent": True,
            "recipient": user.email,
            "reset_url": reset_url,
            "expires_at": expires_at,
        }