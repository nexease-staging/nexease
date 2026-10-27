from django.urls import path

from apps.sales import views


urlpatterns = [
    path(
        "customers/",
        views.customer_list,
        name="customer-list",
    ),

    path(
        "customers/<str:customer_id>/deactivate/",
        views.customer_deactivate,
        name="customer-deactivate",
    ),

    path(
        "customers/<str:customer_id>/activate/",
        views.customer_activate,
        name="customer-activate",
    ),

    path(
        "customers/<str:customer_id>/",
        views.customer_detail,
        name="customer-detail",
    ),

    path(
        "orders/",
        views.sales_order_list,
        name="sales-order-list",
    ),

    path(
        "orders/<str:sales_order_id>/confirm/",
        views.sales_order_confirm,
        name="sales-order-confirm",
    ),

    path(
        "orders/<str:sales_order_id>/cancel/",
        views.sales_order_cancel,
        name="sales-order-cancel",
    ),

    path(
        "orders/<str:sales_order_id>/fulfill/",
        views.sales_order_fulfill,
        name="sales-order-fulfill",
    ),
    
    path(
        "orders/<str:sales_order_id>/",
        views.sales_order_detail,
        name="sales-order-detail",
    ),

    path(
        "invoices/",
        views.invoice_list,
        name="invoice-list",
    ),

    path(
        "invoices/<str:invoice_id>/issue/",
        views.invoice_issue,
        name="invoice-issue",
    ),

    path(
        "invoices/<str:invoice_id>/cancel/",
        views.invoice_cancel,
        name="invoice-cancel",
    ),

    path(
        "invoices/<str:invoice_id>/",
        views.invoice_detail,
        name="invoice-detail",
    ),

    path(
        "customers/<str:customer_id>/outstanding/",
        views.customer_outstanding,
        name="customer-outstanding",
    ),

    path(
        "accounts-receivable/",
        views.accounts_receivable_summary,
        name="accounts-receivable-summary",
    ),

    path(
        "payments/",
        views.payment_list,
        name="payment-list",
    ),

    path(
        "payments/<str:payment_id>/",
        views.payment_detail,
        name="payment-detail",
    ),
    path(
        "invoices/<str:invoice_id>/payments/",
        views.invoice_payment_history,
        name="invoice-payment-history",
    ),

    path(
        "customers/<str:customer_id>/payments/",
        views.customer_payment_history,
        name="customer-payment-history",
    ),

    path(
        "returns/",
        views.sales_returns,
        name="sales-returns",
    ),

    path(
        "returns/<str:return_id>/confirm/",
        views.confirm_sales_return,
        name="confirm-sales-return",
    ),

    path(
        "returns/<str:return_id>/",
        views.sales_return_detail,
        name="sales-return-detail",
    ),
    path(
        "credit-notes/",
        views.credit_notes,
        name="credit-notes",
    ),

    path(
        "credit-notes/<str:credit_note_id>/issue/",
        views.issue_credit_note,
        name="issue-credit-note",
    ),
    
    path(
        "credit-notes/<str:credit_note_id>/cancel/",
        views.cancel_credit_note,
        name="cancel-credit-note",
    ),
    path(
        "credit-notes/<str:credit_note_id>/",
        views.credit_note_detail,
        name="credit-note-detail",
    ),
    path(
        "invoices/<str:invoice_id>/pdf/",
        views.invoice_pdf,
        name="invoice-pdf",
    ),
    path(
        "sales-orders/<str:sales_order_id>/pdf/",
        views.sales_order_pdf,
        name="sales-order-pdf",
    ),
    path(
        "credit-notes/<str:credit_note_id>/pdf/",
        views.credit_note_pdf,
        name="credit-note-pdf",
    ),
    path(
        "customer-payments/<str:payment_id>/pdf/",
        views.customer_payment_pdf,
        name="customer-payment-pdf",
    ),
    path(
        "sales-orders/<str:sales_order_id>/email/",
        views.sales_order_email,
        name="sales-order-email",
    ),

    path(
        "credit-notes/<str:credit_note_id>/email/",
        views.credit_note_email,
        name="credit-note-email",
    ),

    path(
        "customer-payments/<str:payment_id>/email/",
        views.customer_payment_email,
        name="customer-payment-email",
    ),
    path(
        "invoices/<str:invoice_id>/email/",
        views.invoice_email,
        name="invoice-email",
    ),
]