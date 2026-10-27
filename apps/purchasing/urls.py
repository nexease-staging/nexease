from django.urls import path

from apps.purchasing import views


urlpatterns = [
    path(
        "suppliers/",
        views.supplier_list,
        name="supplier-list",
    ),

    path(
        "suppliers/<str:supplier_id>/deactivate/",
        views.supplier_deactivate,
        name="supplier-deactivate",
    ),

    path(
        "suppliers/<str:supplier_id>/activate/",
        views.supplier_activate,
        name="supplier-activate",
    ),

    path(
        "suppliers/<str:supplier_id>/",
        views.supplier_detail,
        name="supplier-detail",
    ),

    path(
        "purchase-orders/",
        views.purchase_order_list,
        name="purchase-order-list",
    ),

    path(
        "purchase-orders/<str:purchase_order_id>/confirm/",
        views.purchase_order_confirm,
        name="purchase-order-confirm",
    ),

    path(
        "purchase-orders/<str:purchase_order_id>/cancel/",
        views.purchase_order_cancel,
        name="purchase-order-cancel",
    ),

    path(
        "purchase-orders/<str:purchase_order_id>/",
        views.purchase_order_detail,
        name="purchase-order-detail",
    ),

    path(
        "goods-receipts/",
        views.goods_receipt_list,
        name="goods-receipt-list",
    ),

    path(
        "goods-receipts/<str:goods_receipt_id>/",
        views.goods_receipt_detail,
        name="goods-receipt-detail",
    ),

    path(
        "vendor-bills/",
        views.vendor_bills,
        name="vendor-bills",
    ),

    path(
        "vendor-bills/<str:bill_id>/post/",
        views.post_vendor_bill,
        name="post-vendor-bill",
    ),

    path(
        "vendor-bills/<str:bill_id>/",
        views.vendor_bill_detail,
        name="vendor-bill-detail",
    ),
    
    path(
        "accounts-payable/",
        views.accounts_payable_summary,
        name="accounts-payable-summary",
    ),

    path(
        "suppliers/<str:supplier_id>/outstanding/",
        views.supplier_outstanding,
        name="supplier-outstanding",
    ),
    
    path(
        "vendor-bills/<str:bill_id>/cancel/",
        views.cancel_vendor_bill,
        name="cancel-vendor-bill",
    ),
    path(
        "vendor-bills/<str:bill_id>/payments/",
        views.vendor_bill_payments,
        name="vendor-bill-payments",
    ),

    path(
        "supplier-payments/",
        views.supplier_payments,
        name="supplier-payments",
    ),

    path(
        "supplier-payments/<str:payment_id>/",
        views.supplier_payment_detail,
        name="supplier-payment-detail",
    ),
    path(
        "purchase-returns/",
        views.purchase_returns,
        name="purchase-returns",
    ),

    path(
        "purchase-returns/<str:purchase_return_id>/confirm/",
        views.confirm_purchase_return,
        name="confirm-purchase-return",
    ),

    path(
        "purchase-returns/<str:purchase_return_id>/cancel/",
        views.cancel_purchase_return,
        name="cancel-purchase-return",
    ),
    path(
        "purchase-returns/<str:purchase_return_id>/",
        views.purchase_return_detail,
        name="purchase-return-detail",
    ),
    path(
        "vendor-debit-notes/",
        views.vendor_debit_notes,
        name="vendor-debit-notes",
    ),

    path(
        "vendor-debit-notes/<str:debit_note_id>/issue/",
        views.issue_vendor_debit_note,
        name="issue-vendor-debit-note",
    ),

    path(
        "vendor-debit-notes/<str:debit_note_id>/cancel/",
        views.cancel_vendor_debit_note,
        name="cancel-vendor-debit-note",
    ),

    path(
        "vendor-debit-notes/<str:debit_note_id>/",
        views.vendor_debit_note_detail,
        name="vendor-debit-note-detail",
    ),
    path(
        "purchase-orders/<str:purchase_order_id>/pdf/",
        views.purchase_order_pdf,
        name="purchase-order-pdf",
    ),
    path(
        "vendor-bills/<str:vendor_bill_id>/pdf/",
        views.vendor_bill_pdf,
        name="vendor-bill-pdf",
    ),
    path(
        "vendor-debit-notes/<str:vendor_debit_note_id>/pdf/",
        views.vendor_debit_note_pdf,
        name="vendor-debit-note-pdf",
    ),
    path(
        "supplier-payments/<str:payment_id>/pdf/",
        views.supplier_payment_pdf,
        name="supplier-payment-pdf",
    ),

    path(
        "purchase-orders/<str:purchase_order_id>/email/",
        views.purchase_order_email,
        name="purchase-order-email",
    ),

    path(
        "vendor-bills/<str:vendor_bill_id>/email/",
        views.vendor_bill_email,
        name="vendor-bill-email",
    ),

    path(
        "vendor-debit-notes/<str:debit_note_id>/email/",
        views.vendor_debit_note_email,
        name="vendor-debit-note-email",
    ),

    path(
        "supplier-payments/<str:payment_id>/email/",
        views.supplier_payment_email,
        name="supplier-payment-email",
    ),

    path(
        "goods-receipts/<str:goods_receipt_id>/email/",
        views.goods_receipt_email,
        name="goods-receipt-email",
    ),
]