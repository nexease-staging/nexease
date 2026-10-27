from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from apps.authorization.services import (
    AuthorizationService,
)

from apps.finance.models import (
    JournalLine,
)

from apps.finance.repositories.chart_of_account_repository import (
    ChartOfAccountRepository,
)

from apps.finance.repositories.journal_entry_repository import (
    JournalEntryRepository,
)


class JournalEntryService:

    VALID_SOURCE_TYPES = {
        "MANUAL",
        "PAYROLL", "SALARY_PAYMENT", "EMPLOYEE_ADVANCE", "DAILY_EXPENSE",
            "SALES_INVOICE",
        "CUSTOMER_PAYMENT",
        "SALES_CREDIT_NOTE",
        "VENDOR_BILL",
        "SUPPLIER_PAYMENT",
        "VENDOR_DEBIT_NOTE",
        "BANK_TRANSACTION",
        "OPENING_BALANCE",
        "REVERSAL",
    }

    VALID_STATUSES = {
        "DRAFT",
        "POSTED",
        "REVERSED",
    }

    # ==================================================
    # COMMON VALIDATION
    # ==================================================

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
    def _to_decimal(
        value,
        field_name,
    ):
        try:
            amount = Decimal(
                str(
                    value
                    if value is not None
                    else "0"
                )
            )

        except (
            InvalidOperation,
            ValueError,
            TypeError,
        ):
            raise ValueError(
                f"Invalid {field_name}."
            )

        return amount.quantize(
            Decimal("0.01")
        )

    @staticmethod
    def _normalize_source_type(
        source_type,
    ):
        source_type = str(
            source_type
            or "MANUAL"
        ).strip().upper()

        if (
            source_type
            not in JournalEntryService
            .VALID_SOURCE_TYPES
        ):
            raise ValueError(
                "Invalid journal source type."
            )

        return source_type

    @staticmethod
    def _generate_journal_number():
        return (
            "JE-"
            + uuid4().hex[
                :12
            ].upper()
        )

    # ==================================================
    # JOURNAL LINE BUILDER
    # ==================================================

    @staticmethod
    def _build_lines(
        *,
        organization,
        raw_lines,
        source_type,
    ):
        if not raw_lines:
            raise ValueError(
                "Journal must contain "
                "at least two lines."
            )

        if not isinstance(
            raw_lines,
            list,
        ):
            raise ValueError(
                "Journal lines must be a list."
            )

        if len(raw_lines) < 2:
            raise ValueError(
                "Journal must contain "
                "at least two lines."
            )

        lines = []

        total_debit = Decimal(
            "0.00"
        )

        total_credit = Decimal(
            "0.00"
        )

        for raw_line in raw_lines:

            account = raw_line.get(
                "account"
            )

            account_id = raw_line.get(
                "account_id"
            )

            if (
                not account
                and account_id
            ):
                account = (
                    ChartOfAccountRepository
                    .get_by_id(
                        organization=organization,
                        account_id=account_id,
                    )
                )

            if not account:
                raise ValueError(
                    "Journal account is required."
                )

            if (
                account.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Journal account does not "
                    "belong to this organization."
                )

            if not account.is_active:
                raise ValueError(
                    f"Account "
                    f"{account.account_code} "
                    "is inactive."
                )

            if (
                source_type == "MANUAL"
                and
                not account
                .allow_manual_posting
            ):
                raise ValueError(
                    f"Manual posting is not "
                    f"allowed for account "
                    f"{account.account_code} "
                    f"{account.account_name}."
                )

            debit = (
                JournalEntryService
                ._to_decimal(
                    raw_line.get(
                        "debit",
                        0,
                    ),
                    "debit amount",
                )
            )

            credit = (
                JournalEntryService
                ._to_decimal(
                    raw_line.get(
                        "credit",
                        0,
                    ),
                    "credit amount",
                )
            )

            if (
                debit < Decimal("0")
                or
                credit < Decimal("0")
            ):
                raise ValueError(
                    "Journal debit and credit "
                    "amounts cannot be negative."
                )

            if (
                debit > Decimal("0")
                and
                credit > Decimal("0")
            ):
                raise ValueError(
                    "A journal line cannot contain "
                    "both debit and credit amounts."
                )

            if (
                debit == Decimal("0")
                and
                credit == Decimal("0")
            ):
                raise ValueError(
                    "A journal line must contain "
                    "either a debit or credit amount."
                )

            description = str(
                raw_line.get(
                    "description",
                    "",
                )
                or ""
            ).strip()

            line = JournalLine(
                account=account,
                description=description,
                debit=debit,
                credit=credit,
            )

            lines.append(
                line
            )

            total_debit += debit
            total_credit += credit

        total_debit = total_debit.quantize(
            Decimal("0.01")
        )

        total_credit = total_credit.quantize(
            Decimal("0.01")
        )

        return (
            lines,
            total_debit,
            total_credit,
        )

    # ==================================================
    # BALANCE VALIDATION
    # ==================================================

    @staticmethod
    def _validate_balanced(
        *,
        total_debit,
        total_credit,
    ):
        if (
            total_debit
            <= Decimal("0")
        ):
            raise ValueError(
                "Journal total debit must "
                "be greater than zero."
            )

        if (
            total_credit
            <= Decimal("0")
        ):
            raise ValueError(
                "Journal total credit must "
                "be greater than zero."
            )

        if (
            total_debit
            != total_credit
        ):
            raise ValueError(
                "Journal entry is not balanced. "
                f"Debit: {total_debit}, "
                f"Credit: {total_credit}."
            )

    # ==================================================
    # DUPLICATE SOURCE PROTECTION
    # ==================================================

    @staticmethod
    def _check_duplicate_source(
        *,
        organization,
        source_type,
        source_id,
        exclude_journal=None,
    ):
        source_id = str(
            source_id
            or ""
        ).strip()

        if (
            source_type
            == "MANUAL"
            and not source_id
        ):
            return

        if not source_id:
            return

        existing = (
            JournalEntryRepository
            .get_by_source(
                organization=organization,
                source_type=source_type,
                source_id=source_id,
            )
        )

        if not existing:
            return

        if (
            exclude_journal
            and
            existing.id
            == exclude_journal.id
        ):
            return

        raise ValueError(
            "Journal already exists "
            "for this source."
        )

    # ==================================================
    # CREATE JOURNAL
    # ==================================================

    @staticmethod
    def create_journal(
        *,
        user,
        organization,
        journal_date,
        raw_lines,
        description="",
        source_type="MANUAL",
        source_id="",
    ):
        JournalEntryService._check_permission(
            user,
            "journal_entries.create",
        )

        JournalEntryService._check_organization(
            user,
            organization,
        )

        journal_date = (
            JournalEntryService
            ._parse_journal_date(
                journal_date
            )
        )

        source_type = (
            JournalEntryService
            ._normalize_source_type(
                source_type
            )
        )

        source_id = str(
            source_id
            or ""
        ).strip()

        JournalEntryService._check_duplicate_source(
            organization=organization,
            source_type=source_type,
            source_id=source_id,
        )

        (
            lines,
            total_debit,
            total_credit,
        ) = (
            JournalEntryService
            ._build_lines(
                organization=organization,
                raw_lines=raw_lines,
                source_type=source_type,
            )
        )

        description = str(
            description
            or ""
        ).strip()

        journal = (
            JournalEntryRepository
            .create_journal(
                organization=organization,
                journal_number=(
                    JournalEntryService
                    ._generate_journal_number()
                ),
                journal_date=journal_date,
                description=description,
                source_type=source_type,
                source_id=source_id,
                lines=lines,
                total_debit=total_debit,
                total_credit=total_credit,
                created_by=user,
            )
        )

        return journal

    # ==================================================
    # GET JOURNAL
    # ==================================================

    @staticmethod
    def get_journal(
        *,
        user,
        organization,
        journal_id,
    ):
        JournalEntryService._check_permission(
            user,
            "journal_entries.read",
        )

        JournalEntryService._check_organization(
            user,
            organization,
        )

        journal = (
            JournalEntryRepository
            .get_by_id(
                organization=organization,
                journal_id=journal_id,
            )
        )

        if not journal:
            raise ValueError(
                "Journal entry not found."
            )

        return journal

    # ==================================================
    # LIST JOURNALS
    # ==================================================

    @staticmethod
    def list_journals(
        *,
        user,
        organization,
        status=None,
        source_type=None,
    ):
        JournalEntryService._check_permission(
            user,
            "journal_entries.read",
        )

        JournalEntryService._check_organization(
            user,
            organization,
        )

        if (
            status is not None
        ):
            status = str(
                status
            ).strip().upper()

            if (
                status
                not in JournalEntryService
                .VALID_STATUSES
            ):
                raise ValueError(
                    "Invalid journal status."
                )

        if (
            source_type
            is not None
        ):
            source_type = (
                JournalEntryService
                ._normalize_source_type(
                    source_type
                )
            )

        return (
            JournalEntryRepository
            .list_journals(
                organization=organization,
                status=status,
                source_type=source_type,
            )
        )

    # ==================================================
    # UPDATE DRAFT
    # ==================================================

    @staticmethod
    def update_draft(
        *,
        user,
        organization,
        journal_id,
        journal_date=None,
        raw_lines=None,
        description=None,
    ):
        JournalEntryService._check_permission(
            user,
            "journal_entries.create",
        )

        JournalEntryService._check_organization(
            user,
            organization,
        )

        journal = (
            JournalEntryRepository
            .get_by_id(
                organization=organization,
                journal_id=journal_id,
            )
        )

        if not journal:
            raise ValueError(
                "Journal entry not found."
            )

        if (
            journal.status
            != "DRAFT"
        ):
            raise ValueError(
                "Only draft journal entries "
                "can be updated."
            )

        lines = None
        total_debit = None
        total_credit = None

        if raw_lines is not None:
            (
                lines,
                total_debit,
                total_credit,
            ) = (
                JournalEntryService
                ._build_lines(
                    organization=organization,
                    raw_lines=raw_lines,
                    source_type=(
                        journal.source_type
                    ),
                )
            )
        if journal_date is not None:
            journal_date = (
                JournalEntryService
                ._parse_journal_date(
                    journal_date
                )
            )
        return (
            JournalEntryRepository
            .update_draft(
                journal=journal,
                journal_date=journal_date,
                description=description,
                lines=lines,
                total_debit=total_debit,
                total_credit=total_credit,
            )
        )

    # ==================================================
    # POST JOURNAL
    # ==================================================

    @staticmethod
    def post_journal(
        *,
        user,
        organization,
        journal_id,
    ):
        JournalEntryService._check_permission(
            user,
            "journal_entries.post",
        )

        JournalEntryService._check_organization(
            user,
            organization,
        )

        journal = (
            JournalEntryRepository
            .get_by_id(
                organization=organization,
                journal_id=journal_id,
            )
        )

        if not journal:
            raise ValueError(
                "Journal entry not found."
            )

        if (
            journal.status
            == "POSTED"
        ):
            raise ValueError(
                "Journal entry is already posted."
            )

        if (
            journal.status
            == "REVERSED"
        ):
            raise ValueError(
                "Reversed journal entry "
                "cannot be posted."
            )

        if (
            journal.status
            != "DRAFT"
        ):
            raise ValueError(
                "Only draft journal entries "
                "can be posted."
            )

        if len(journal.lines) < 2:
            raise ValueError(
                "Journal must contain "
                "at least two lines."
            )

        recalculated_debit = sum(
            (
                line.debit
                for line in journal.lines
            ),
            Decimal("0.00"),
        ).quantize(
            Decimal("0.01")
        )

        recalculated_credit = sum(
            (
                line.credit
                for line in journal.lines
            ),
            Decimal("0.00"),
        ).quantize(
            Decimal("0.01")
        )

        if (
            recalculated_debit
            != journal.total_debit
            or
            recalculated_credit
            != journal.total_credit
        ):
            raise ValueError(
                "Journal stored totals do not "
                "match journal lines."
            )

        JournalEntryService._validate_balanced(
            total_debit=(
                recalculated_debit
            ),
            total_credit=(
                recalculated_credit
            ),
        )

        for line in journal.lines:

            account = line.account

            if not account:
                raise ValueError(
                    "Journal line account "
                    "is missing."
                )

            if (
                account.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Journal line account "
                    "belongs to another "
                    "organization."
                )

            if not account.is_active:
                raise ValueError(
                    f"Cannot post to inactive "
                    f"account "
                    f"{account.account_code}."
                )

            if (
                line.debit > Decimal("0")
                and
                line.credit > Decimal("0")
            ):
                raise ValueError(
                    "A journal line cannot "
                    "contain both debit "
                    "and credit amounts."
                )

            if (
                line.debit == Decimal("0")
                and
                line.credit == Decimal("0")
            ):
                raise ValueError(
                    "Journal line contains "
                    "no debit or credit amount."
                )

            if (
                journal.source_type
                == "MANUAL"
                and
                not account
                .allow_manual_posting
            ):
                raise ValueError(
                    f"Manual posting is not "
                    f"allowed for account "
                    f"{account.account_code} "
                    f"{account.account_name}."
                )

        return (
            JournalEntryRepository
            .mark_posted(
                journal=journal,
                posted_at=(
                    datetime.utcnow()
                ),
            )
        )
    @staticmethod
    def reverse_journal(
        *,
        user,
        organization,
        journal_id,
        reversal_date=None,
        description="",
    ):
        JournalEntryService._check_permission(
            user,
            "journal_entries.reverse",
        )

        JournalEntryService._check_organization(
            user,
            organization,
        )

        original = (
            JournalEntryRepository
            .get_by_id(
                organization=organization,
                journal_id=journal_id,
            )
        )

        if not original:
            raise ValueError(
                "Journal entry not found."
            )

        original.reload()

        if original.status == "DRAFT":
            raise ValueError(
                "Draft journal entries "
                "cannot be reversed."
            )

        if original.status == "REVERSED":
            raise ValueError(
                "Journal entry is already reversed."
            )

        if original.status != "POSTED":
            raise ValueError(
                "Only posted journal entries "
                "can be reversed."
            )

        if original.reversed_by:
            raise ValueError(
                "Journal entry already has "
                "a reversal journal."
            )

        if original.source_type == "REVERSAL":
            raise ValueError(
                "A reversal journal cannot "
                "be reversed directly."
            )

        if reversal_date is None:
            reversal_date = (
                datetime.utcnow()
            )

        else:
            reversal_date = (
                JournalEntryService
                ._parse_journal_date(
                    reversal_date
                )
            )

        reversal_source_id = (
            str(
                original.id
            )
        )

        existing_reversal = (
            JournalEntryRepository
            .get_by_source(
                organization=organization,
                source_type="REVERSAL",
                source_id=(
                    reversal_source_id
                ),
            )
        )

        if existing_reversal:
            raise ValueError(
                "Reversal journal already exists."
            )

        reversal_lines = []

        for line in original.lines:

            if not line.account:
                raise ValueError(
                    "Original journal contains "
                    "a line without an account."
                )

            if (
                line.account.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Original journal contains "
                    "an account from another "
                    "organization."
                )

            if (
                line.debit < Decimal("0")
                or
                line.credit < Decimal("0")
            ):
                raise ValueError(
                    "Original journal contains "
                    "invalid negative amounts."
                )

            if (
                line.debit > Decimal("0")
                and
                line.credit > Decimal("0")
            ):
                raise ValueError(
                    "Original journal contains "
                    "a line with both debit "
                    "and credit amounts."
                )

            if (
                line.debit == Decimal("0")
                and
                line.credit == Decimal("0")
            ):
                raise ValueError(
                    "Original journal contains "
                    "a zero-value line."
                )

            reversal_lines.append(
                {
                    "account":
                        line.account,

                    "description": (
                        line.description
                        or
                        (
                            "Reversal of "
                            f"{original.journal_number}"
                        )
                    ),

                    "debit":
                        line.credit,

                    "credit":
                        line.debit,
                }
            )

        if not description:
            description = (
                "Reversal of journal "
                f"{original.journal_number}"
            )

        reversal = (
            JournalEntryService
            .create_journal(
                user=user,
                organization=organization,
                journal_date=(
                    reversal_date
                ),
                raw_lines=(
                    reversal_lines
                ),
                description=(
                    description
                ),
                source_type="REVERSAL",
                source_id=(
                    reversal_source_id
                ),
            )
        )

        reversal = (
            JournalEntryService
            .post_journal(
                user=user,
                organization=organization,
                journal_id=str(
                    reversal.id
                ),
            )
        )

        reversal = (
            JournalEntryRepository
            .link_reversal(
                reversal_journal=(
                    reversal
                ),
                original_journal=(
                    original
                ),
            )
        )

        original = (
            JournalEntryRepository
            .mark_reversed(
                journal=original,
                reversal_journal=(
                    reversal
                ),
                reversed_at=(
                    datetime.utcnow()
                ),
            )
        )

        return {
            "original":
                original,

            "reversal":
                reversal,
        }
    @staticmethod
    def _parse_journal_date(
        value,
    ):
        if value is None:
            return datetime.utcnow()

        if isinstance(
            value,
            datetime,
        ):
            return value

        value = str(
            value
        ).strip()

        if not value:
            return datetime.utcnow()

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
            "Invalid journal_date. "
            "Use YYYY-MM-DD or "
            "YYYY-MM-DDTHH:MM:SS."
        )


