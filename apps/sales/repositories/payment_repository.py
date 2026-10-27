from apps.sales.models import (
    CustomerPayment,
)


class PaymentRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        """
        Return the tenant-scoped payment queryset.
        """

        if not organization:
            return (
                CustomerPayment
                .objects(
                    id=None,
                )
            )

        return (
            CustomerPayment
            .objects(
                organization=organization,
            )
        )

    @staticmethod
    def create_payment(
        *,
        organization,
        payment_number,
        customer,
        payment_date,
        amount,
        payment_method,
        bank_account,
        reference_number,
        allocations,
        notes,
        created_by,
    ):
        """
        Create and persist a customer payment.
        """

        payment = CustomerPayment(
            organization=organization,
            payment_number=payment_number,
            customer=customer,
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
        """
        Retrieve a payment within an organization.
        """

        return (
            PaymentRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                id=payment_id,
            )
            .first()
        )

    @staticmethod
    def get_by_payment_number(
        *,
        organization,
        payment_number,
    ):
        """
        Retrieve payment using its payment number.
        """

        return (
            PaymentRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                payment_number=payment_number,
            )
            .first()
        )

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        """
        List all customer payments.
        """

        return (
            PaymentRepository
            .queryset_for_organization(
                organization=organization,
            )
            .order_by(
                "-payment_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_customer(
        *,
        organization,
        customer,
    ):
        """
        List payments received from one customer.
        """

        return (
            PaymentRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                customer=customer,
            )
            .order_by(
                "-payment_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_invoice(
        *,
        organization,
        invoice,
    ):
        """
        List payments allocated to an invoice.
        """

        return (
            PaymentRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                allocations__invoice=invoice,
            )
            .order_by(
                "-payment_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def get_by_reference_number(
        *,
        organization,
        reference_number,
    ):
        """
        Find payment by external reference or UTR.
        """

        if not reference_number:
            return None

        return (
            PaymentRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                reference_number=(
                    reference_number
                ),
            )
            .first()
        )