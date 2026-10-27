from datetime import (
    datetime,
)

from bson import (
    ObjectId,
)

from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.sales.repositories.sales_return_repository import (
    SalesReturnRepository,
)
from apps.sales.services.sales_return_service import (
    SalesReturnService,
)


class SalesReturnAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Sales return validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class SalesReturnAPIStateError(
    ValueError
):

    def __init__(
        self,
        *,
        message,
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class SalesReturnAPIService:

    CREATE_FIELDS = {
        "invoice_id",
        "return_date",
        "items",
        "reason",
        "notes",
    }

    ITEM_FIELDS = {
        "product_id",
        "quantity",
        "reason",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise SalesReturnAPIValidationError(
            details={
                field: [
                    message,
                ],
            },
        )

    @staticmethod
    def _validate_payload_object(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise SalesReturnAPIValidationError(
                details={
                    "body": [
                        (
                            "JSON body must be "
                            "an object."
                        ),
                    ],
                },
            )

    @staticmethod
    def _validate_allowed_fields(
        payload,
        *,
        allowed_fields,
        prefix=None,
    ):
        unknown_fields = (
            set(
                payload.keys()
            )
            -
            allowed_fields
        )

        if unknown_fields:
            raise SalesReturnAPIValidationError(
                details={
                    (
                        f"{prefix}.{field}"
                        if prefix
                        else field
                    ): [
                        (
                            "This field is not "
                            "supported."
                        ),
                    ]
                    for field
                    in sorted(
                        unknown_fields
                    )
                },
            )

    @staticmethod
    def _normalize_identifier(
        value,
        *,
        field,
    ):
        if (
            not isinstance(
                value,
                str,
            )
            or
            not ObjectId.is_valid(
                value.strip()
            )
        ):
            SalesReturnAPIService._raise_field_error(
                field,
                (
                    "This field must contain a "
                    "valid ObjectId."
                ),
            )

        return value.strip()

    @staticmethod
    def _normalize_datetime(
        value,
        *,
        field,
    ):
        if value in (
            None,
            "",
        ):
            return None

        if not isinstance(
            value,
            str,
        ):
            SalesReturnAPIService._raise_field_error(
                field,
                (
                    "This field must be an "
                    "ISO-8601 date or datetime."
                ),
            )

        normalized = value.strip()

        if normalized.endswith(
            "Z"
        ):
            normalized = (
                normalized[:-1]
                +
                "+00:00"
            )

        try:
            return datetime.fromisoformat(
                normalized
            )

        except ValueError:
            SalesReturnAPIService._raise_field_error(
                field,
                (
                    "Enter a valid ISO-8601 "
                    "date or datetime."
                ),
            )

    @staticmethod
    def _normalize_text(
        value,
        *,
        field,
        maximum_length,
    ):
        if value in (
            None,
            "",
        ):
            return ""

        if not isinstance(
            value,
            str,
        ):
            SalesReturnAPIService._raise_field_error(
                field,
                "This field must be text.",
            )

        normalized = value.strip()

        if (
            len(
                normalized
            )
            >
            maximum_length
        ):
            SalesReturnAPIService._raise_field_error(
                field,
                (
                    "Ensure this field has no "
                    f"more than {maximum_length} "
                    "characters."
                ),
            )

        return normalized

    @staticmethod
    def _normalize_quantity(
        value,
        *,
        field,
    ):
        if value in (
            None,
            "",
        ):
            SalesReturnAPIService._raise_field_error(
                field,
                "This field is required.",
            )

        if isinstance(
            value,
            bool,
        ):
            SalesReturnAPIService._raise_field_error(
                field,
                (
                    "Enter a number greater "
                    "than zero."
                ),
            )

        try:
            normalized = str(
                value
            ).strip()

            if (
                not normalized
                or
                float(
                    normalized
                )
                <=
                0
            ):
                raise ValueError

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            SalesReturnAPIService._raise_field_error(
                field,
                (
                    "Enter a number greater "
                    "than zero."
                ),
            )

        return normalized

    @staticmethod
    def _normalize_items(
        *,
        organization,
        items,
    ):
        if not isinstance(
            items,
            list,
        ):
            SalesReturnAPIService._raise_field_error(
                "items",
                "This field must be a list.",
            )

        if not items:
            SalesReturnAPIService._raise_field_error(
                "items",
                (
                    "At least one return item "
                    "is required."
                ),
            )

        normalized_items = []
        seen_product_ids = set()
        errors = {}

        for index, item in enumerate(
            items
        ):
            prefix = (
                f"items.{index}"
            )

            if not isinstance(
                item,
                dict,
            ):
                errors[
                    prefix
                ] = [
                    (
                        "Each return item must "
                        "be an object."
                    ),
                ]
                continue

            unknown_fields = (
                set(
                    item.keys()
                )
                -
                SalesReturnAPIService.ITEM_FIELDS
            )

            for field in sorted(
                unknown_fields
            ):
                errors[
                    f"{prefix}.{field}"
                ] = [
                    (
                        "This field is not "
                        "supported."
                    ),
                ]

            product_id = item.get(
                "product_id"
            )

            if (
                not isinstance(
                    product_id,
                    str,
                )
                or
                not ObjectId.is_valid(
                    product_id.strip()
                )
            ):
                errors[
                    f"{prefix}.product_id"
                ] = [
                    (
                        "This field must contain "
                        "a valid ObjectId."
                    ),
                ]
                continue

            product_id = (
                product_id.strip()
            )

            if (
                product_id
                in
                seen_product_ids
            ):
                errors[
                    f"{prefix}.product_id"
                ] = [
                    (
                        "Duplicate products are "
                        "not allowed."
                    ),
                ]
                continue

            seen_product_ids.add(
                product_id
            )

            product = (
                ProductRepository
                .get_by_id(
                    organization=organization,
                    product_id=product_id,
                )
            )

            if not product:
                errors[
                    f"{prefix}.product_id"
                ] = [
                    "Product was not found.",
                ]
                continue

            try:
                quantity = (
                    SalesReturnAPIService
                    ._normalize_quantity(
                        item.get(
                            "quantity"
                        ),
                        field=(
                            f"{prefix}.quantity"
                        ),
                    )
                )

                reason = (
                    SalesReturnAPIService
                    ._normalize_text(
                        item.get(
                            "reason"
                        ),
                        field=(
                            f"{prefix}.reason"
                        ),
                        maximum_length=500,
                    )
                )

            except SalesReturnAPIValidationError as exc:
                errors.update(
                    exc.details
                )
                continue

            normalized_items.append({
                "product":
                    product,
                "quantity":
                    quantity,
                "reason":
                    reason,
            })

        if errors:
            raise SalesReturnAPIValidationError(
                details=errors,
            )

        return normalized_items

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        SalesReturnAPIService._validate_payload_object(
            payload
        )

        SalesReturnAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                SalesReturnAPIService
                .CREATE_FIELDS
            ),
        )

        invoice_id = (
            SalesReturnAPIService
            ._normalize_identifier(
                payload.get(
                    "invoice_id"
                ),
                field="invoice_id",
            )
        )

        invoice = (
            InvoiceRepository
            .get_by_id(
                organization=organization,
                invoice_id=invoice_id,
            )
        )

        if not invoice:
            SalesReturnAPIService._raise_field_error(
                "invoice_id",
                "Invoice was not found.",
            )

        items = (
            SalesReturnAPIService
            ._normalize_items(
                organization=organization,
                items=payload.get(
                    "items"
                ),
            )
        )

        return {
            "invoice":
                invoice,
            "items":
                items,
            "return_date": (
                SalesReturnAPIService
                ._normalize_datetime(
                    payload.get(
                        "return_date"
                    ),
                    field="return_date",
                )
            ),
            "reason": (
                SalesReturnAPIService
                ._normalize_text(
                    payload.get(
                        "reason"
                    ),
                    field="reason",
                    maximum_length=500,
                )
            ),
            "notes": (
                SalesReturnAPIService
                ._normalize_text(
                    payload.get(
                        "notes"
                    ),
                    field="notes",
                    maximum_length=1000,
                )
            ),
        }

    @staticmethod
    def get_sales_return(
        *,
        organization,
        sales_return_id,
    ):
        normalized_id = (
            SalesReturnAPIService
            ._normalize_identifier(
                sales_return_id,
                field="sales_return_id",
            )
        )

        sales_return = (
            SalesReturnRepository
            .get_by_id(
                organization=organization,
                return_id=normalized_id,
            )
        )

        if not sales_return:
            raise LookupError(
                "Sales return not found."
            )

        return sales_return

    @staticmethod
    def create_sales_return(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            SalesReturnAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                SalesReturnService
                .create_return(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise SalesReturnAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "sales_return": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def confirm_sales_return(
        *,
        user,
        organization,
        sales_return_id,
    ):
        sales_return = (
            SalesReturnAPIService
            .get_sales_return(
                organization=organization,
                sales_return_id=(
                    sales_return_id
                ),
            )
        )

        try:
            return (
                SalesReturnService
                .confirm_return(
                    user=user,
                    organization=organization,
                    sales_return=sales_return,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise SalesReturnAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "sales_return": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def cancel_sales_return(
        *,
        user,
        organization,
        sales_return_id,
    ):
        sales_return = (
            SalesReturnAPIService
            .get_sales_return(
                organization=organization,
                sales_return_id=(
                    sales_return_id
                ),
            )
        )

        try:
            return (
                SalesReturnService
                .cancel_return(
                    user=user,
                    organization=organization,
                    sales_return=sales_return,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise SalesReturnAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "sales_return": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc