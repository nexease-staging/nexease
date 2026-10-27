class MigrationSchemaError(
    ValueError,
):
    pass


class MigrationSchemaService:

    SCHEMAS = {
        "CATEGORIES": {
            "migration_type": "CATEGORIES",
            "label": "Categories",
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
                        "notes",
                    ),
                },
            },
        },

        "PRODUCTS": {
            "migration_type": "PRODUCTS",
            "label": "Products",
            "fields": {
                "sku": {
                    "label": "SKU",
                    "required": True,
                    "aliases": (
                        "sku",
                        "item code",
                        "product code",
                        "stock code",
                        "item sku",
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
                        "product",
                    ),
                },
                "description": {
                    "label": "Description",
                    "required": False,
                    "aliases": (
                        "description",
                        "product description",
                        "item details",
                        "remarks",
                    ),
                },
                "category": {
                    "label": "Category",
                    "required": True,
                    "aliases": (
                        "category",
                        "category name",
                        "group",
                        "item group",
                        "product group",
                    ),
                },
                "brand": {
                    "label": "Brand",
                    "required": False,
                    "aliases": (
                        "brand",
                        "brand name",
                        "manufacturer",
                    ),
                },
                "unit": {
                    "label": "Unit",
                    "required": True,
                    "aliases": (
                        "unit",
                        "uom",
                        "unit of measure",
                        "unit of measurement",
                    ),
                },
                "cost_price": {
                    "label": "Cost Price",
                    "required": False,
                    "aliases": (
                        "cost price",
                        "cost",
                        "purchase price",
                        "purchase rate",
                        "buying price",
                    ),
                },
                "selling_price": {
                    "label": "Selling Price",
                    "required": False,
                    "aliases": (
                        "selling price",
                        "sales price",
                        "sale price",
                        "selling rate",
                        "sales rate",
                        "rate",
                    ),
                },
            },
        },
        "CUSTOMERS": {
            "migration_type": "CUSTOMERS",
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
            "migration_type": "SUPPLIERS",
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
            "migration_type": "WAREHOUSES",
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
            "migration_type": "INVENTORY",
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
        "SALES_ORDERS": {
            "migration_type": "SALES_ORDERS",
            "label": "Sales Orders",
            "fields": {
                "so_number": {
                    "label": "Sales Order Number",
                    "required": True,
                    "aliases": [
                        "sales order number",
                        "sales_order_number",
                        "sales order no",
                        "sales_order_no",
                        "so number",
                        "so_number",
                        "so no",
                        "so_no",
                        "order number",
                        "order_number",
                    ],
                },
                "customer_code": {
                    "label": "Customer Code",
                    "required": True,
                    "aliases": [
                        "customer code",
                        "customer_code",
                        "customer id",
                        "customer_id",
                    ],
                },
                "warehouse_code": {
                    "label": "Warehouse Code",
                    "required": True,
                    "aliases": [
                        "warehouse code",
                        "warehouse_code",
                        "warehouse id",
                        "warehouse_id",
                    ],
                },
                "order_date": {
                    "label": "Order Date",
                    "required": True,
                    "aliases": [
                        "order date",
                        "order_date",
                        "sales order date",
                        "sales_order_date",
                        "date",
                    ],
                },
                "expected_delivery_date": {
                    "label": "Expected Delivery Date",
                    "required": False,
                    "aliases": [
                        "expected delivery date",
                        "expected_delivery_date",
                        "delivery date",
                        "delivery_date",
                    ],
                },
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
                "quantity": {
                    "label": "Quantity",
                    "required": True,
                    "aliases": [
                        "quantity",
                        "qty",
                        "order quantity",
                        "order_quantity",
                    ],
                },
                "unit_price": {
                    "label": "Unit Price",
                    "required": True,
                    "aliases": [
                        "unit price",
                        "unit_price",
                        "price",
                        "rate",
                        "sales price",
                        "selling price",
                    ],
                },
                "tax_rate": {
                    "label": "Tax Rate",
                    "required": False,
                    "aliases": [
                        "tax rate",
                        "tax_rate",
                        "tax %",
                        "tax percentage",
                        "gst rate",
                        "gst_rate",
                    ],
                },
                "discount": {
                    "label": "Discount",
                    "required": False,
                    "aliases": [
                        "discount",
                        "discount amount",
                        "discount_amount",
                    ],
                },
                "notes": {
                    "label": "Notes",
                    "required": False,
                    "aliases": [
                        "notes",
                        "note",
                        "remarks",
                        "remark",
                        "description",
                    ],
                },
            },
        },
        "PURCHASE_ORDERS": {
            "migration_type": "PURCHASE_ORDERS",
            "label": "Purchase Orders",
            "fields": {
                "po_number": {
                    "label": "PO Number",
                    "required": True,
                    "aliases": [
                        "po number",
                        "po_number",
                        "purchase order number",
                        "purchase_order_number",
                        "purchase order",
                        "po",
                    ],
                },
                "supplier_code": {
                    "label": "Supplier Code",
                    "required": True,
                    "aliases": [
                        "supplier code",
                        "supplier_code",
                        "vendor code",
                        "vendor_code",
                    ],
                },
                "order_date": {
                    "label": "Order Date",
                    "required": True,
                    "aliases": [
                        "order date",
                        "order_date",
                        "po date",
                        "po_date",
                    ],
                },
                "expected_delivery_date": {
                    "label": "Expected Delivery Date",
                    "required": False,
                    "aliases": [
                        "expected delivery date",
                        "expected_delivery_date",
                        "delivery date",
                        "delivery_date",
                    ],
                },
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
                "quantity": {
                    "label": "Quantity",
                    "required": True,
                    "aliases": [
                        "quantity",
                        "qty",
                    ],
                },
                "unit_price": {
                    "label": "Unit Price",
                    "required": True,
                    "aliases": [
                        "unit price",
                        "unit_price",
                        "price",
                        "rate",
                    ],
                },
                "tax_rate": {
                    "label": "Tax Rate",
                    "required": False,
                    "aliases": [
                        "tax rate",
                        "tax_rate",
                        "tax",
                        "gst rate",
                        "gst_rate",
                    ],
                },
                "discount": {
                    "label": "Discount",
                    "required": False,
                    "aliases": [
                        "discount",
                        "discount amount",
                        "discount_amount",
                    ],
                },
                "notes": {
                    "label": "Notes",
                    "required": False,
                    "aliases": [
                        "notes",
                        "note",
                        "remarks",
                        "remark",
                    ],
                },
            },
        },
        "GOODS_RECEIPTS": {
            "migration_type": "GOODS_RECEIPTS",
            "label": "Goods Receipts",
            "description": (
                "Import goods received against "
                "existing purchase orders."
            ),
            "fields": {
                "purchase_order_number": {
                    "label": "Purchase Order Number",
                    "required": True,
                    "aliases": (
                        "purchase order number",
                        "po number",
                        "po no",
                        "po",
                    ),
                },
                "warehouse_code": {
                    "label": "Warehouse Code",
                    "required": True,
                    "aliases": (
                        "warehouse code",
                        "warehouse",
                        "location code",
                    ),
                },
                "product_sku": {
                    "label": "Product SKU",
                    "required": True,
                    "aliases": (
                        "product sku",
                        "sku",
                        "item code",
                        "product code",
                    ),
                },
                "quantity_received": {
                    "label": "Quantity Received",
                    "required": True,
                    "aliases": (
                        "quantity received",
                        "received quantity",
                        "qty received",
                        "received qty",
                        "quantity",
                        "qty",
                    ),
                },
                "notes": {
                    "label": "Notes",
                    "required": False,
                    "aliases": (
                        "notes",
                        "remarks",
                        "comments",
                    ),
                },
            },
        },
        "SALES_INVOICES": {
            "migration_type": "SALES_INVOICES",
            "label": "Sales Invoices",
            "fields": {
                "invoice_number": {
                    "label": "Invoice Number",
                    "required": True,
                    "aliases": (
                        "invoice number",
                        "invoice no",
                        "invoice no.",
                        "invoice",
                        "inv no",
                        "inv number",
                    ),
                },
                "sales_order_number": {
                    "label": "Sales Order Number",
                    "required": True,
                    "aliases": (
                        "sales order number",
                        "sales order no",
                        "sales order no.",
                        "so number",
                        "so no",
                        "so no.",
                    ),
                },
                "invoice_date": {
                    "label": "Invoice Date",
                    "required": True,
                    "aliases": (
                        "invoice date",
                        "date",
                        "inv date",
                    ),
                },
                "due_date": {
                    "label": "Due Date",
                    "required": False,
                    "aliases": (
                        "due date",
                        "payment due date",
                        "payment due",
                    ),
                },
                "notes": {
                    "label": "Notes",
                    "required": False,
                    "aliases": (
                        "notes",
                        "note",
                        "remarks",
                        "remark",
                        "description",
                    ),
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
            raise MigrationSchemaError(
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
    def required_fields(
        cls,
        migration_type,
    ):
        fields = cls.get_fields(
            migration_type
        )

        return [
            field_name
            for field_name, definition
            in fields.items()
            if definition.get(
                "required",
                False,
            )
        ]
# Financial import schemas use the same registry as mapping, preview and templates.
from apps.migration.services.financial_import import FIELDS
for _kind, _fields in FIELDS.items():
    MigrationSchemaService.SCHEMAS[_kind] = {"migration_type":_kind,"label":_kind.replace("_"," ").title(),"fields":{k:{"label":k.replace("_"," ").title(),"required":v,"aliases":(k,k.replace("_"," "))} for k,v in _fields.items()}}

from apps.migration.services.employee_import import FIELDS as EMPLOYEE_FIELDS
MigrationSchemaService.SCHEMAS["EMPLOYEES"]={"migration_type":"EMPLOYEES","label":"Employees","fields":{k:{"label":k.replace("_"," ").title(),"required":v,"aliases":(k,k.replace("_"," "))} for k,v in EMPLOYEE_FIELDS.items()}}
