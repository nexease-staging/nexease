class MigrationSchemaRegistry:

    SCHEMAS = {
        "CATEGORIES": {
            "fields": {
                "name": {
                    "label": "Category Name",
                    "required": True,
                    "aliases": (
                        "category",
                        "category name",
                        "group",
                        "group name",
                        "item group",
                    ),
                },
                "description": {
                    "label": "Description",
                    "required": False,
                    "aliases": (
                        "description",
                        "category description",
                        "remarks",
                    ),
                },
            },
        },

        "PRODUCTS": {
            "fields": {
                "sku": {
                    "label": "SKU",
                    "required": True,
                    "aliases": (
                        "sku",
                        "item code",
                        "product code",
                        "item id",
                        "product id",
                        "stock code",
                    ),
                },
                "name": {
                    "label": "Product Name",
                    "required": True,
                    "aliases": (
                        "name",
                        "product name",
                        "item name",
                        "item description",
                        "product description",
                    ),
                },
                "category": {
                    "label": "Category",
                    "required": False,
                    "aliases": (
                        "category",
                        "category name",
                        "group",
                        "group name",
                        "item group",
                    ),
                },
                "unit": {
                    "label": "Unit",
                    "required": True,
                    "aliases": (
                        "unit",
                        "uom",
                        "unit of measure",
                        "measurement unit",
                    ),
                },
                "brand": {
                    "label": "Brand",
                    "required": False,
                    "aliases": (
                        "brand",
                        "manufacturer",
                        "make",
                    ),
                },
                "description": {
                    "label": "Description",
                    "required": False,
                    "aliases": (
                        "description",
                        "product description",
                        "remarks",
                    ),
                },
                "purchase_price": {
                    "label": "Purchase Price",
                    "required": False,
                    "aliases": (
                        "purchase price",
                        "purchase rate",
                        "buying price",
                        "cost price",
                        "cost",
                    ),
                },
                "selling_price": {
                    "label": "Selling Price",
                    "required": False,
                    "aliases": (
                        "selling price",
                        "sales price",
                        "sale price",
                        "sales rate",
                        "selling rate",
                    ),
                },
            },
        },
        "CUSTOMERS": {
            "label": "Customers",
            "fields": {
                "code": {
                    "label": "Customer Code",
                    "required": True,
                    "aliases": [
                        "customer code",
                        "customer_code",
                        "customer id",
                        "customer_id",
                        "code",
                    ],
                },
                "name": {
                    "label": "Customer Name",
                    "required": True,
                    "aliases": [
                        "customer name",
                        "customer_name",
                        "name",
                    ],
                },
                "email": {
                    "label": "Email",
                    "required": False,
                    "aliases": [
                        "email",
                        "email address",
                        "email_address",
                        "customer email",
                    ],
                },
                "phone": {
                    "label": "Phone",
                    "required": False,
                    "aliases": [
                        "phone",
                        "phone number",
                        "phone_number",
                        "mobile",
                        "mobile number",
                        "contact number",
                    ],
                },
                "gstin": {
                    "label": "GSTIN",
                    "required": False,
                    "aliases": [
                        "gstin",
                        "gst no",
                        "gst number",
                        "gst_number",
                    ],
                },
                "billing_address": {
                    "label": "Billing Address",
                    "required": False,
                    "aliases": [
                        "billing address",
                        "billing_address",
                        "bill to",
                        "bill_to",
                    ],
                },
                "shipping_address": {
                    "label": "Shipping Address",
                    "required": False,
                    "aliases": [
                        "shipping address",
                        "shipping_address",
                        "ship to",
                        "ship_to",
                    ],
                },
                "city": {
                    "label": "City",
                    "required": False,
                    "aliases": [
                        "city",
                    ],
                },
                "state": {
                    "label": "State",
                    "required": False,
                    "aliases": [
                        "state",
                    ],
                },
                "country": {
                    "label": "Country",
                    "required": False,
                    "aliases": [
                        "country",
                    ],
                },
                "pincode": {
                    "label": "Pincode",
                    "required": False,
                    "aliases": [
                        "pincode",
                        "pin code",
                        "postal code",
                        "postal_code",
                        "zip",
                        "zip code",
                    ],
                },
            },
        },
        "SUPPLIERS": {
            "label": "Suppliers",
            "fields": {
                "code": {
                    "label": "Supplier Code",
                    "required": True,
                    "aliases": [
                        "supplier code",
                        "supplier_code",
                        "supplier id",
                        "supplier_id",
                        "vendor code",
                        "vendor_code",
                        "vendor id",
                        "vendor_id",
                        "code",
                    ],
                },
                "name": {
                    "label": "Supplier Name",
                    "required": True,
                    "aliases": [
                        "supplier name",
                        "supplier_name",
                        "vendor name",
                        "vendor_name",
                        "name",
                    ],
                },
                "email": {
                    "label": "Email",
                    "required": False,
                    "aliases": [
                        "email",
                        "email address",
                        "email_address",
                        "supplier email",
                        "vendor email",
                    ],
                },
                "phone": {
                    "label": "Phone",
                    "required": False,
                    "aliases": [
                        "phone",
                        "phone number",
                        "phone_number",
                        "mobile",
                        "mobile number",
                        "contact number",
                    ],
                },
                "gstin": {
                    "label": "GSTIN",
                    "required": False,
                    "aliases": [
                        "gstin",
                        "gst no",
                        "gst number",
                        "gst_number",
                    ],
                },
                "address": {
                    "label": "Address",
                    "required": False,
                    "aliases": [
                        "address",
                        "supplier address",
                        "supplier_address",
                        "vendor address",
                        "vendor_address",
                    ],
                },
                "city": {
                    "label": "City",
                    "required": False,
                    "aliases": [
                        "city",
                    ],
                },
                "state": {
                    "label": "State",
                    "required": False,
                    "aliases": [
                        "state",
                    ],
                },
                "country": {
                    "label": "Country",
                    "required": False,
                    "aliases": [
                        "country",
                    ],
                },
                "pincode": {
                    "label": "Pincode",
                    "required": False,
                    "aliases": [
                        "pincode",
                        "pin code",
                        "postal code",
                        "postal_code",
                        "zip",
                        "zip code",
                    ],
                },
            },
        },
        "WAREHOUSES": {
            "label": "Warehouses",
            "fields": {
                "code": {
                    "label": "Warehouse Code",
                    "required": True,
                    "aliases": [
                        "warehouse code",
                        "warehouse_code",
                        "warehouse id",
                        "warehouse_id",
                        "code",
                    ],
                },
                "name": {
                    "label": "Warehouse Name",
                    "required": True,
                    "aliases": [
                        "warehouse name",
                        "warehouse_name",
                        "name",
                    ],
                },
                "address": {
                    "label": "Address",
                    "required": False,
                    "aliases": [
                        "address",
                        "warehouse address",
                        "warehouse_address",
                    ],
                },
                "city": {
                    "label": "City",
                    "required": False,
                    "aliases": [
                        "city",
                    ],
                },
                "state": {
                    "label": "State",
                    "required": False,
                    "aliases": [
                        "state",
                    ],
                },
                "country": {
                    "label": "Country",
                    "required": False,
                    "aliases": [
                        "country",
                    ],
                },
                "pincode": {
                    "label": "Pincode",
                    "required": False,
                    "aliases": [
                        "pincode",
                        "pin code",
                        "postal code",
                        "postal_code",
                        "zip",
                        "zip code",
                    ],
                },
            },
            },
        "INVENTORY": {
            "label": "Opening Inventory",
            "fields": {
                "product_sku": {
                    "label": "Product SKU",
                    "required": True,
                    "aliases": [
                        "product sku",
                        "product_sku",
                        "sku",
                        "item sku",
                        "item_sku",
                    ],
                },
                "warehouse_code": {
                    "label": "Warehouse Code",
                    "required": True,
                    "aliases": [
                        "warehouse code",
                        "warehouse_code",
                        "warehouse",
                        "location code",
                        "location_code",
                    ],
                },
                "quantity": {
                    "label": "Opening Quantity",
                    "required": True,
                    "aliases": [
                        "opening quantity",
                        "opening_quantity",
                        "opening stock",
                        "opening_stock",
                        "quantity",
                        "qty",
                    ],
                },
            },
        },
    }

    @classmethod
    def get_schema(
        cls,
        migration_type,
    ):
        migration_type = (
            str(migration_type or "")
            .strip()
            .upper()
        )

        schema = cls.SCHEMAS.get(
            migration_type
        )

        if schema is None:
            raise ValueError(
                "Migration schema is not "
                "available for this type."
            )

        return schema

    @classmethod
    def get_fields(
        cls,
        migration_type,
    ):
        return (
            cls.get_schema(
                migration_type
            )["fields"]
        )

    @classmethod
    def get_required_fields(
        cls,
        migration_type,
    ):
        fields = cls.get_fields(
            migration_type
        )

        return {
            name
            for name, configuration
            in fields.items()
            if configuration.get(
                "required",
                False,
            )
        }