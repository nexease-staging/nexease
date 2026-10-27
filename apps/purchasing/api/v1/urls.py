from django.urls import (
    path,
)

from apps.purchasing.api.v1 import (
    views,
)
from apps.purchasing.api.v1 import (
    goods_receipt_views,
    purchase_return_views,
    vendor_bill_views,
    vendor_debit_note_views,
    views,
)

app_name = "purchasing_api_v1"


urlpatterns = [
    path(
        "suppliers/",
        views.supplier_collection_api,
        name="supplier_collection",
    ),

    path(
        (
            "suppliers/"
            "<str:supplier_id>/activate/"
        ),
        views.supplier_activate_api,
        name="supplier_activate",
    ),

    path(
        (
            "suppliers/"
            "<str:supplier_id>/deactivate/"
        ),
        views.supplier_deactivate_api,
        name="supplier_deactivate",
    ),

    path(
        "suppliers/<str:supplier_id>/",
        views.supplier_detail_api,
        name="supplier_detail",
    ),
    path(
        "purchase-orders/",
        views.purchase_order_collection_api,
        name="purchase_order_collection",
    ),

    path(
        (
            "purchase-orders/"
            "<str:purchase_order_id>/"
            "confirm/"
        ),
        views.purchase_order_confirm_api,
        name="purchase_order_confirm",
    ),

    path(
        (
            "purchase-orders/"
            "<str:purchase_order_id>/"
            "cancel/"
        ),
        views.purchase_order_cancel_api,
        name="purchase_order_cancel",
    ),

    path(
        (
            "purchase-orders/"
            "<str:purchase_order_id>/"
        ),
        views.purchase_order_detail_api,
        name="purchase_order_detail",
    ),
    path(
        "goods-receipts/",
        goods_receipt_views
        .goods_receipt_collection_api,
        name="goods_receipt_collection",
    ),

    path(
        "goods-receipts/"
        "<str:goods_receipt_id>/",
        goods_receipt_views
        .goods_receipt_detail_api,
        name="goods_receipt_detail",
    ),
    path(
        "vendor-bills/",
        vendor_bill_views
        .vendor_bill_collection_api,
        name="vendor_bill_collection",
    ),

    path(
        "vendor-bills/bank-accounts/",
        vendor_bill_views
        .vendor_bill_bank_account_list_api,
        name="vendor_bill_bank_accounts",
    ),

    path(
        "vendor-bills/"
        "<str:bill_id>/post/",
        vendor_bill_views
        .vendor_bill_post_api,
        name="vendor_bill_post",
    ),

    path(
        "vendor-bills/"
        "<str:bill_id>/cancel/",
        vendor_bill_views
        .vendor_bill_cancel_api,
        name="vendor_bill_cancel",
    ),

    path(
        "vendor-bills/"
        "<str:bill_id>/payments/",
        vendor_bill_views
        .vendor_bill_record_payment_api,
        name="vendor_bill_record_payment",
    ),

    path(
        "vendor-bills/"
        "<str:bill_id>/",
        vendor_bill_views
        .vendor_bill_detail_api,
        name="vendor_bill_detail",
    ),

    path(
        "accounts-payable/",
        vendor_bill_views
        .accounts_payable_api,
        name="accounts_payable",
    ),
    path(
        "purchase-returns/",
        purchase_return_views
        .purchase_return_collection_api,
        name="purchase_return_collection",
    ),

    path(
        (
            "purchase-returns/"
            "<str:purchase_return_id>/"
            "confirm/"
        ),
        purchase_return_views
        .purchase_return_confirm_api,
        name="purchase_return_confirm",
    ),

    path(
        (
            "purchase-returns/"
            "<str:purchase_return_id>/"
            "cancel/"
        ),
        purchase_return_views
        .purchase_return_cancel_api,
        name="purchase_return_cancel",
    ),

    path(
        (
            "purchase-returns/"
            "<str:purchase_return_id>/"
        ),
        purchase_return_views
        .purchase_return_detail_api,
        name="purchase_return_detail",
    ),

    path(
        "vendor-debit-notes/",
        vendor_debit_note_views
        .vendor_debit_note_collection_api,
        name="vendor_debit_note_collection",
    ),

    path(
        (
            "vendor-debit-notes/"
            "<str:debit_note_id>/"
            "issue/"
        ),
        vendor_debit_note_views
        .vendor_debit_note_issue_api,
        name="vendor_debit_note_issue",
    ),

    path(
        (
            "vendor-debit-notes/"
            "<str:debit_note_id>/"
            "cancel/"
        ),
        vendor_debit_note_views
        .vendor_debit_note_cancel_api,
        name="vendor_debit_note_cancel",
    ),

    path(
        (
            "vendor-debit-notes/"
            "<str:debit_note_id>/"
        ),
        vendor_debit_note_views
        .vendor_debit_note_detail_api,
        name="vendor_debit_note_detail",
    ),
]