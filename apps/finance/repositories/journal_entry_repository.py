from datetime import (
    datetime,
)

from mongoengine.errors import (
    ValidationError,
)

from apps.finance.models import (
    JournalEntry,
)


class JournalEntryRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return JournalEntry.objects(
            organization=organization,
        )

    @staticmethod
    def create_journal(
        *,
        organization,
        journal_number,
        journal_date,
        description,
        source_type,
        source_id,
        lines,
        total_debit,
        total_credit,
        created_by,
    ):
        journal = JournalEntry(
            organization=organization,
            journal_number=journal_number,
            journal_date=journal_date,
            description=description,
            source_type=source_type,
            source_id=source_id,
            lines=lines,
            total_debit=total_debit,
            total_credit=total_credit,
            status="DRAFT",
            posted_at=None,
            reversed_at=None,
            reversal_of=None,
            reversed_by=None,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        journal.save()

        return journal

    @staticmethod
    def get_by_id(
        *,
        organization,
        journal_id,
    ):
        try:
            return (
                JournalEntryRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=journal_id,
                )
                .first()
            )

        except (
            ValidationError,
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def get_by_number(
        *,
        organization,
        journal_number,
    ):
        return (
            JournalEntryRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                journal_number=str(
                    journal_number
                    or
                    ""
                ).strip(),
            )
            .first()
        )

    @staticmethod
    def get_by_source(
        *,
        organization,
        source_type,
        source_id,
    ):
        return (
            JournalEntryRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                source_type=str(
                    source_type
                    or
                    ""
                ).strip().upper(),
                source_id=str(
                    source_id
                    or
                    ""
                ).strip(),
            )
            .first()
        )

    @staticmethod
    def list_journals(
        *,
        organization,
        status=None,
        source_type=None,
    ):
        query = {}

        if status is not None:
            query[
                "status"
            ] = str(
                status
            ).strip().upper()

        if source_type is not None:
            query[
                "source_type"
            ] = str(
                source_type
            ).strip().upper()

        return (
            JournalEntryRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                **query
            )
            .order_by(
                "-journal_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def update_draft(
        *,
        journal,
        journal_date=None,
        description=None,
        lines=None,
        total_debit=None,
        total_credit=None,
    ):
        if journal_date is not None:
            journal.journal_date = (
                journal_date
            )

        if description is not None:
            journal.description = (
                str(
                    description
                ).strip()
            )

        if lines is not None:
            journal.lines = lines

        if total_debit is not None:
            journal.total_debit = (
                total_debit
            )

        if total_credit is not None:
            journal.total_credit = (
                total_credit
            )

        journal.updated_at = (
            datetime.utcnow()
        )

        journal.save()

        return journal

    @staticmethod
    def mark_posted(
        *,
        journal,
        posted_at,
    ):
        journal.status = "POSTED"
        journal.posted_at = posted_at
        journal.updated_at = (
            datetime.utcnow()
        )

        journal.save()

        return journal

    @staticmethod
    def mark_reversed(
        *,
        journal,
        reversal_journal,
        reversed_at,
    ):
        journal.status = "REVERSED"
        journal.reversed_at = reversed_at
        journal.reversed_by = (
            reversal_journal
        )
        journal.updated_at = (
            datetime.utcnow()
        )

        journal.save()

        return journal

    @staticmethod
    def link_reversal(
        *,
        reversal_journal,
        original_journal,
    ):
        reversal_journal.reversal_of = (
            original_journal
        )

        reversal_journal.updated_at = (
            datetime.utcnow()
        )

        reversal_journal.save()

        return reversal_journal