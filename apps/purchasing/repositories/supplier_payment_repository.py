from apps.purchasing.models import (
    SupplierPayment,
)


class SupplierPaymentRepository:

    @staticmethod
    def create_payment(
        *,
        organization,
        payment_number,
        supplier,
        payment_date,
        amount,
        payment_method,
        bank_account,
        reference_number,
        allocations,
        notes,
        created_by,
    ):
        payment = SupplierPayment(
            organization=organization,
            payment_number=payment_number,
            supplier=supplier,
            payment_date=payment_date,
            amount=amount,
            payment_method=payment_method,
            bank_account=bank_account,
            reference_number=reference_number,
            allocations=allocations,
            notes=notes,
            created_by=created_by,
        )

        payment.save()

        return payment

    @staticmethod
    def get_by_id(
        *,
        organization,
        payment_id,
    ):
        return SupplierPayment.objects(
            organization=organization,
            id=payment_id,
        ).first()

    @staticmethod
    def get_by_payment_number(
        *,
        organization,
        payment_number,
    ):
        return SupplierPayment.objects(
            organization=organization,
            payment_number=payment_number,
        ).first()

    @staticmethod
    def get_by_reference_number(
        *,
        organization,
        reference_number,
    ):
        if not reference_number:
            return None

        return SupplierPayment.objects(
            organization=organization,
            reference_number=reference_number,
        ).first()

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return SupplierPayment.objects(
            organization=organization,
        ).order_by(
            "-payment_date",
            "-created_at",
        )

    @staticmethod
    def list_by_supplier(
        *,
        organization,
        supplier,
    ):
        return SupplierPayment.objects(
            organization=organization,
            supplier=supplier,
        ).order_by(
            "-payment_date",
            "-created_at",
        )

    @staticmethod
    def list_by_vendor_bill(
        *,
        organization,
        vendor_bill,
    ):
        return SupplierPayment.objects(
            organization=organization,
            allocations__vendor_bill=vendor_bill,
        ).order_by(
            "-payment_date",
            "-created_at",
        )