from datetime import datetime

from mongoengine.errors import (
    ValidationError,
)

from apps.purchasing.models import (
    VendorDebitNote,
)


class VendorDebitNoteRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return VendorDebitNote.objects(
            organization=organization,
        )

    @staticmethod
    def create_debit_note(
        *,
        organization,
        debit_note_number,
        purchase_return,
        vendor_bill,
        purchase_order,
        supplier,
        debit_note_date,
        items,
        subtotal,
        tax_amount,
        discount_amount,
        total_amount,
        reason,
        notes,
        created_by,
        status="DRAFT",
    ):
        debit_note = VendorDebitNote(
            organization=organization,
            debit_note_number=(
                debit_note_number
            ),
            purchase_return=(
                purchase_return
            ),
            vendor_bill=vendor_bill,
            purchase_order=(
                purchase_order
            ),
            supplier=supplier,
            debit_note_date=(
                debit_note_date
            ),
            items=items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=(
                discount_amount
            ),
            total_amount=total_amount,
            applied_amount=0,
            remaining_credit=(
                total_amount
            ),
            reason=reason,
            notes=notes,
            created_by=created_by,
            status=status,
        )

        debit_note.save()

        return debit_note

    @staticmethod
    def get_by_id(
        *,
        organization,
        debit_note_id,
    ):
        try:
            return (
                VendorDebitNoteRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=debit_note_id,
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
    def get_by_purchase_return(
        *,
        organization,
        purchase_return,
    ):
        return (
            VendorDebitNoteRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                purchase_return=(
                    purchase_return
                ),
            )
            .first()
        )

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return (
            VendorDebitNoteRepository
            .queryset_for_organization(
                organization=organization,
            )
            .order_by(
                "-debit_note_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_supplier(
        *,
        organization,
        supplier,
    ):
        return (
            VendorDebitNoteRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                supplier=supplier,
            )
            .order_by(
                "-debit_note_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_vendor_bill(
        *,
        organization,
        vendor_bill,
    ):
        return (
            VendorDebitNoteRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                vendor_bill=vendor_bill,
            )
            .order_by(
                "-debit_note_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_issued(
        *,
        organization,
        supplier=None,
        vendor_bill=None,
    ):
        queryset = (
            VendorDebitNoteRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                status="ISSUED",
            )
        )

        if supplier is not None:
            queryset = queryset.filter(
                supplier=supplier,
            )

        if vendor_bill is not None:
            queryset = queryset.filter(
                vendor_bill=vendor_bill,
            )

        return queryset.order_by(
            "-debit_note_date",
            "-created_at",
            "-id",
        )

    @staticmethod
    def update_status(
        *,
        debit_note,
        status,
        issued_at=None,
        cancelled_at=None,
    ):
        debit_note.status = status

        if issued_at is not None:
            debit_note.issued_at = (
                issued_at
            )

        if cancelled_at is not None:
            debit_note.cancelled_at = (
                cancelled_at
            )

        debit_note.updated_at = (
            datetime.utcnow()
        )

        debit_note.save()

        return debit_note

    @staticmethod
    def update_application(
        *,
        debit_note,
        applied_amount,
        remaining_credit,
    ):
        debit_note.applied_amount = (
            applied_amount
        )

        debit_note.remaining_credit = (
            remaining_credit
        )

        debit_note.updated_at = (
            datetime.utcnow()
        )

        debit_note.save()

        return debit_note