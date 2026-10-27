from datetime import datetime
from decimal import Decimal

from apps.authorization.services import (
    AuthorizationService,
)

from apps.finance.models import (
    JournalEntry,
)

from apps.finance.repositories.chart_of_account_repository import (
    ChartOfAccountRepository,
)


class GeneralLedgerService:

    @staticmethod
    def _check_permission(
        user,
        permission_code,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not AuthorizationService.has_permission(
            user,
            permission_code,
        ):
            raise PermissionError(
                f"Permission denied: "
                f"{permission_code}"
            )

    @staticmethod
    def _check_organization(
        user,
        organization,
    ):
        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if (
            user.organization.id
            != organization.id
        ):
            raise PermissionError(
                "User does not belong "
                "to this organization."
            )

    @staticmethod
    def _normalize_datetime(
        value,
        field_name,
    ):
        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value

        value = str(
            value
        ).strip()

        if not value:
            return None

        for date_format in (
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                return datetime.strptime(
                    value,
                    date_format,
                )

            except ValueError:
                pass

        raise ValueError(
            f"Invalid {field_name}. "
            "Use YYYY-MM-DD or "
            "YYYY-MM-DDTHH:MM:SS."
        )

    @staticmethod
    def _movement_effect(
        *,
        account,
        debit,
        credit,
    ):
        """
        Convert a journal line into the
        account's natural signed balance.

        Debit-normal:
            debit increases
            credit decreases

        Credit-normal:
            credit increases
            debit decreases
        """

        if (
            account.normal_balance
            == "DEBIT"
        ):
            return (
                debit
                - credit
            )

        if (
            account.normal_balance
            == "CREDIT"
        ):
            return (
                credit
                - debit
            )

        raise ValueError(
            "Invalid account normal balance."
        )

    @staticmethod
    def get_account_ledger(
        *,
        user,
        organization,
        account_id,
        start_date=None,
        end_date=None,
    ):
        GeneralLedgerService._check_permission(
            user,
            "general_ledger.read",
        )

        GeneralLedgerService._check_organization(
            user,
            organization,
        )

        account = (
            ChartOfAccountRepository
            .get_by_id(
                organization=organization,
                account_id=account_id,
            )
        )

        if not account:
            raise ValueError(
                "Chart of account not found."
            )

        start_date = (
            GeneralLedgerService
            ._normalize_datetime(
                start_date,
                "start date",
            )
        )

        end_date = (
            GeneralLedgerService
            ._normalize_datetime(
                end_date,
                "end date",
            )
        )

        if (
            start_date
            and end_date
            and start_date > end_date
        ):
            raise ValueError(
                "Start date cannot be "
                "after end date."
            )

        # ==============================================
        # POSTED JOURNALS ONLY
        # ==============================================

        query = {
            "organization":
                organization,

            "status__in": [
                "POSTED",
                "REVERSED",
            ],
        }

        if end_date:
            query[
                "journal_date__lte"
            ] = end_date

        journals = (
            JournalEntry.objects(
                **query
            )
            .order_by(
                "journal_date",
                "created_at",
            )
        )

        # ==============================================
        # OPENING BALANCE
        # ==============================================

        opening_balance = (
            Decimal("0.00")
        )

        movements = []

        for journal in journals:

            for line in journal.lines:

                if not line.account:
                    continue

                if (
                    line.account.id
                    != account.id
                ):
                    continue

                effect = (
                    GeneralLedgerService
                    ._movement_effect(
                        account=account,
                        debit=line.debit,
                        credit=line.credit,
                    )
                )

                if (
                    start_date
                    and
                    journal.journal_date
                    < start_date
                ):
                    opening_balance += (
                        effect
                    )

                    continue

                movements.append(
                    {
                        "journal":
                            journal,

                        "journal_number":
                            journal.journal_number,

                        "journal_date":
                            journal.journal_date,

                        "description": (
                            line.description
                            or
                            journal.description
                        ),

                        "source_type":
                            journal.source_type,

                        "source_id":
                            journal.source_id,

                        "debit":
                            line.debit,

                        "credit":
                            line.credit,

                        "effect":
                            effect,
                    }
                )

        # ==============================================
        # RUNNING BALANCE
        # ==============================================

        running_balance = (
            opening_balance
        )

        entries = []

        total_debit = (
            Decimal("0.00")
        )

        total_credit = (
            Decimal("0.00")
        )

        for movement in movements:

            running_balance += (
                movement["effect"]
            )

            total_debit += (
                movement["debit"]
            )

            total_credit += (
                movement["credit"]
            )

            entries.append(
                {
                    "journal_number":
                        movement[
                            "journal_number"
                        ],

                    "journal_date":
                        movement[
                            "journal_date"
                        ],

                    "description":
                        movement[
                            "description"
                        ],

                    "source_type":
                        movement[
                            "source_type"
                        ],

                    "source_id":
                        movement[
                            "source_id"
                        ],

                    "debit":
                        movement[
                            "debit"
                        ],

                    "credit":
                        movement[
                            "credit"
                        ],

                    "running_balance":
                        running_balance,
                }
            )

        closing_balance = (
            running_balance
        )

        return {
            "account":
                account,

            "start_date":
                start_date,

            "end_date":
                end_date,

            "opening_balance":
                opening_balance,

            "entries":
                entries,

            "total_debit":
                total_debit,

            "total_credit":
                total_credit,

            "closing_balance":
                closing_balance,
        }