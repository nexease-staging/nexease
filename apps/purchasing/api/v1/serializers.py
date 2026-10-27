from apps.core.services.api_serialization_service import (
    APISerializationService,
)
from apps.inventory.api.v1.serializers import (
    WarehouseAPISerializer,
)

class SupplierAPISerializer:

    @staticmethod
    def serialize_summary(
        supplier,
    ):
        if not supplier:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    supplier.id
                )
            ),
            "code":
                supplier.code,
            "name":
                supplier.name,
            "email":
                (
                    supplier.email
                    or
                    None
                ),
            "phone":
                (
                    supplier.phone
                    or
                    None
                ),
            "gstin":
                (
                    supplier.gstin
                    or
                    None
                ),
            "city":
                (
                    supplier.city
                    or
                    None
                ),
            "state":
                (
                    supplier.state
                    or
                    None
                ),
            "country":
                (
                    supplier.country
                    or
                    None
                ),
            "is_active":
                bool(
                    supplier.is_active
                ),
        }

    @staticmethod
    def serialize_detail(
        supplier,
    ):
        if not supplier:
            return None

        summary = (
            SupplierAPISerializer
            .serialize_summary(
                supplier
            )
        )

        return {
            **summary,
            "address":
                (
                    supplier.address
                    or
                    None
                ),
            "pincode":
                (
                    supplier.pincode
                    or
                    None
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    supplier.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    supplier.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        suppliers,
    ):
        return [
            (
                SupplierAPISerializer
                .serialize_summary(
                    supplier
                )
            )
            for supplier
            in suppliers
        ]

class PurchaseOrderAPISerializer:

    @staticmethod
    def _serialize_product(
        product,
    ):
        if not product:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    product.id
                )
            ),
            "sku":
                product.sku,
            "name":
                product.name,
            "unit":
                product.unit,
            "is_active":
                bool(
                    product.is_active
                ),
        }

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_item(
        item,
    ):
        if not item:
            return None

        remaining_quantity = (
            item.quantity
            -
            item.received_quantity
        )

        if remaining_quantity < 0:
            remaining_quantity = 0

        return {
            "product": (
                PurchaseOrderAPISerializer
                ._serialize_product(
                    item.product
                )
            ),
            "quantity":
                str(
                    item.quantity
                ),
            "received_quantity":
                str(
                    item.received_quantity
                ),
            "remaining_quantity":
                str(
                    remaining_quantity
                ),
            "unit_price":
                str(
                    item.unit_price
                ),
            "tax_rate":
                str(
                    item.tax_rate
                ),
            "discount":
                str(
                    item.discount
                ),
            "subtotal":
                str(
                    item.subtotal
                ),
            "tax_amount":
                str(
                    item.tax_amount
                ),
            "total":
                str(
                    item.total
                ),
        }

    @staticmethod
    def serialize_summary(
        purchase_order,
    ):
        if not purchase_order:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    purchase_order.id
                )
            ),
            "po_number":
                purchase_order.po_number,
            "supplier": (
                SupplierAPISerializer
                .serialize_summary(
                    purchase_order.supplier
                )
            ),
            "status":
                purchase_order.status,
            "order_date": (
                APISerializationService
                .serialize_date(
                    purchase_order.order_date
                )
            ),
            "expected_delivery_date": (
                APISerializationService
                .serialize_date(
                    (
                        purchase_order
                        .expected_delivery_date
                    )
                )
            ),
            "subtotal":
                str(
                    purchase_order.subtotal
                ),
            "tax_amount":
                str(
                    purchase_order.tax_amount
                ),
            "discount_amount":
                str(
                    purchase_order
                    .discount_amount
                ),
            "total_amount":
                str(
                    purchase_order.total_amount
                ),
            "item_count":
                len(
                    purchase_order.items
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    purchase_order.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    purchase_order.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        purchase_order,
    ):
        if not purchase_order:
            return None

        summary = (
            PurchaseOrderAPISerializer
            .serialize_summary(
                purchase_order
            )
        )

        return {
            **summary,
            "items": [
                (
                    PurchaseOrderAPISerializer
                    .serialize_item(
                        item
                    )
                )
                for item
                in (
                    purchase_order.items
                    or
                    []
                )
            ],
            "notes":
                (
                    purchase_order.notes
                    or
                    None
                ),
            "created_by": (
                PurchaseOrderAPISerializer
                ._serialize_created_by(
                    purchase_order.created_by
                )
            ),
            "confirmed_at": (
                APISerializationService
                .serialize_datetime(
                    purchase_order.confirmed_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    purchase_order.cancelled_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        purchase_orders,
    ):
        return [
            (
                PurchaseOrderAPISerializer
                .serialize_summary(
                    purchase_order
                )
            )
            for purchase_order
            in purchase_orders
        ]

class GoodsReceiptItemAPISerializer:

    @staticmethod
    def serialize(
        item,
    ):
        if not item:
            return None

        product = item.product

        return {
            "product": {
                "id": (
                    APISerializationService
                    .serialize_identifier(
                        product.id
                    )
                ),
                "sku": product.sku,
                "name": product.name,
                "unit": product.unit,
            },
            "quantity_received": str(
                item.quantity_received
            ),
        }


class GoodsReceiptAPISerializer:

    @staticmethod
    def serialize_summary(
        goods_receipt,
    ):
        if not goods_receipt:
            return None

        supplier = (
            goods_receipt.supplier
        )

        warehouse = (
            goods_receipt.warehouse
        )

        purchase_order = (
            goods_receipt.purchase_order
        )

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    goods_receipt.id
                )
            ),
            "grn_number":
                goods_receipt.grn_number,
            "purchase_order": {
                "id": (
                    APISerializationService
                    .serialize_identifier(
                        purchase_order.id
                    )
                ),
                "po_number":
                    purchase_order.po_number,
                "status":
                    purchase_order.status,
            },
            "supplier": (
                SupplierAPISerializer
                .serialize_summary(
                    supplier
                )
            ),
            "warehouse": {
                "id": (
                    APISerializationService
                    .serialize_identifier(
                        warehouse.id
                    )
                ),
                "code":
                    warehouse.code,
                "name":
                    warehouse.name,
            },
            "item_count": len(
                goods_receipt.items
                or []
            ),
            "received_at": (
                goods_receipt
                .received_at
                .isoformat()
                if goods_receipt.received_at
                else None
            ),
            "created_at": (
                goods_receipt
                .created_at
                .isoformat()
                if goods_receipt.created_at
                else None
            ),
        }

    @staticmethod
    def serialize_detail(
        goods_receipt,
    ):
        if not goods_receipt:
            return None

        data = (
            GoodsReceiptAPISerializer
            .serialize_summary(
                goods_receipt
            )
        )

        data.update(
            {
                "items": [
                    (
                        GoodsReceiptItemAPISerializer
                        .serialize(item)
                    )
                    for item
                    in (
                        goods_receipt.items
                        or []
                    )
                ],
                "notes": (
                    goods_receipt.notes
                    or
                    None
                ),
                "received_by": (
                    {
                        "id": (
                            APISerializationService
                            .serialize_identifier(
                                goods_receipt
                                .received_by
                                .id
                            )
                        ),
                        "email": (
                            goods_receipt
                            .received_by
                            .email
                        ),
                    }
                    if goods_receipt.received_by
                    else None
                ),
            }
        )

        return data

    @staticmethod
    def serialize_many(
        goods_receipts,
    ):
        return [
            (
                GoodsReceiptAPISerializer
                .serialize_summary(
                    goods_receipt
                )
            )
            for goods_receipt
            in (
                goods_receipts
                or []
            )
        ]

class PurchasingBankAccountAPISerializer:

    @staticmethod
    def serialize_summary(
        bank_account,
    ):
        if not bank_account:
            return None

        account_number = (
            bank_account.account_number
            or
            ""
        )

        masked_account_number = (
            (
                "••••"
                +
                account_number[-4:]
            )
            if account_number
            else None
        )

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    bank_account.id
                )
            ),
            "account_name":
                bank_account.account_name,
            "account_type":
                bank_account.account_type,
            "bank_name":
                (
                    bank_account.bank_name
                    or
                    None
                ),
            "masked_account_number":
                masked_account_number,
            "currency":
                bank_account.currency,
            "is_active":
                bool(
                    bank_account.is_active
                ),
        }

    @staticmethod
    def serialize_many(
        bank_accounts,
    ):
        return [
            (
                PurchasingBankAccountAPISerializer
                .serialize_summary(
                    bank_account
                )
            )
            for bank_account
            in bank_accounts
        ]


class VendorBillAPISerializer:

    @staticmethod
    def _serialize_purchase_order(
        purchase_order,
    ):
        if not purchase_order:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    purchase_order.id
                )
            ),
            "po_number":
                purchase_order.po_number,
            "status":
                purchase_order.status,
        }

    @staticmethod
    def _serialize_product(
        product,
    ):
        if not product:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    product.id
                )
            ),
            "sku":
                product.sku,
            "name":
                product.name,
            "unit":
                product.unit,
        }

    @staticmethod
    def _serialize_user(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_item(
        item,
    ):
        if not item:
            return None

        return {
            "product": (
                VendorBillAPISerializer
                ._serialize_product(
                    item.product
                )
            ),
            "quantity":
                str(
                    item.quantity
                ),
            "unit_price":
                str(
                    item.unit_price
                ),
            "tax_rate":
                str(
                    item.tax_rate
                ),
            "discount":
                str(
                    item.discount
                ),
            "line_subtotal":
                str(
                    item.line_subtotal
                ),
            "line_tax":
                str(
                    item.line_tax
                ),
            "line_total":
                str(
                    item.line_total
                ),
        }

    @staticmethod
    def serialize_summary(
        bill,
    ):
        if not bill:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    bill.id
                )
            ),
            "bill_number":
                bill.bill_number,
            "supplier_invoice_number": (
                bill.supplier_invoice_number
                or
                None
            ),
            "purchase_order": (
                VendorBillAPISerializer
                ._serialize_purchase_order(
                    bill.purchase_order
                )
            ),
            "supplier": (
                SupplierAPISerializer
                .serialize_summary(
                    bill.supplier
                )
            ),
            "status":
                bill.status,
            "bill_date": (
                APISerializationService
                .serialize_datetime(
                    bill.bill_date
                )
            ),
            "due_date": (
                APISerializationService
                .serialize_datetime(
                    bill.due_date
                )
            ),
            "subtotal":
                str(
                    bill.subtotal
                ),
            "tax_amount":
                str(
                    bill.tax_amount
                ),
            "discount_amount":
                str(
                    bill.discount_amount
                ),
            "total_amount":
                str(
                    bill.total_amount
                ),
            "amount_paid":
                str(
                    bill.amount_paid
                ),
            "balance_due":
                str(
                    bill.balance_due
                ),
            "item_count":
                len(
                    bill.items
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    bill.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    bill.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        bill,
    ):
        if not bill:
            return None

        summary = (
            VendorBillAPISerializer
            .serialize_summary(
                bill
            )
        )

        return {
            **summary,
            "items": [
                (
                    VendorBillAPISerializer
                    .serialize_item(
                        item
                    )
                )
                for item
                in (
                    bill.items
                    or
                    []
                )
            ],
            "supplier_snapshot": {
                "name":
                    bill.supplier_name,
                "address":
                    (
                        bill.supplier_address
                        or
                        None
                    ),
                "city":
                    (
                        bill.supplier_city
                        or
                        None
                    ),
                "state":
                    (
                        bill.supplier_state
                        or
                        None
                    ),
                "country":
                    (
                        bill.supplier_country
                        or
                        None
                    ),
                "pincode":
                    (
                        bill.supplier_pincode
                        or
                        None
                    ),
                "gstin":
                    (
                        bill.supplier_gstin
                        or
                        None
                    ),
            },
            "notes":
                (
                    bill.notes
                    or
                    None
                ),
            "created_by": (
                VendorBillAPISerializer
                ._serialize_user(
                    bill.created_by
                )
            ),
            "posted_at": (
                APISerializationService
                .serialize_datetime(
                    bill.posted_at
                )
            ),
            "paid_at": (
                APISerializationService
                .serialize_datetime(
                    bill.paid_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    bill.cancelled_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        bills,
    ):
        return [
            (
                VendorBillAPISerializer
                .serialize_summary(
                    bill
                )
            )
            for bill
            in bills
        ]


class SupplierPaymentAPISerializer:

    @staticmethod
    def serialize_summary(
        payment,
    ):
        if not payment:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    payment.id
                )
            ),
            "payment_number":
                payment.payment_number,
            "supplier": (
                SupplierAPISerializer
                .serialize_summary(
                    payment.supplier
                )
            ),
            "payment_date": (
                APISerializationService
                .serialize_datetime(
                    payment.payment_date
                )
            ),
            "amount":
                str(
                    payment.amount
                ),
            "payment_method":
                payment.payment_method,
            "bank_account": (
                PurchasingBankAccountAPISerializer
                .serialize_summary(
                    payment.bank_account
                )
            ),
            "reference_number":
                (
                    payment.reference_number
                    or
                    None
                ),
            "allocation_count":
                len(
                    payment.allocations
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    payment.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    payment.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        payment,
    ):
        if not payment:
            return None

        summary = (
            SupplierPaymentAPISerializer
            .serialize_summary(
                payment
            )
        )

        return {
            **summary,
            "allocations": [
                {
                    "vendor_bill": {
                        "id": (
                            APISerializationService
                            .serialize_identifier(
                                allocation
                                .vendor_bill
                                .id
                            )
                        ),
                        "bill_number": (
                            allocation
                            .vendor_bill
                            .bill_number
                        ),
                        "status": (
                            allocation
                            .vendor_bill
                            .status
                        ),
                        "bill_date": (
                            APISerializationService
                            .serialize_datetime(
                                allocation
                                .vendor_bill
                                .bill_date
                            )
                        ),
                        "total_amount":
                            str(
                                allocation
                                .vendor_bill
                                .total_amount
                            ),
                        "balance_due":
                            str(
                                allocation
                                .vendor_bill
                                .balance_due
                            ),
                    },
                    "amount":
                        str(
                            allocation.amount
                        ),
                }
                for allocation
                in (
                    payment.allocations
                    or
                    []
                )
            ],
            "notes":
                (
                    payment.notes
                    or
                    None
                ),
            "created_by": (
                VendorBillAPISerializer
                ._serialize_user(
                    payment.created_by
                )
            ),
        }

    @staticmethod
    def serialize_many(
        payments,
    ):
        return [
            (
                SupplierPaymentAPISerializer
                .serialize_summary(
                    payment
                )
            )
            for payment
            in payments
        ]

class PurchaseReturnAPISerializer:

    @staticmethod
    def _serialize_purchase_order(
        purchase_order,
    ):
        if not purchase_order:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    purchase_order.id
                )
            ),
            "po_number":
                purchase_order.po_number,
            "status":
                purchase_order.status,
        }

    @staticmethod
    def _serialize_vendor_bill(
        vendor_bill,
    ):
        if not vendor_bill:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    vendor_bill.id
                )
            ),
            "bill_number":
                vendor_bill.bill_number,
            "status":
                vendor_bill.status,
            "total_amount":
                str(
                    vendor_bill.total_amount
                ),
            "balance_due":
                str(
                    vendor_bill.balance_due
                ),
        }

    @staticmethod
    def serialize_item(
        item,
    ):
        if not item:
            return None

        return {
            "product": (
                VendorBillAPISerializer
                ._serialize_product(
                    item.product
                )
            ),
            "quantity":
                str(
                    item.quantity
                ),
            "unit_price":
                str(
                    item.unit_price
                ),
            "tax_rate":
                str(
                    item.tax_rate
                ),
            "discount":
                str(
                    item.discount
                ),
            "line_subtotal":
                str(
                    item.line_subtotal
                ),
            "line_tax":
                str(
                    item.line_tax
                ),
            "line_total":
                str(
                    item.line_total
                ),
            "reason":
                (
                    item.reason
                    or
                    None
                ),
        }

    @staticmethod
    def serialize_summary(
        purchase_return,
    ):
        if not purchase_return:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    purchase_return.id
                )
            ),
            "return_number":
                purchase_return.return_number,
            "purchase_order": (
                PurchaseReturnAPISerializer
                ._serialize_purchase_order(
                    purchase_return
                    .purchase_order
                )
            ),
            "vendor_bill": (
                PurchaseReturnAPISerializer
                ._serialize_vendor_bill(
                    purchase_return
                    .vendor_bill
                )
            ),
            "supplier": (
                SupplierAPISerializer
                .serialize_summary(
                    purchase_return.supplier
                )
            ),
            "warehouse": (
                WarehouseAPISerializer
                .serialize_summary(
                    purchase_return.warehouse
                )
            ),
            "status":
                purchase_return.status,
            "return_date": (
                APISerializationService
                .serialize_datetime(
                    purchase_return.return_date
                )
            ),
            "subtotal":
                str(
                    purchase_return.subtotal
                ),
            "tax_amount":
                str(
                    purchase_return.tax_amount
                ),
            "discount_amount":
                str(
                    purchase_return
                    .discount_amount
                ),
            "total_amount":
                str(
                    purchase_return.total_amount
                ),
            "item_count":
                len(
                    purchase_return.items
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    purchase_return.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    purchase_return.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        purchase_return,
    ):
        if not purchase_return:
            return None

        summary = (
            PurchaseReturnAPISerializer
            .serialize_summary(
                purchase_return
            )
        )

        return {
            **summary,
            "items": [
                (
                    PurchaseReturnAPISerializer
                    .serialize_item(
                        item
                    )
                )
                for item
                in (
                    purchase_return.items
                    or
                    []
                )
            ],
            "reason":
                (
                    purchase_return.reason
                    or
                    None
                ),
            "notes":
                (
                    purchase_return.notes
                    or
                    None
                ),
            "created_by": (
                VendorBillAPISerializer
                ._serialize_user(
                    purchase_return.created_by
                )
            ),
            "confirmed_at": (
                APISerializationService
                .serialize_datetime(
                    purchase_return
                    .confirmed_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    purchase_return
                    .cancelled_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        purchase_returns,
    ):
        return [
            (
                PurchaseReturnAPISerializer
                .serialize_summary(
                    purchase_return
                )
            )
            for purchase_return
            in purchase_returns
        ]


class VendorDebitNoteAPISerializer:

    @staticmethod
    def _serialize_purchase_return(
        purchase_return,
    ):
        if not purchase_return:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    purchase_return.id
                )
            ),
            "return_number":
                purchase_return.return_number,
            "status":
                purchase_return.status,
            "total_amount":
                str(
                    purchase_return.total_amount
                ),
        }

    @staticmethod
    def serialize_item(
        item,
    ):
        if not item:
            return None

        return {
            "product": (
                VendorBillAPISerializer
                ._serialize_product(
                    item.product
                )
            ),
            "quantity":
                str(
                    item.quantity
                ),
            "unit_price":
                str(
                    item.unit_price
                ),
            "tax_rate":
                str(
                    item.tax_rate
                ),
            "discount":
                str(
                    item.discount
                ),
            "line_subtotal":
                str(
                    item.line_subtotal
                ),
            "line_tax":
                str(
                    item.line_tax
                ),
            "line_total":
                str(
                    item.line_total
                ),
        }

    @staticmethod
    def serialize_summary(
        debit_note,
    ):
        if not debit_note:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    debit_note.id
                )
            ),
            "debit_note_number":
                debit_note.debit_note_number,
            "purchase_return": (
                VendorDebitNoteAPISerializer
                ._serialize_purchase_return(
                    debit_note.purchase_return
                )
            ),
            "vendor_bill": (
                PurchaseReturnAPISerializer
                ._serialize_vendor_bill(
                    debit_note.vendor_bill
                )
            ),
            "purchase_order": (
                PurchaseReturnAPISerializer
                ._serialize_purchase_order(
                    debit_note.purchase_order
                )
            ),
            "supplier": (
                SupplierAPISerializer
                .serialize_summary(
                    debit_note.supplier
                )
            ),
            "status":
                debit_note.status,
            "debit_note_date": (
                APISerializationService
                .serialize_datetime(
                    debit_note
                    .debit_note_date
                )
            ),
            "subtotal":
                str(
                    debit_note.subtotal
                ),
            "tax_amount":
                str(
                    debit_note.tax_amount
                ),
            "discount_amount":
                str(
                    debit_note.discount_amount
                ),
            "total_amount":
                str(
                    debit_note.total_amount
                ),
            "applied_amount":
                str(
                    debit_note.applied_amount
                ),
            "remaining_credit":
                str(
                    debit_note.remaining_credit
                ),
            "item_count":
                len(
                    debit_note.items
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    debit_note.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    debit_note.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        debit_note,
    ):
        if not debit_note:
            return None

        summary = (
            VendorDebitNoteAPISerializer
            .serialize_summary(
                debit_note
            )
        )

        return {
            **summary,
            "items": [
                (
                    VendorDebitNoteAPISerializer
                    .serialize_item(
                        item
                    )
                )
                for item
                in (
                    debit_note.items
                    or
                    []
                )
            ],
            "reason":
                (
                    debit_note.reason
                    or
                    None
                ),
            "notes":
                (
                    debit_note.notes
                    or
                    None
                ),
            "created_by": (
                VendorBillAPISerializer
                ._serialize_user(
                    debit_note.created_by
                )
            ),
            "issued_at": (
                APISerializationService
                .serialize_datetime(
                    debit_note.issued_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    debit_note.cancelled_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        debit_notes,
    ):
        return [
            (
                VendorDebitNoteAPISerializer
                .serialize_summary(
                    debit_note
                )
            )
            for debit_note
            in debit_notes
        ]