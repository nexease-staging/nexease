from apps.authorization.permissions import (
    PERMISSION_CATALOG,
)


def select_permissions(
    *resource_prefixes,
):
    prefixes = tuple(
        f"{prefix}."
        for prefix in resource_prefixes
    )

    return sorted(
        code

        for code
        in PERMISSION_CATALOG

        if code.startswith(
            prefixes
        )
    )


ROLE_CATALOG = {
    "admin": {
        "name":
            "Admin",

        "description":
            (
                "Full access to the "
                "organization."
            ),

        "is_system":
            True,

        "permissions":
            sorted(
                PERMISSION_CATALOG.keys()
            ),
    },

    "warehouse_manager": {
        "name":
            "Warehouse Manager",

        "description":
            (
                "Manages warehouses, inventory, "
                "goods receipts and stock "
                "fulfilment."
            ),

        "is_system":
            True,

        "permissions":
            sorted({
                *select_permissions(
                    "products",
                    "warehouses",
                    "inventory",
                    "goods_receipts",
                ),

                "purchase_orders.read",
                "sales_orders.read",
                "sales_orders.fulfill",
                "purchase_returns.read",
                "sales_returns.read",
            }),
    },

    "sales_manager": {
        "name":
            "Sales Manager",

        "description":
            (
                "Manages customers, sales orders, "
                "invoices, payments and sales "
                "returns."
            ),

        "is_system":
            True,

        "permissions":
            sorted({
                *select_permissions(
                    "customers",
                    "sales_orders",
                    "invoices",
                    "customer_payments",
                    "sales_returns",
                    "credit_notes",
                ),

                "products.read",
                "inventory.read",
                "warehouses.read",
            }),
    },

    "purchase_manager": {
        "name":
            "Purchase Manager",

        "description":
            (
                "Manages suppliers, purchasing, "
                "goods receipts, vendor bills "
                "and purchase returns."
            ),

        "is_system":
            True,

        "permissions":
            sorted({
                *select_permissions(
                    "suppliers",
                    "purchase_orders",
                    "goods_receipts",
                    "purchase_returns",
                    "vendor_bills",
                    "bills",
                    "vendor_debit_notes",
                    "supplier_payments",
                ),

                "products.read",
                "inventory.read",
                "warehouses.read",
            }),
    },
}