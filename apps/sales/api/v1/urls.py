from django.urls import (
    path,
)

from apps.sales.api.v1 import (
    credit_note_views,
    sales_return_views,
    views,
)


app_name = "sales_api_v1"


urlpatterns = [
    path(
        "customers/",
        views.customer_collection_api,
        name="customer_collection",
    ),

    path(
        (
            "customers/"
            "<str:customer_id>/activate/"
        ),
        views.customer_activate_api,
        name="customer_activate",
    ),

    path(
        (
            "customers/"
            "<str:customer_id>/deactivate/"
        ),
        views.customer_deactivate_api,
        name="customer_deactivate",
    ),

    path(
        "customers/<str:customer_id>/",
        views.customer_detail_api,
        name="customer_detail",
    ),
    path(
        "sales-orders/",
        views.sales_order_collection_api,
        name="sales_order_collection",
    ),

    path(
        (
            "sales-orders/"
            "<str:sales_order_id>/confirm/"
        ),
        views.sales_order_confirm_api,
        name="sales_order_confirm",
    ),

    path(
        (
            "sales-orders/"
            "<str:sales_order_id>/cancel/"
        ),
        views.sales_order_cancel_api,
        name="sales_order_cancel",
    ),

    path(
        (
            "sales-orders/"
            "<str:sales_order_id>/fulfill/"
        ),
        views.sales_order_fulfill_api,
        name="sales_order_fulfill",
    ),

    path(
        (
            "sales-orders/"
            "<str:sales_order_id>/"
        ),
        views.sales_order_detail_api,
        name="sales_order_detail",
    ),
    path(
        "invoice-bank-accounts/",
        views.invoice_bank_account_list_api,
        name="invoice_bank_account_list",
    ),

    path(
        "invoices/",
        views.invoice_collection_api,
        name="invoice_collection",
    ),

    path(
        (
            "invoices/"
            "<str:invoice_id>/issue/"
        ),
        views.invoice_issue_api,
        name="invoice_issue",
    ),

    path(
        (
            "invoices/"
            "<str:invoice_id>/cancel/"
        ),
        views.invoice_cancel_api,
        name="invoice_cancel",
    ),

    path(
        (
            "invoices/"
            "<str:invoice_id>/record-payment/"
        ),
        views.invoice_record_payment_api,
        name="invoice_record_payment",
    ),

    path(
        (
            "invoices/"
            "<str:invoice_id>/"
        ),
        views.invoice_detail_api,
        name="invoice_detail",
    ),
    path(
        "customer-payments/",
        views.customer_payment_collection_api,
        name=(
            "customer_payment_collection"
        ),
    ),

    path(
        (
            "customer-payments/"
            "<str:payment_id>/"
        ),
        views.customer_payment_detail_api,
        name="customer_payment_detail",
    ),

    path(
        "accounts-receivable/",
        views.accounts_receivable_api,
        name="accounts_receivable",
    ),

    path(
        "accounts-receivable/aging/",
        views.accounts_receivable_aging_api,
        name=(
            "accounts_receivable_aging"
        ),
    ),
    path(
        "sales-returns/",
        sales_return_views
        .sales_return_collection_api,
        name="sales_return_collection",
    ),

    path(
        (
            "sales-returns/"
            "<str:sales_return_id>/"
            "confirm/"
        ),
        sales_return_views
        .sales_return_confirm_api,
        name="sales_return_confirm",
    ),

    path(
        (
            "sales-returns/"
            "<str:sales_return_id>/"
            "cancel/"
        ),
        sales_return_views
        .sales_return_cancel_api,
        name="sales_return_cancel",
    ),

    path(
        (
            "sales-returns/"
            "<str:sales_return_id>/"
        ),
        sales_return_views
        .sales_return_detail_api,
        name="sales_return_detail",
    ),

    path(
        "credit-notes/",
        credit_note_views
        .credit_note_collection_api,
        name="credit_note_collection",
    ),

    path(
        (
            "credit-notes/"
            "<str:credit_note_id>/"
            "issue/"
        ),
        credit_note_views
        .credit_note_issue_api,
        name="credit_note_issue",
    ),

    path(
        (
            "credit-notes/"
            "<str:credit_note_id>/"
            "cancel/"
        ),
        credit_note_views
        .credit_note_cancel_api,
        name="credit_note_cancel",
    ),

    path(
        (
            "credit-notes/"
            "<str:credit_note_id>/"
        ),
        credit_note_views
        .credit_note_detail_api,
        name="credit_note_detail",
    ),
]