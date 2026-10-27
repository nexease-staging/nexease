from datetime import (
    datetime,
)
from decimal import (
    Decimal,
    InvalidOperation,
)

from mongoengine.errors import (
    NotUniqueError,
)

from apps.products.models import (
    Product,
)
from apps.products.repositories.category_repository import (
    CategoryRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)

class ProductAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class ProductAPIService:

    CREATE_FIELDS = {
        "sku",
        "name",
        "description",
        "category_id",
        "brand",
        "unit",
        "cost_price",
        "selling_price",
        "barcode",
    }

    UPDATE_FIELDS = {
        "sku",
        "name",
        "description",
        "category_id",
        "brand",
        "unit",
        "cost_price",
        "selling_price",
        "barcode",
    }

    REQUIRED_CREATE_FIELDS = {
        "sku",
        "name",
        "category_id",
        "unit",
    }

    @staticmethod
    def _raise_field_error(
        field_name,
        message,
    ):
        raise ProductAPIValidationError(
            details={
                field_name: [
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
            raise ProductAPIValidationError(
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
    ):
        unknown_fields = (
            set(
                payload.keys()
            )
            -
            allowed_fields
        )

        if not unknown_fields:
            return

        details = {
            field_name: [
                "This field is not supported.",
            ]
            for field_name
            in sorted(
                unknown_fields
            )
        }

        raise ProductAPIValidationError(
            message=(
                "Unsupported product fields "
                "were supplied."
            ),
            details=details,
        )

    @staticmethod
    def _normalize_required_string(
        value,
        *,
        field_name,
        maximum_length,
    ):
        if not isinstance(
            value,
            str,
        ):
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} must be "
                    "a string."
                ),
            )

        value = value.strip()

        if not value:
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} is "
                    "required."
                ),
            )

        if len(value) > maximum_length:
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} cannot exceed "
                    f"{maximum_length} characters."
                ),
            )

        return value

    @staticmethod
    def _normalize_optional_string(
        value,
        *,
        field_name,
        maximum_length,
    ):
        if value is None:
            return ""

        if not isinstance(
            value,
            str,
        ):
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} must be "
                    "a string or null."
                ),
            )

        value = value.strip()

        if len(value) > maximum_length:
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} cannot exceed "
                    f"{maximum_length} characters."
                ),
            )

        return value

    @staticmethod
    def _normalize_price(
        value,
        *,
        field_name,
    ):
        if isinstance(
            value,
            bool,
        ):
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} must be "
                    "a valid number."
                ),
            )

        try:

            price = Decimal(
                str(
                    value
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} must be "
                    "a valid number."
                ),
            )

        if not price.is_finite():
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} must be "
                    "a finite number."
                ),
            )

        if price < Decimal("0"):
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} cannot "
                    "be negative."
                ),
            )

        decimal_places = (
            -price.as_tuple().exponent
            if price.as_tuple().exponent < 0
            else 0
        )

        if decimal_places > 2:
            ProductAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} cannot have "
                    "more than 2 decimal places."
                ),
            )

        return price.quantize(
            Decimal("0.01")
        )

    @staticmethod
    def _resolve_category(
        *,
        organization,
        category_id,
    ):
        category_id = (
            ProductAPIService
            ._normalize_required_string(
                category_id,
                field_name="category_id",
                maximum_length=100,
            )
        )

        category = (
            CategoryRepository
            .get_active_by_id(
                organization=organization,
                category_id=category_id,
            )
        )

        if not category:
            ProductAPIService._raise_field_error(
                "category_id",
                (
                    "Active category was not found "
                    "in the current organization."
                ),
            )

        return category

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        ProductAPIService._validate_payload_object(
            payload
        )

        ProductAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                ProductAPIService
                .CREATE_FIELDS
            ),
        )

        missing_fields = (
            ProductAPIService
            .REQUIRED_CREATE_FIELDS
            -
            set(
                payload.keys()
            )
        )

        if missing_fields:

            details = {
                field_name: [
                    (
                        f"{field_name} is "
                        "required."
                    ),
                ]
                for field_name
                in sorted(
                    missing_fields
                )
            }

            raise ProductAPIValidationError(
                details=details,
            )

        sku = (
            ProductAPIService
            ._normalize_required_string(
                payload.get(
                    "sku"
                ),
                field_name="sku",
                maximum_length=50,
            )
            .upper()
        )

        name = (
            ProductAPIService
            ._normalize_required_string(
                payload.get(
                    "name"
                ),
                field_name="name",
                maximum_length=200,
            )
        )

        unit = (
            ProductAPIService
            ._normalize_required_string(
                payload.get(
                    "unit"
                ),
                field_name="unit",
                maximum_length=30,
            )
        )

        category = (
            ProductAPIService
            ._resolve_category(
                organization=organization,
                category_id=payload.get(
                    "category_id"
                ),
            )
        )

        description = (
            ProductAPIService
            ._normalize_optional_string(
                payload.get(
                    "description",
                    "",
                ),
                field_name="description",
                maximum_length=1000,
            )
        )

        brand = (
            ProductAPIService
            ._normalize_optional_string(
                payload.get(
                    "brand",
                    "",
                ),
                field_name="brand",
                maximum_length=100,
            )
        )

        barcode = (
            ProductAPIService
            ._normalize_optional_string(
                payload.get(
                    "barcode",
                    "",
                ),
                field_name="barcode",
                maximum_length=100,
            )
        )

        cost_price = (
            ProductAPIService
            ._normalize_price(
                payload.get(
                    "cost_price",
                    0,
                ),
                field_name="cost_price",
            )
        )

        selling_price = (
            ProductAPIService
            ._normalize_price(
                payload.get(
                    "selling_price",
                    0,
                ),
                field_name="selling_price",
            )
        )

        return {
            "sku":
                sku,
            "name":
                name,
            "description":
                description,
            "category":
                category,
            "brand":
                brand,
            "unit":
                unit,
            "cost_price":
                cost_price,
            "selling_price":
                selling_price,
            "barcode":
                barcode,
        }

    @staticmethod
    def validate_update_payload(
        *,
        organization,
        payload,
    ):
        ProductAPIService._validate_payload_object(
            payload
        )

        if not payload:
            raise ProductAPIValidationError(
                details={
                    "body": [
                        (
                            "At least one editable "
                            "field is required."
                        ),
                    ],
                },
            )

        ProductAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                ProductAPIService
                .UPDATE_FIELDS
            ),
        )

        updates = {}

        if "sku" in payload:
            updates["sku"] = (
                ProductAPIService
                ._normalize_required_string(
                    payload["sku"],
                    field_name="sku",
                    maximum_length=50,
                )
                .upper()
            )

        if "name" in payload:
            updates["name"] = (
                ProductAPIService
                ._normalize_required_string(
                    payload["name"],
                    field_name="name",
                    maximum_length=200,
                )
            )

        if "unit" in payload:
            updates["unit"] = (
                ProductAPIService
                ._normalize_required_string(
                    payload["unit"],
                    field_name="unit",
                    maximum_length=30,
                )
            )

        if "category_id" in payload:
            updates["category"] = (
                ProductAPIService
                ._resolve_category(
                    organization=organization,
                    category_id=payload[
                        "category_id"
                    ],
                )
            )

        if "description" in payload:
            updates["description"] = (
                ProductAPIService
                ._normalize_optional_string(
                    payload["description"],
                    field_name="description",
                    maximum_length=1000,
                )
            )

        if "brand" in payload:
            updates["brand"] = (
                ProductAPIService
                ._normalize_optional_string(
                    payload["brand"],
                    field_name="brand",
                    maximum_length=100,
                )
            )

        if "barcode" in payload:
            updates["barcode"] = (
                ProductAPIService
                ._normalize_optional_string(
                    payload["barcode"],
                    field_name="barcode",
                    maximum_length=100,
                )
            )

        if "cost_price" in payload:
            updates["cost_price"] = (
                ProductAPIService
                ._normalize_price(
                    payload["cost_price"],
                    field_name="cost_price",
                )
            )

        if "selling_price" in payload:
            updates["selling_price"] = (
                ProductAPIService
                ._normalize_price(
                    payload["selling_price"],
                    field_name="selling_price",
                )
            )

        return updates

    @staticmethod
    def create_product(
        *,
        organization,
        payload,
    ):
        if not organization:
            raise PermissionError(
                "Organization context unavailable."
            )

        values = (
            ProductAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        if (
            ProductRepository
            .sku_exists(
                organization=organization,
                sku=values["sku"],
            )
        ):
            raise ProductAPIValidationError(
                message=(
                    "A product with this SKU "
                    "already exists."
                ),
                details={
                    "sku": [
                        (
                            "SKU must be unique within "
                            "the current organization."
                        ),
                    ],
                },
            )

        current_time = datetime.utcnow()

        product = Product(
            organization=organization,
            sku=values["sku"],
            name=values["name"],
            description=values[
                "description"
            ],
            category=values["category"],
            brand=values["brand"],
            unit=values["unit"],
            cost_price=values[
                "cost_price"
            ],
            selling_price=values[
                "selling_price"
            ],
            barcode=values["barcode"],
            is_active=True,
            created_at=current_time,
            updated_at=current_time,
        )

        try:

            product.save()

        except NotUniqueError:

            raise ProductAPIValidationError(
                message=(
                    "A product with this SKU "
                    "already exists."
                ),
                details={
                    "sku": [
                        (
                            "SKU must be unique within "
                            "the current organization."
                        ),
                    ],
                },
            )

        return product

    @staticmethod
    def get_product(
        *,
        organization,
        product_id,
    ):
        if not organization:
            raise PermissionError(
                "Organization context unavailable."
            )

        product = (
            ProductRepository
            .get_by_id(
                organization=organization,
                product_id=product_id,
            )
        )

        if not product:
            raise LookupError(
                "Product not found."
            )

        return product

    @staticmethod
    def update_product(
        *,
        organization,
        product_id,
        payload,
    ):
        product = (
            ProductAPIService
            .get_product(
                organization=organization,
                product_id=product_id,
            )
        )

        if not product.is_active:
            raise ProductAPIValidationError(
                message=(
                    "Inactive product cannot "
                    "be updated."
                ),
                details={
                    "is_active": [
                        (
                            "Activate the product "
                            "before updating it."
                        ),
                    ],
                },
            )

        updates = (
            ProductAPIService
            .validate_update_payload(
                organization=organization,
                payload=payload,
            )
        )

        if "sku" in updates:

            if (
                ProductRepository
                .sku_exists(
                    organization=organization,
                    sku=updates["sku"],
                    exclude_product_id=(
                        product.id
                    ),
                )
            ):
                raise ProductAPIValidationError(
                    message=(
                        "A product with this SKU "
                        "already exists."
                    ),
                    details={
                        "sku": [
                            (
                                "SKU must be unique "
                                "within the current "
                                "organization."
                            ),
                        ],
                    },
                )

        mongo_updates = {
            f"set__{field_name}":
                value
            for field_name, value
            in updates.items()
        }

        mongo_updates[
            "set__updated_at"
        ] = datetime.utcnow()

        try:

            updated_product = (
                Product.objects(
                    organization=organization,
                    id=product.id,
                    is_active=True,
                )
                .modify(
                    new=True,
                    **mongo_updates,
                )
            )

        except NotUniqueError:

            raise ProductAPIValidationError(
                message=(
                    "A product with this SKU "
                    "already exists."
                ),
                details={
                    "sku": [
                        (
                            "SKU must be unique within "
                            "the current organization."
                        ),
                    ],
                },
            )

        if not updated_product:
            raise LookupError(
                "Product not found."
            )

        return updated_product

    @staticmethod
    def activate_product(
        *,
        organization,
        product_id,
    ):
        product = (
            ProductAPIService
            .get_product(
                organization=organization,
                product_id=product_id,
            )
        )

        if product.is_active:
            return product

        activated_product = (
            Product.objects(
                organization=organization,
                id=product.id,
            )
            .modify(
                new=True,
                set__is_active=True,
                set__updated_at=(
                    datetime.utcnow()
                ),
            )
        )

        if not activated_product:
            raise LookupError(
                "Product not found."
            )

        return activated_product

    @staticmethod
    def deactivate_product(
        *,
        organization,
        product_id,
    ):
        product = (
            ProductAPIService
            .get_product(
                organization=organization,
                product_id=product_id,
            )
        )

        if not product.is_active:
            return product

        deactivated_product = (
            Product.objects(
                organization=organization,
                id=product.id,
            )
            .modify(
                new=True,
                set__is_active=False,
                set__updated_at=(
                    datetime.utcnow()
                ),
            )
        )

        if not deactivated_product:
            raise LookupError(
                "Product not found."
            )

        return deactivated_product