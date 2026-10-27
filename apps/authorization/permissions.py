ACTION_LABELS = {
    "manage": "Manage",
    "read": "View",
    "create": "Create",
    "update": "Update",
    "delete": "Delete",
    "activate": "Activate",
    "deactivate": "Deactivate",
    "adjust": "Adjust",
    "transfer": "Transfer",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "fulfill": "Fulfill",
    "issue": "Issue",
    "post": "Post",
    "reconcile": "Reconcile",
    "record_payment": "Record Payment",
    "reverse": "Reverse",
    "assign_permissions": "Assign Permissions",
    "validate": "Validate",
    "import": "Import",
}


PERMISSION_DEFINITIONS = [
    ("finance", "expenses", "Daily expenses", ("read", "manage")),
    ("workforce", "payroll", "Payroll", ("read", "manage")),
    ("workforce", "labour", "Labour", ("read", "manage")),
    ("taxation", "taxation", "Taxation", ("read", "manage")),
    # ==================================================
    # AUTHORIZATION
    # ==================================================

    (
        "authorization",
        "permissions",
        "Permissions",
        (
            "read",
        ),
    ),

    (
        "authorization",
        "roles",
        "Roles",
        (
            "read",
            "create",
            "update",
            "activate",
            "deactivate",
            "assign_permissions",
        ),
    ),

    # ==================================================
    # ORGANIZATIONS AND USERS
    # ==================================================

    (
        "organizations",
        "organizations",
        "Organizations",
        (
            "update",
        ),
    ),

    (
        "users",
        "users",
        "Users",
        (
            "read",
            "create",
            "update",
            "activate",
            "deactivate",
        ),
    ),

    # ==================================================
    # PRODUCTS AND INVENTORY
    # ==================================================

    (
        "products",
        "products",
        "Products",
        (
            "read",
            "create",
            "update",
            "delete",
        ),
    ),

    (
        "inventory",
        "warehouses",
        "Warehouses",
        (
            "read",
            "create",
            "update",
        ),
    ),

    (
        "inventory",
        "inventory",
        "Inventory",
        (
            "read",
            "create",
            "adjust",
            "transfer",
        ),
    ),

    # ==================================================
    # PURCHASING
    # ==================================================

    (
        "purchasing",
        "suppliers",
        "Suppliers",
        (
            "read",
            "create",
            "update",
        ),
    ),

    (
        "purchasing",
        "purchase_orders",
        "Purchase Orders",
        (
            "read",
            "create",
            "update",
            "cancel",
        ),
    ),

    (
        "purchasing",
        "goods_receipts",
        "Goods Receipts",
        (
            "read",
            "create",
        ),
    ),

    (
        "purchasing",
        "purchase_returns",
        "Purchase Returns",
        (
            "read",
            "create",
            "confirm",
            "cancel",
        ),
    ),

    (
        "purchasing",
        "vendor_bills",
        "Vendor Bills",
        (
            "read",
        ),
    ),

    (
        "purchasing",
        "bills",
        "Bills",
        (
            "read",
            "create",
            "post",
            "cancel",
            "record_payment",
        ),
    ),

    (
        "purchasing",
        "vendor_debit_notes",
        "Vendor Debit Notes",
        (
            "read",
            "create",
            "issue",
            "cancel",
        ),
    ),

    (
        "purchasing",
        "supplier_payments",
        "Supplier Payments",
        (
            "read",
        ),
    ),

    # ==================================================
    # SALES
    # ==================================================

    (
        "sales",
        "customers",
        "Customers",
        (
            "read",
            "create",
            "update",
        ),
    ),

    (
        "sales",
        "sales_orders",
        "Sales Orders",
        (
            "read",
            "create",
            "update",
            "fulfill",
            "cancel",
        ),
    ),

    (
        "sales",
        "invoices",
        "Invoices",
        (
            "read",
            "create",
            "issue",
            "cancel",
            "record_payment",
        ),
    ),

    (
        "sales",
        "customer_payments",
        "Customer Payments",
        (
            "read",
        ),
    ),

    (
        "sales",
        "sales_returns",
        "Sales Returns",
        (
            "read",
            "create",
            "confirm",
            "cancel",
        ),
    ),

    (
        "sales",
        "credit_notes",
        "Credit Notes",
        (
            "read",
            "create",
            "issue",
            "cancel",
        ),
    ),

    # ==================================================
    # ACCOUNTING
    # ==================================================

    (
        "accounting",
        "chart_of_accounts",
        "Chart of Accounts",
        (
            "read",
            "create",
            "update",
            "deactivate",
        ),
    ),

    (
        "accounting",
        "journal_entries",
        "Journal Entries",
        (
            "read",
            "create",
            "post",
            "reverse",
        ),
    ),

    (
        "accounting",
        "general_ledger",
        "General Ledger",
        (
            "read",
        ),
    ),

    (
        "accounting",
        "trial_balance",
        "Trial Balance",
        (
            "read",
        ),
    ),

    (
        "accounting",
        "accounting_reports",
        "Accounting Reports",
        (
            "read",
        ),
    ),

    (
        "accounting",
        "accounting_audit",
        "Accounting Audit",
        (
            "read",
        ),
    ),

    # ==================================================
    # BANKING
    # ==================================================

    (
        "banking",
        "bank_accounts",
        "Bank Accounts",
        (
            "read",
            "create",
            "update",
            "deactivate",
        ),
    ),

    (
        "banking",
        "bank_transfers",
        "Bank Transfers",
        (
            "read",
            "create",
            "post",
            "cancel",
        ),
    ),

    (
        "banking",
        "bank_statements",
        "Bank Statements",
        (
            "read",
            "create",
            "reconcile",
            "cancel",
        ),
    ),

    (
        "banking",
        "bank_transactions",
        "Bank Transactions",
        (
            "read",
            "create",
            "reconcile",
        ),
    ),
    # ==================================================
    # DATA MIGRATION
    # ==================================================

    (
        "migration",
        "migration",
        "Data Migration",
        (
            "read",
            "create",
            "validate",
            "import",
        ),
    ),
]


def build_permission_catalog():
    catalog = {}

    for (
        module,
        resource_code,
        resource_name,
        actions,
    ) in PERMISSION_DEFINITIONS:

        for action in actions:

            action_label = (
                ACTION_LABELS[
                    action
                ]
            )

            code = (
                f"{resource_code}.{action}"
            )

            catalog[
                code
            ] = {
                "name": (
                    f"{action_label} "
                    f"{resource_name}"
                ),

                "description": (
                    f"Allows "
                    f"{action_label.lower()} "
                    f"{resource_name.lower()}."
                ),

                "module":
                    module,
            }

    return catalog


PERMISSION_CATALOG = (
    build_permission_catalog()
)


LEGACY_PERMISSION_REPLACEMENTS = {
    "product.view":
        "products.read",

    "product.create":
        "products.create",

    "product.update":
        "products.update",

    "product.delete":
        "products.delete",
}