from datetime import datetime

from apps.finance.models import (
    BankPaymentSuggestion,
)


class BankPaymentSuggestionRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        """
        Return a tenant-scoped payment suggestion
        queryset for API filtering, searching,
        sorting, and pagination.
        """

        return (
            BankPaymentSuggestion
            .objects(
                organization=organization,
            )
        )

    @staticmethod
    def create_suggestion(
        *,
        organization,
        statement,
        line_number,
        suggestion_type,
        invoice,
        vendor_bill,
        amount,
        confidence,
        match_reason,
        created_by,
    ):
        suggestion = (
            BankPaymentSuggestion(
                organization=organization,
                statement=statement,
                line_number=line_number,
                suggestion_type=(
                    suggestion_type
                ),
                invoice=invoice,
                vendor_bill=vendor_bill,
                amount=amount,
                confidence=confidence,
                match_reason=(
                    match_reason
                ),
                status="PENDING",
                created_by=created_by,
            )
        )

        suggestion.save()

        return suggestion

    @staticmethod
    def get_by_id(
        *,
        organization,
        suggestion_id,
    ):
        return (
            BankPaymentSuggestion
            .objects(
                organization=organization,
                id=suggestion_id,
            )
            .first()
        )

    @staticmethod
    def get_by_statement_line(
        *,
        organization,
        statement,
        line_number,
    ):
        return (
            BankPaymentSuggestion
            .objects(
                organization=organization,
                statement=statement,
                line_number=(
                    str(line_number)
                ),
            )
            .first()
        )

    @staticmethod
    def list_by_organization(
        *,
        organization,
        status=None,
        suggestion_type=None,
    ):
        query = {
            "organization":
                organization,
        }

        if status is not None:
            query["status"] = status

        if suggestion_type is not None:
            query[
                "suggestion_type"
            ] = suggestion_type

        return (
            BankPaymentSuggestion
            .objects(
                **query
            )
            .order_by(
                "-created_at"
            )
        )

    @staticmethod
    def update_status(
        *,
        suggestion,
        status,
        confirmed_at=None,
        rejected_at=None,
    ):
        suggestion.status = status

        suggestion.confirmed_at = (
            confirmed_at
        )

        suggestion.rejected_at = (
            rejected_at
        )

        suggestion.updated_at = (
            datetime.utcnow()
        )

        suggestion.save()

        return suggestion

    @staticmethod
    def mark_executed(
        *,
        suggestion,
        payment_reference,
        executed_at,
    ):
        suggestion.executed_at = (
            executed_at
        )

        suggestion.payment_reference = str(
            payment_reference
        ).strip()

        suggestion.updated_at = (
            datetime.utcnow()
        )

        suggestion.save()

        return suggestion