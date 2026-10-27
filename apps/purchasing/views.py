from apps.inventory.models import Warehouse
from decimal import Decimal
from datetime import datetime
from apps.purchasing.models import (
    GoodsReceipt,
    PurchaseOrder,
    VendorBill,
    VendorDebitNote,
    PurchaseReturn,
)
from apps.finance.documents.purchase_order_pdf import (
    PurchaseOrderPDF,
)
from apps.finance.documents.pdf_security import (
    PDFSecurity,
)
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from apps.purchasing.services.goods_receipt_service import (
    GoodsReceiptService,
)
from apps.finance.documents.goods_receipt_pdf import (
    GoodsReceiptPDF,
)
from apps.purchasing.repositories.goods_receipt_repository import (
    GoodsReceiptRepository,
)
import json
from datetime import date
from bson import ObjectId
from bson.errors import InvalidId
from django.http import JsonResponse, HttpResponse

from apps.purchasing.services.supplier_service import (
    SupplierService,
)
from apps.products.models import Product
from apps.purchasing.models import Supplier
from apps.purchasing.services.purchase_order_service import (
    PurchaseOrderService,
)
from apps.finance.documents.vendor_bill_pdf import (
    VendorBillPDF,
)
from apps.purchasing.repositories.vendor_bill_repository import (
    VendorBillRepository,
)

from apps.purchasing.services.vendor_bill_service import (
    VendorBillService,
)
from apps.finance.documents.supplier_payment_receipt_pdf import (
    SupplierPaymentReceiptPDF,
)
from apps.purchasing.repositories.supplier_payment_repository import (
    SupplierPaymentRepository,
)

from apps.purchasing.services.supplier_payment_service import (
    SupplierPaymentService,
)
from apps.purchasing.repositories.supplier_payment_repository import (
    SupplierPaymentRepository,
)

from apps.purchasing.services.supplier_payment_service import (
    SupplierPaymentService,
)

from apps.purchasing.repositories.purchase_return_repository import (
    PurchaseReturnRepository,
)

from apps.purchasing.services.purchase_return_service import (
    PurchaseReturnService,
)
from apps.purchasing.repositories.vendor_debit_note_repository import (
    VendorDebitNoteRepository,
)
from apps.finance.documents.vendor_debit_note_pdf import (
    VendorDebitNotePDF,
)
from apps.purchasing.services.vendor_debit_note_service import (
    VendorDebitNoteService,
)
from apps.finance.services.document_audit_service import (
    DocumentAuditService,
)
from apps.finance.services.document_email_api_service import (
    DocumentEmailAPIService,
)
def _supplier_response(supplier):
    return {
        "id": str(supplier.id),
        "code": supplier.code,
        "name": supplier.name,
        "email": supplier.email or "",
        "phone": supplier.phone,
        "gstin": supplier.gstin,
        "address": supplier.address,
        "city": supplier.city,
        "state": supplier.state,
        "country": supplier.country,
        "pincode": supplier.pincode,
        "is_active": supplier.is_active,
        "created_at": (
            supplier.created_at.isoformat()
            if supplier.created_at
            else None
        ),
        "updated_at": (
            supplier.updated_at.isoformat()
            if supplier.updated_at
            else None
        ),
    }


def supplier_list(request):
    """
    GET  /purchasing/suppliers/
    POST /purchasing/suppliers/
    """

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    if request.method == "GET":
        active_only = (
            request.GET.get("active")
            == "true"
        )

        try:
            suppliers = SupplierService.list_suppliers(
                user=user,
                organization=user.organization,
                active_only=active_only,
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        data = [
            _supplier_response(supplier)
            for supplier in suppliers
        ]

        return JsonResponse(
            {
                "count": len(data),
                "suppliers": data,
            },
            status=200,
        )

    if request.method == "POST":
        try:
            data = json.loads(request.body)

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON."},
                status=400,
            )

        if not isinstance(data, dict):
            return JsonResponse(
                {
                    "error":
                    "JSON body must be an object."
                },
                status=400,
            )

        required_fields = [
            "name",
            "code",
        ]

        missing_fields = [
            field
            for field in required_fields
            if not data.get(field)
        ]

        if missing_fields:
            return JsonResponse(
                {
                    "error": "Missing required fields.",
                    "fields": missing_fields,
                },
                status=400,
            )

        try:
            supplier = SupplierService.create_supplier(
                user=user,
                organization=user.organization,
                name=data.get("name", ""),
                code=data.get("code", ""),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                gstin=data.get("gstin", ""),
                address=data.get("address", ""),
                city=data.get("city", ""),
                state=data.get("state", ""),
                country=data.get(
                    "country",
                    "India",
                ),
                pincode=data.get("pincode", ""),
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        return JsonResponse(
            {
                "message":
                "Supplier created successfully.",
                "supplier":
                _supplier_response(supplier),
            },
            status=201,
        )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )


def supplier_detail(
    request,
    supplier_id,
):
    """
    GET /purchasing/suppliers/<id>/
    PUT /purchasing/suppliers/<id>/
    """

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(supplier_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid supplier ID."},
            status=400,
        )

    if request.method == "GET":
        try:
            supplier = SupplierService.get_supplier(
                user=user,
                organization=user.organization,
                supplier_id=supplier_id,
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=404,
            )

        return JsonResponse(
            _supplier_response(supplier),
            status=200,
        )

    if request.method == "PUT":
        try:
            data = json.loads(request.body)

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON."},
                status=400,
            )

        if not isinstance(data, dict):
            return JsonResponse(
                {
                    "error":
                    "JSON body must be an object."
                },
                status=400,
            )

        try:
            supplier = SupplierService.update_supplier(
                user=user,
                organization=user.organization,
                supplier_id=supplier_id,
                name=data.get("name"),
                email=data.get("email"),
                phone=data.get("phone"),
                gstin=data.get("gstin"),
                address=data.get("address"),
                city=data.get("city"),
                state=data.get("state"),
                country=data.get("country"),
                pincode=data.get("pincode"),
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        return JsonResponse(
            {
                "message":
                "Supplier updated successfully.",
                "supplier":
                _supplier_response(supplier),
            },
            status=200,
        )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )


def supplier_deactivate(
    request,
    supplier_id,
):
    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(supplier_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid supplier ID."},
            status=400,
        )

    try:
        supplier = (
            SupplierService.deactivate_supplier(
                user=user,
                organization=user.organization,
                supplier_id=supplier_id,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    return JsonResponse(
        {
            "message":
            "Supplier deactivated successfully.",
            "supplier":
            _supplier_response(supplier),
        },
        status=200,
    )


def supplier_activate(
    request,
    supplier_id,
):
    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(supplier_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid supplier ID."},
            status=400,
        )

    try:
        supplier = SupplierService.activate_supplier(
            user=user,
            organization=user.organization,
            supplier_id=supplier_id,
        )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    return JsonResponse(
        {
            "message":
            "Supplier activated successfully.",
            "supplier":
            _supplier_response(supplier),
        },
        status=200,
    )

def _purchase_order_response(purchase_order):
    items = []

    for item in purchase_order.items:
        items.append(
            {
                "product": {
                    "id": str(item.product.id),
                    "sku": item.product.sku,
                    "name": item.product.name,
                },
                "quantity": str(item.quantity),
                "received_quantity": str(
                    item.received_quantity
                ),
                "unit_price": str(item.unit_price),
                "tax_rate": str(item.tax_rate),
                "discount": str(item.discount),
                "subtotal": str(item.subtotal),
                "tax_amount": str(
                    item.tax_amount
                ),
                "total": str(item.total),
            }
        )

    return {
        "id": str(purchase_order.id),
        "po_number": purchase_order.po_number,
        "status": purchase_order.status,

        "supplier": {
            "id": str(
                purchase_order.supplier.id
            ),
            "code":
                purchase_order.supplier.code,
            "name":
                purchase_order.supplier.name,
        },

        "order_date": (
            purchase_order.order_date.isoformat()
            if purchase_order.order_date
            else None
        ),

        "expected_delivery_date": (
            purchase_order
            .expected_delivery_date
            .isoformat()
            if purchase_order.expected_delivery_date
            else None
        ),

        "items": items,

        "subtotal": str(
            purchase_order.subtotal
        ),

        "tax_amount": str(
            purchase_order.tax_amount
        ),

        "discount_amount": str(
            purchase_order.discount_amount
        ),

        "total_amount": str(
            purchase_order.total_amount
        ),

        "notes": purchase_order.notes,

        "created_by": {
            "id": str(
                purchase_order.created_by.id
            ),
            "email":
                purchase_order.created_by.email,
        },

        "created_at": (
            purchase_order.created_at.isoformat()
            if purchase_order.created_at
            else None
        ),

        "updated_at": (
            purchase_order.updated_at.isoformat()
            if purchase_order.updated_at
            else None
        ),

        "confirmed_at": (
            purchase_order.confirmed_at.isoformat()
            if purchase_order.confirmed_at
            else None
        ),

        "cancelled_at": (
            purchase_order.cancelled_at.isoformat()
            if purchase_order.cancelled_at
            else None
        ),
    }

def _build_purchase_order_request_items(
    *,
    organization,
    raw_items,
):
    if not isinstance(raw_items, list):
        raise ValueError(
            "Items must be a list."
        )

    items = []

    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise ValueError(
                "Each purchase order item "
                "must be an object."
            )

        product_id = raw_item.get(
            "product_id"
        )

        if not product_id:
            raise ValueError(
                "Product ID is required."
            )

        try:
            ObjectId(product_id)
        except (InvalidId, TypeError):
            raise ValueError(
                "Invalid product ID."
            )

        product = Product.objects(
            organization=organization,
            id=product_id,
        ).first()

        if not product:
            raise ValueError(
                "Product not found."
            )

        items.append(
            {
                "product": product,
                "quantity":
                    raw_item.get(
                        "quantity",
                        0,
                    ),
                "unit_price":
                    raw_item.get(
                        "unit_price",
                        0,
                    ),
                "tax_rate":
                    raw_item.get(
                        "tax_rate",
                        0,
                    ),
                "discount":
                    raw_item.get(
                        "discount",
                        0,
                    ),
            }
        )

    return items

def _parse_date(
    value,
    field_name,
    required=False,
):
    if not value:
        if required:
            raise ValueError(
                f"{field_name} is required."
            )

        return None

    try:
        return date.fromisoformat(
            value
        )
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid {field_name}. "
            "Use YYYY-MM-DD."
        )

def purchase_order_list(request):
    """
    GET  /purchasing/purchase-orders/
    POST /purchasing/purchase-orders/
    """

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    if request.method == "GET":
        status = request.GET.get(
            "status"
        )

        try:
            purchase_orders = (
                PurchaseOrderService
                .list_purchase_orders(
                    user=user,
                    organization=user.organization,
                    status=status,
                )
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        data = [
            _purchase_order_response(
                purchase_order
            )
            for purchase_order
            in purchase_orders
        ]

        return JsonResponse(
            {
                "count": len(data),
                "purchase_orders": data,
            },
            status=200,
        )

    if request.method == "POST":
        try:
            data = json.loads(
                request.body
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON."},
                status=400,
            )

        if not isinstance(data, dict):
            return JsonResponse(
                {
                    "error":
                    "JSON body must be an object."
                },
                status=400,
            )

        supplier_id = data.get(
            "supplier_id"
        )

        if not supplier_id:
            return JsonResponse(
                {
                    "error":
                    "supplier_id is required."
                },
                status=400,
            )

        try:
            ObjectId(supplier_id)

        except (InvalidId, TypeError):
            return JsonResponse(
                {
                    "error":
                    "Invalid supplier ID."
                },
                status=400,
            )

        supplier = Supplier.objects(
            organization=user.organization,
            id=supplier_id,
        ).first()

        if not supplier:
            return JsonResponse(
                {
                    "error":
                    "Supplier not found."
                },
                status=404,
            )

        try:
            order_date = _parse_date(
                data.get("order_date"),
                "order_date",
                required=True,
            )

            expected_delivery_date = (
                _parse_date(
                    data.get(
                        "expected_delivery_date"
                    ),
                    "expected_delivery_date",
                    required=False,
                )
            )

            raw_items = (
                _build_purchase_order_request_items(
                    organization=user.organization,
                    raw_items=data.get(
                        "items"
                    ),
                )
            )

            purchase_order = (
                PurchaseOrderService
                .create_purchase_order(
                    user=user,
                    organization=user.organization,
                    supplier=supplier,
                    order_date=order_date,
                    expected_delivery_date=(
                        expected_delivery_date
                    ),
                    raw_items=raw_items,
                    notes=data.get(
                        "notes",
                        "",
                    ),
                )
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        return JsonResponse(
            {
                "message":
                "Purchase order created successfully.",
                "purchase_order":
                _purchase_order_response(
                    purchase_order
                ),
            },
            status=201,
        )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )

def purchase_order_detail(
    request,
    purchase_order_id,
):
    """
    GET /purchasing/purchase-orders/<id>/
    PUT /purchasing/purchase-orders/<id>/
    """

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(purchase_order_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid purchase order ID."},
            status=400,
        )

    if request.method == "GET":
        try:
            purchase_order = (
                PurchaseOrderService.get_purchase_order(
                    user=user,
                    organization=user.organization,
                    purchase_order_id=purchase_order_id,
                )
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=404,
            )

        return JsonResponse(
            _purchase_order_response(
                purchase_order
            ),
            status=200,
        )

    if request.method == "PUT":
        try:
            data = json.loads(
                request.body
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON."},
                status=400,
            )

        if not isinstance(data, dict):
            return JsonResponse(
                {
                    "error":
                    "JSON body must be an object."
                },
                status=400,
            )

        supplier = None

        if "supplier_id" in data:
            supplier_id = data.get(
                "supplier_id"
            )

            try:
                ObjectId(supplier_id)

            except (InvalidId, TypeError):
                return JsonResponse(
                    {
                        "error":
                        "Invalid supplier ID."
                    },
                    status=400,
                )

            supplier = Supplier.objects(
                organization=user.organization,
                id=supplier_id,
            ).first()

            if not supplier:
                return JsonResponse(
                    {
                        "error":
                        "Supplier not found."
                    },
                    status=404,
                )

        try:
            order_date = None

            if "order_date" in data:
                order_date = _parse_date(
                    data.get("order_date"),
                    "order_date",
                    required=True,
                )

            expected_delivery_date = None

            if "expected_delivery_date" in data:
                expected_delivery_date = (
                    _parse_date(
                        data.get(
                            "expected_delivery_date"
                        ),
                        "expected_delivery_date",
                        required=False,
                    )
                )

            raw_items = None

            if "items" in data:
                raw_items = (
                    _build_purchase_order_request_items(
                        organization=user.organization,
                        raw_items=data.get(
                            "items"
                        ),
                    )
                )

            purchase_order = (
                PurchaseOrderService.update_purchase_order(
                    user=user,
                    organization=user.organization,
                    purchase_order_id=purchase_order_id,
                    supplier=supplier,
                    order_date=order_date,
                    expected_delivery_date=(
                        expected_delivery_date
                    ),
                    raw_items=raw_items,
                    notes=(
                        data.get("notes")
                        if "notes" in data
                        else None
                    ),
                )
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        return JsonResponse(
            {
                "message":
                "Purchase order updated successfully.",
                "purchase_order":
                _purchase_order_response(
                    purchase_order
                ),
            },
            status=200,
        )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )


def purchase_order_confirm(
    request,
    purchase_order_id,
):
    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(purchase_order_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error":
                "Invalid purchase order ID."
            },
            status=400,
        )

    try:
        purchase_order = (
            PurchaseOrderService
            .confirm_purchase_order(
                user=user,
                organization=user.organization,
                purchase_order_id=purchase_order_id,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    return JsonResponse(
        {
            "message":
            "Purchase order confirmed successfully.",
            "purchase_order":
            _purchase_order_response(
                purchase_order
            ),
        },
        status=200,
    )

def purchase_order_cancel(
    request,
    purchase_order_id,
):
    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(purchase_order_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error":
                "Invalid purchase order ID."
            },
            status=400,
        )

    try:
        purchase_order = (
            PurchaseOrderService
            .cancel_purchase_order(
                user=user,
                organization=user.organization,
                purchase_order_id=purchase_order_id,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    return JsonResponse(
        {
            "message":
            "Purchase order cancelled successfully.",
            "purchase_order":
            _purchase_order_response(
                purchase_order
            ),
        },
        status=200,
    )

def _purchase_return_response(
    purchase_return,
):
    return {
        "id":
            str(purchase_return.id),

        "return_number":
            purchase_return.return_number,

        "status":
            purchase_return.status,

        "purchase_order": {
            "id":
                str(
                    purchase_return
                    .purchase_order.id
                ),
            "po_number":
                purchase_return
                .purchase_order
                .po_number,
        },

        "vendor_bill": {
            "id":
                str(
                    purchase_return
                    .vendor_bill.id
                ),
            "bill_number":
                purchase_return
                .vendor_bill
                .bill_number,
        },

        "supplier": {
            "id":
                str(
                    purchase_return
                    .supplier.id
                ),
            "name":
                purchase_return
                .supplier.name,
        },

        "warehouse": {
            "id":
                str(
                    purchase_return
                    .warehouse.id
                ),
            "code":
                purchase_return
                .warehouse.code,
        },

        "return_date": (
            purchase_return
            .return_date
            .isoformat()
            if purchase_return.return_date
            else None
        ),

        "items": [
            {
                "product": {
                    "id":
                        str(item.product.id),
                    "sku":
                        item.product.sku,
                    "name":
                        item.product.name,
                },
                "quantity":
                    str(item.quantity),
                "unit_price":
                    str(item.unit_price),
                "tax_rate":
                    str(item.tax_rate),
                "discount":
                    str(item.discount),
                "line_subtotal":
                    str(
                        item.line_subtotal
                    ),
                "line_tax":
                    str(item.line_tax),
                "line_total":
                    str(item.line_total),
                "reason":
                    item.reason,
            }
            for item
            in purchase_return.items
        ],

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

        "reason":
            purchase_return.reason,

        "notes":
            purchase_return.notes,

        "confirmed_at": (
            purchase_return
            .confirmed_at
            .isoformat()
            if purchase_return.confirmed_at
            else None
        ),

        "cancelled_at": (
            purchase_return
            .cancelled_at
            .isoformat()
            if purchase_return.cancelled_at
            else None
        ),

        "created_at": (
            purchase_return
            .created_at
            .isoformat()
            if purchase_return.created_at
            else None
        ),
    }

def purchase_returns(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Authentication required."
            },
            status=401,
        )

    organization = user.organization

    if request.method == "GET":
        try:
            PurchaseReturnService._check_permission(
                user,
                "purchase_returns.read",
            )

            returns = (
                PurchaseReturnRepository
                .list_by_organization(
                    organization=organization,
                )
            )

            return JsonResponse(
                {
                    "count":
                        returns.count(),
                    "purchase_returns": [
                        _purchase_return_response(
                            item
                        )
                        for item in returns
                    ],
                },
                status=200,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    if request.method == "POST":
        try:
            payload = json.loads(
                request.body
            )

            purchase_order_id = (
                payload.get(
                    "purchase_order_id"
                )
            )

            vendor_bill_id = (
                payload.get(
                    "vendor_bill_id"
                )
            )

            warehouse_id = (
                payload.get(
                    "warehouse_id"
                )
            )

            if not purchase_order_id:
                raise ValueError(
                    "purchase_order_id is required."
                )

            if not vendor_bill_id:
                raise ValueError(
                    "vendor_bill_id is required."
                )

            if not warehouse_id:
                raise ValueError(
                    "warehouse_id is required."
                )

            for value, label in [
                (
                    purchase_order_id,
                    "purchase order",
                ),
                (
                    vendor_bill_id,
                    "vendor bill",
                ),
                (
                    warehouse_id,
                    "warehouse",
                ),
            ]:
                try:
                    ObjectId(value)

                except (
                    InvalidId,
                    TypeError,
                ):
                    raise ValueError(
                        f"Invalid {label} ID."
                    )

            purchase_order = (
                PurchaseOrder.objects(
                    organization=organization,
                    id=purchase_order_id,
                ).first()
            )

            if not purchase_order:
                return JsonResponse(
                    {
                        "error":
                            "Purchase order not found."
                    },
                    status=404,
                )

            vendor_bill = (
                VendorBill.objects(
                    organization=organization,
                    id=vendor_bill_id,
                ).first()
            )

            if not vendor_bill:
                return JsonResponse(
                    {
                        "error":
                            "Vendor bill not found."
                    },
                    status=404,
                )

            warehouse = (
                Warehouse.objects(
                    organization=organization,
                    id=warehouse_id,
                ).first()
            )

            if not warehouse:
                return JsonResponse(
                    {
                        "error":
                            "Warehouse not found."
                    },
                    status=404,
                )

            raw_items = payload.get(
                "items",
                []
            )

            service_items = []

            for raw_item in raw_items:
                product_id = raw_item.get(
                    "product_id"
                )

                if not product_id:
                    raise ValueError(
                        "product_id is required "
                        "for every return item."
                    )

                try:
                    ObjectId(product_id)

                except (
                    InvalidId,
                    TypeError,
                ):
                    raise ValueError(
                        "Invalid product ID."
                    )

                product = Product.objects(
                    organization=organization,
                    id=product_id,
                ).first()

                if not product:
                    raise ValueError(
                        "Product not found."
                    )

                service_items.append(
                    {
                        "product":
                            product,
                        "quantity":
                            raw_item.get(
                                "quantity",
                                0,
                            ),
                        "reason":
                            raw_item.get(
                                "reason",
                                "",
                            ),
                    }
                )

            return_date = payload.get(
                "return_date"
            )

            if return_date:
                try:
                    return_date = (
                        datetime.fromisoformat(
                            return_date
                        )
                    )

                except ValueError:
                    raise ValueError(
                        "Invalid return_date."
                    )

            purchase_return = (
                PurchaseReturnService
                .create_purchase_return(
                    user=user,
                    organization=organization,
                    purchase_order=(
                        purchase_order
                    ),
                    vendor_bill=vendor_bill,
                    warehouse=warehouse,
                    items=service_items,
                    return_date=return_date,
                    reason=payload.get(
                        "reason",
                        "",
                    ),
                    notes=payload.get(
                        "notes",
                        "",
                    ),
                )
            )

            return JsonResponse(
                {
                    "message":
                        "Purchase return created "
                        "successfully.",
                    "purchase_return":
                        _purchase_return_response(
                            purchase_return
                        ),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "error":
                        "Invalid JSON body."
                },
                status=400,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except (
            ValueError,
            TypeError,
        ) as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )

def purchase_return_detail(
    request,
    purchase_return_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Authentication required."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        PurchaseReturnService._check_permission(
            user,
            "purchase_returns.read",
        )

        try:
            ObjectId(
                purchase_return_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid purchase return ID."
            )

        purchase_return = (
            PurchaseReturnRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                purchase_return_id=(
                    purchase_return_id
                ),
            )
        )

        if not purchase_return:
            return JsonResponse(
                {
                    "error":
                        "Purchase return not found."
                },
                status=404,
            )

        return JsonResponse(
            {
                "purchase_return":
                    _purchase_return_response(
                        purchase_return
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def confirm_purchase_return(
    request,
    purchase_return_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Authentication required."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        try:
            ObjectId(
                purchase_return_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid purchase return ID."
            )

        purchase_return = (
            PurchaseReturnRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                purchase_return_id=(
                    purchase_return_id
                ),
            )
        )

        if not purchase_return:
            return JsonResponse(
                {
                    "error":
                        "Purchase return not found."
                },
                status=404,
            )

        purchase_return = (
            PurchaseReturnService
            .confirm_purchase_return(
                user=user,
                organization=(
                    user.organization
                ),
                purchase_return=(
                    purchase_return
                ),
            )
        )

        return JsonResponse(
            {
                "message":
                    "Purchase return confirmed "
                    "successfully.",
                "purchase_return":
                    _purchase_return_response(
                        purchase_return
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )


    
def _goods_receipt_response(
    goods_receipt,
):
    items = []

    for item in goods_receipt.items:
        items.append(
            {
                "product": {
                    "id": str(
                        item.product.id
                    ),
                    "sku": item.product.sku,
                    "name": item.product.name,
                },
                "quantity_received": str(
                    item.quantity_received
                ),
            }
        )

    return {
        "id": str(
            goods_receipt.id
        ),

        "grn_number":
            goods_receipt.grn_number,

        "purchase_order": {
            "id": str(
                goods_receipt
                .purchase_order
                .id
            ),
            "po_number":
                goods_receipt
                .purchase_order
                .po_number,
            "status":
                goods_receipt
                .purchase_order
                .status,
        },

        "supplier": {
            "id": str(
                goods_receipt.supplier.id
            ),
            "code":
                goods_receipt.supplier.code,
            "name":
                goods_receipt.supplier.name,
        },

        "warehouse": {
            "id": str(
                goods_receipt.warehouse.id
            ),
            "code":
                goods_receipt.warehouse.code,
            "name":
                goods_receipt.warehouse.name,
        },

        "items": items,

        "notes":
            goods_receipt.notes,

        "received_by": {
            "id": str(
                goods_receipt.received_by.id
            ),
            "email":
                goods_receipt.received_by.email,
        },

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

def _build_goods_receipt_request_items(
    *,
    organization,
    raw_items,
):
    if not isinstance(
        raw_items,
        list,
    ):
        raise ValueError(
            "Items must be a list."
        )

    if not raw_items:
        raise ValueError(
            "Goods receipt must contain "
            "at least one item."
        )

    items = []

    product_ids = set()

    for raw_item in raw_items:

        if not isinstance(
            raw_item,
            dict,
        ):
            raise ValueError(
                "Each goods receipt item "
                "must be an object."
            )

        product_id = raw_item.get(
            "product_id"
        )

        if not product_id:
            raise ValueError(
                "Product ID is required."
            )

        try:
            ObjectId(
                product_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid product ID."
            )

        if product_id in product_ids:
            raise ValueError(
                "Duplicate product in "
                "goods receipt."
            )

        product_ids.add(
            product_id
        )

        product = Product.objects(
            organization=organization,
            id=product_id,
        ).first()

        if not product:
            raise ValueError(
                "Product not found."
            )

        items.append(
            {
                "product": product,
                "quantity_received":
                    raw_item.get(
                        "quantity_received",
                        0,
                    ),
            }
        )

    return items


def goods_receipt_list(
    request,
):
    """
    GET  /purchasing/goods-receipts/
    POST /purchasing/goods-receipts/
    """

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method == "GET":

        try:
            GoodsReceiptService._check_permission(
                user,
                "goods_receipts.read",
            )

            GoodsReceiptService._check_organization(
                user,
                user.organization,
            )

            goods_receipts = (
                GoodsReceiptRepository
                .list_by_organization(
                    organization=user.organization,
                )
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        data = [
            _goods_receipt_response(
                receipt
            )
            for receipt in goods_receipts
        ]

        return JsonResponse(
            {
                "count": len(data),
                "goods_receipts": data,
            },
            status=200,
        )

    if request.method == "POST":

        try:
            data = json.loads(
                request.body
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "error":
                        "Invalid JSON."
                },
                status=400,
            )

        if not isinstance(
            data,
            dict,
        ):
            return JsonResponse(
                {
                    "error":
                        "JSON body must be "
                        "an object."
                },
                status=400,
            )

        purchase_order_id = (
            data.get(
                "purchase_order_id"
            )
        )

        warehouse_id = data.get(
            "warehouse_id"
        )

        if not purchase_order_id:
            return JsonResponse(
                {
                    "error":
                        "purchase_order_id "
                        "is required."
                },
                status=400,
            )

        if not warehouse_id:
            return JsonResponse(
                {
                    "error":
                        "warehouse_id "
                        "is required."
                },
                status=400,
            )

        try:
            ObjectId(
                purchase_order_id
            )

            ObjectId(
                warehouse_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            return JsonResponse(
                {
                    "error":
                        "Invalid purchase order "
                        "or warehouse ID."
                },
                status=400,
            )

        purchase_order = (
            PurchaseOrder.objects(
                organization=user.organization,
                id=purchase_order_id,
            ).first()
        )

        if not purchase_order:
            return JsonResponse(
                {
                    "error":
                        "Purchase order not found."
                },
                status=404,
            )

        warehouse = Warehouse.objects(
            organization=user.organization,
            id=warehouse_id,
        ).first()

        if not warehouse:
            return JsonResponse(
                {
                    "error":
                        "Warehouse not found."
                },
                status=404,
            )

        try:
            raw_items = (
                _build_goods_receipt_request_items(
                    organization=user.organization,
                    raw_items=data.get(
                        "items"
                    ),
                )
            )

            goods_receipt = (
                GoodsReceiptService
                .receive_goods(
                    user=user,
                    organization=user.organization,
                    purchase_order=purchase_order,
                    warehouse=warehouse,
                    raw_items=raw_items,
                    notes=data.get(
                        "notes",
                        "",
                    ),
                )
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        return JsonResponse(
            {
                "message":
                    "Goods received successfully.",

                "goods_receipt":
                    _goods_receipt_response(
                        goods_receipt
                    ),
            },
            status=201,
        )

    return JsonResponse(
        {
            "error":
                "Method not allowed."
        },
        status=405,
    )

def goods_receipt_detail(
    request,
    goods_receipt_id,
):
    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(
            goods_receipt_id
        )

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid goods receipt ID."
            },
            status=400,
        )

    try:
        GoodsReceiptService._check_permission(
            user,
            "goods_receipts.read",
        )

        GoodsReceiptService._check_organization(
            user,
            user.organization,
        )

        goods_receipt = (
            GoodsReceiptRepository
            .get_by_id(
                organization=user.organization,
                goods_receipt_id=goods_receipt_id,
            )
        )

        if not goods_receipt:
            return JsonResponse(
                {
                    "error":
                        "Goods receipt not found."
                },
                status=404,
            )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    return JsonResponse(
        _goods_receipt_response(
            goods_receipt
        ),
        status=200,
    )

def _supplier_payment_response(
    payment,
):
    return {
        "id": str(payment.id),
        "payment_number":
            payment.payment_number,
        "supplier": {
            "id": str(
                payment.supplier.id
            ),
            "code":
                payment.supplier.code,
            "name":
                payment.supplier.name,
        },
        "payment_date": (
            payment.payment_date.isoformat()
            if payment.payment_date
            else None
        ),
        "amount": str(
            payment.amount
        ),
        "payment_method":
            payment.payment_method,
        "reference_number":
            payment.reference_number,
        "allocations": [
            {
                "vendor_bill": {
                    "id": str(
                        allocation
                        .vendor_bill.id
                    ),
                    "bill_number": (
                        allocation
                        .vendor_bill
                        .bill_number
                    ),
                },
                "amount": str(
                    allocation.amount
                ),
            }
            for allocation
            in payment.allocations
        ],
        "notes": payment.notes,
        "created_by": {
            "id": str(
                payment.created_by.id
            ),
            "email":
                payment.created_by.email,
        },
        "created_at": (
            payment.created_at.isoformat()
            if payment.created_at
            else None
        ),
        "updated_at": (
            payment.updated_at.isoformat()
            if payment.updated_at
            else None
        ),
    }

def vendor_bill_payments(
    request,
    bill_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(bill_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid vendor bill ID."
            },
            status=400,
        )

    bill = (
        VendorBillRepository.get_by_id(
            organization=user.organization,
            bill_id=bill_id,
        )
    )

    if not bill:
        return JsonResponse(
            {
                "error":
                    "Vendor bill not found."
            },
            status=404,
        )

    if request.method == "GET":
        try:
            VendorBillService._check_permission(
                user,
                "bills.read",
            )

            payments = (
                SupplierPaymentRepository
                .list_by_vendor_bill(
                    organization=(
                        user.organization
                    ),
                    vendor_bill=bill,
                )
            )

            return JsonResponse(
                {
                    "bill": {
                        "id": str(
                            bill.id
                        ),
                        "bill_number":
                            bill.bill_number,
                        "status":
                            bill.status,
                        "total_amount": str(
                            bill.total_amount
                        ),
                        "amount_paid": str(
                            bill.amount_paid
                        ),
                        "balance_due": str(
                            bill.balance_due
                        ),
                    },
                    "count":
                        payments.count(),
                    "payments": [
                        _supplier_payment_response(
                            payment
                        )
                        for payment in payments
                    ],
                },
                status=200,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    if request.method == "POST":
        try:
            data = json.loads(
                request.body or "{}"
            )

            if "amount" not in data:
                return JsonResponse(
                    {
                        "error":
                            "amount is required."
                    },
                    status=400,
                )

            payment_method = (
                data.get(
                    "payment_method",
                    "",
                )
            )

            if not payment_method:
                return JsonResponse(
                    {
                        "error":
                            "payment_method "
                            "is required."
                    },
                    status=400,
                )

            payment_date = None

            if data.get("payment_date"):
                try:
                    payment_date = (
                        datetime.fromisoformat(
                            data[
                                "payment_date"
                            ]
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    return JsonResponse(
                        {
                            "error":
                                "Invalid "
                                "payment_date."
                        },
                        status=400,
                    )

            payment = (
                SupplierPaymentService
                .record_bill_payment(
                    user=user,
                    organization=(
                        user.organization
                    ),
                    vendor_bill=bill,
                    amount=data["amount"],
                    payment_method=(
                        payment_method
                    ),
                    payment_date=(
                        payment_date
                    ),
                    reference_number=(
                        data.get(
                            "reference_number",
                            "",
                        )
                    ),
                    notes=data.get(
                        "notes",
                        "",
                    ),
                )
            )

            bill.reload()

            return JsonResponse(
                {
                    "message":
                        "Supplier payment "
                        "recorded successfully.",
                    "supplier_payment":
                        _supplier_payment_response(
                            payment
                        ),
                    "vendor_bill":
                        _vendor_bill_response(
                            bill
                        ),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "error":
                        "Invalid JSON body."
                },
                status=400,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    return JsonResponse(
        {
            "error":
                "Method not allowed."
        },
        status=405,
    )


def supplier_payments(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        VendorBillService._check_permission(
            user,
            "bills.read",
        )

        payments = (
            SupplierPaymentRepository
            .list_by_organization(
                organization=(
                    user.organization
                ),
            )
        )

        return JsonResponse(
            {
                "count": payments.count(),
                "supplier_payments": [
                    _supplier_payment_response(
                        payment
                    )
                    for payment in payments
                ],
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )


def supplier_payment_detail(
    request,
    payment_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        ObjectId(payment_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid supplier "
                    "payment ID."
            },
            status=400,
        )

    try:
        VendorBillService._check_permission(
            user,
            "bills.read",
        )

        payment = (
            SupplierPaymentRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                payment_id=payment_id,
            )
        )

        if not payment:
            return JsonResponse(
                {
                    "error":
                        "Supplier payment "
                        "not found."
                },
                status=404,
            )

        return JsonResponse(
            {
                "supplier_payment":
                    _supplier_payment_response(
                        payment
                    )
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )


    
def _vendor_bill_response(bill):
    return {
        "id": str(bill.id),
        "bill_number": bill.bill_number,
        "supplier_invoice_number": (
            bill.supplier_invoice_number
        ),
        "status": bill.status,
        "purchase_order": {
            "id": str(
                bill.purchase_order.id
            ),
            "po_number": (
                bill.purchase_order.po_number
            ),
        } if bill.purchase_order else None,
        "supplier": {
            "id": str(
                bill.supplier.id
            ),
            "code": bill.supplier.code,
            "name": bill.supplier.name,
        },
        "bill_date": (
            bill.bill_date.isoformat()
            if bill.bill_date
            else None
        ),
        "due_date": (
            bill.due_date.isoformat()
            if bill.due_date
            else None
        ),
        "items": [
            {
                "product": {
                    "id": str(
                        item.product.id
                    ),
                    "sku": item.product.sku,
                    "name": item.product.name,
                },
                "quantity": str(
                    item.quantity
                ),
                "unit_price": str(
                    item.unit_price
                ),
                "tax_rate": str(
                    item.tax_rate
                ),
                "discount": str(
                    item.discount
                ),
                "line_subtotal": str(
                    item.line_subtotal
                ),
                "line_tax": str(
                    item.line_tax
                ),
                "line_total": str(
                    item.line_total
                ),
            }
            for item in bill.items
        ],
        "subtotal": str(
            bill.subtotal
        ),
        "tax_amount": str(
            bill.tax_amount
        ),
        "discount_amount": str(
            bill.discount_amount
        ),
        "total_amount": str(
            bill.total_amount
        ),
        "amount_paid": str(
            bill.amount_paid
        ),
        "balance_due": str(
            bill.balance_due
        ),
        "supplier_snapshot": {
            "name": bill.supplier_name,
            "address": bill.supplier_address,
            "city": bill.supplier_city,
            "state": bill.supplier_state,
            "country": bill.supplier_country,
            "pincode": bill.supplier_pincode,
            "gstin": bill.supplier_gstin,
        },
        "notes": bill.notes,
        "created_by": {
            "id": str(
                bill.created_by.id
            ),
            "email": bill.created_by.email,
        },
        "posted_at": (
            bill.posted_at.isoformat()
            if bill.posted_at
            else None
        ),
        "paid_at": (
            bill.paid_at.isoformat()
            if bill.paid_at
            else None
        ),
        "cancelled_at": (
            bill.cancelled_at.isoformat()
            if bill.cancelled_at
            else None
        ),
        "created_at": (
            bill.created_at.isoformat()
            if bill.created_at
            else None
        ),
        "updated_at": (
            bill.updated_at.isoformat()
            if bill.updated_at
            else None
        ),
    }

def _supplier_payment_response(
    payment,
):
    return {
        "id": str(payment.id),
        "payment_number":
            payment.payment_number,
        "supplier": {
            "id": str(
                payment.supplier.id
            ),
            "code":
                payment.supplier.code,
            "name":
                payment.supplier.name,
        },
        "payment_date": (
            payment.payment_date.isoformat()
            if payment.payment_date
            else None
        ),
        "amount": str(
            payment.amount
        ),
        "payment_method":
            payment.payment_method,
        "reference_number":
            payment.reference_number,
        "allocations": [
            {
                "vendor_bill": {
                    "id": str(
                        allocation
                        .vendor_bill.id
                    ),
                    "bill_number": (
                        allocation
                        .vendor_bill
                        .bill_number
                    ),
                },
                "amount": str(
                    allocation.amount
                ),
            }
            for allocation
            in payment.allocations
        ],
        "notes": payment.notes,
        "created_by": {
            "id": str(
                payment.created_by.id
            ),
            "email":
                payment.created_by.email,
        },
        "created_at": (
            payment.created_at.isoformat()
            if payment.created_at
            else None
        ),
        "updated_at": (
            payment.updated_at.isoformat()
            if payment.updated_at
            else None
        ),
    }
def vendor_bill_payments(
    request,
    bill_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(bill_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid vendor bill ID."
            },
            status=400,
        )

    bill = (
        VendorBillRepository.get_by_id(
            organization=user.organization,
            bill_id=bill_id,
        )
    )

    if not bill:
        return JsonResponse(
            {
                "error":
                    "Vendor bill not found."
            },
            status=404,
        )

    if request.method == "GET":
        try:
            VendorBillService._check_permission(
                user,
                "bills.read",
            )

            payments = (
                SupplierPaymentRepository
                .list_by_vendor_bill(
                    organization=(
                        user.organization
                    ),
                    vendor_bill=bill,
                )
            )

            return JsonResponse(
                {
                    "bill": {
                        "id": str(
                            bill.id
                        ),
                        "bill_number":
                            bill.bill_number,
                        "status":
                            bill.status,
                        "total_amount": str(
                            bill.total_amount
                        ),
                        "amount_paid": str(
                            bill.amount_paid
                        ),
                        "balance_due": str(
                            bill.balance_due
                        ),
                    },
                    "count":
                        payments.count(),
                    "payments": [
                        _supplier_payment_response(
                            payment
                        )
                        for payment in payments
                    ],
                },
                status=200,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    if request.method == "POST":
        try:
            data = json.loads(
                request.body or "{}"
            )

            if "amount" not in data:
                return JsonResponse(
                    {
                        "error":
                            "amount is required."
                    },
                    status=400,
                )

            payment_method = (
                data.get(
                    "payment_method",
                    "",
                )
            )

            if not payment_method:
                return JsonResponse(
                    {
                        "error":
                            "payment_method "
                            "is required."
                    },
                    status=400,
                )

            payment_date = None

            if data.get("payment_date"):
                try:
                    payment_date = (
                        datetime.fromisoformat(
                            data[
                                "payment_date"
                            ]
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    return JsonResponse(
                        {
                            "error":
                                "Invalid "
                                "payment_date."
                        },
                        status=400,
                    )

            payment = (
                SupplierPaymentService
                .record_bill_payment(
                    user=user,
                    organization=(
                        user.organization
                    ),
                    vendor_bill=bill,
                    amount=data["amount"],
                    payment_method=(
                        payment_method
                    ),
                    payment_date=(
                        payment_date
                    ),
                    reference_number=(
                        data.get(
                            "reference_number",
                            "",
                        )
                    ),
                    notes=data.get(
                        "notes",
                        "",
                    ),
                )
            )

            bill.reload()

            return JsonResponse(
                {
                    "message":
                        "Supplier payment "
                        "recorded successfully.",
                    "supplier_payment":
                        _supplier_payment_response(
                            payment
                        ),
                    "vendor_bill":
                        _vendor_bill_response(
                            bill
                        ),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "error":
                        "Invalid JSON body."
                },
                status=400,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    return JsonResponse(
        {
            "error":
                "Method not allowed."
        },
        status=405,
    )

def vendor_bills(request):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    organization = user.organization

    if request.method == "GET":
        try:
            VendorBillService._check_permission(
                user,
                "bills.read",
            )

            bills = (
                VendorBillRepository
                .list_by_organization(
                    organization=organization,
                )
            )

            return JsonResponse(
                {
                    "count": bills.count(),
                    "vendor_bills": [
                        _vendor_bill_response(
                            bill
                        )
                        for bill in bills
                    ],
                },
                status=200,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    if request.method == "POST":
        try:
            data = json.loads(
                request.body or "{}"
            )

            purchase_order_id = (
                data.get(
                    "purchase_order_id"
                )
            )

            if not purchase_order_id:
                return JsonResponse(
                    {
                        "error":
                            "purchase_order_id "
                            "is required."
                    },
                    status=400,
                )

            try:
                ObjectId(
                    purchase_order_id
                )
            except (
                InvalidId,
                TypeError,
            ):
                return JsonResponse(
                    {
                        "error":
                            "Invalid purchase "
                            "order ID."
                    },
                    status=400,
                )

            purchase_order = (
                PurchaseOrder.objects(
                    organization=organization,
                    id=purchase_order_id,
                ).first()
            )

            if not purchase_order:
                return JsonResponse(
                    {
                        "error":
                            "Purchase order "
                            "not found."
                    },
                    status=404,
                )

            bill = (
                VendorBillService
                .generate_from_purchase_order(
                    user=user,
                    organization=organization,
                    purchase_order=(
                        purchase_order
                    ),
                    supplier_invoice_number=(
                        data.get(
                            "supplier_invoice_number",
                            "",
                        )
                    ),
                    bill_date=None,
                    due_date=None,
                    notes=data.get(
                        "notes",
                        "",
                    ),
                )
            )

            return JsonResponse(
                {
                    "message":
                        "Vendor bill created "
                        "successfully.",
                    "vendor_bill":
                        _vendor_bill_response(
                            bill
                        ),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "error":
                        "Invalid JSON body."
                },
                status=400,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )

def vendor_bill_detail(
    request,
    bill_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        ObjectId(bill_id)
    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid vendor bill ID."
            },
            status=400,
        )

    try:
        VendorBillService._check_permission(
            user,
            "bills.read",
        )

        bill = (
            VendorBillRepository.get_by_id(
                organization=user.organization,
                bill_id=bill_id,
            )
        )

        if not bill:
            return JsonResponse(
                {
                    "error":
                        "Vendor bill not found."
                },
                status=404,
            )

        return JsonResponse(
            {
                "vendor_bill":
                    _vendor_bill_response(
                        bill
                    )
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def post_vendor_bill(
    request,
    bill_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        ObjectId(bill_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid vendor bill ID."
            },
            status=400,
        )

    try:
        bill = (
            VendorBillRepository.get_by_id(
                organization=user.organization,
                bill_id=bill_id,
            )
        )

        if not bill:
            return JsonResponse(
                {
                    "error":
                        "Vendor bill not found."
                },
                status=404,
            )

        bill = (
            VendorBillService.post_bill(
                user=user,
                organization=user.organization,
                bill=bill,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Vendor bill posted "
                    "successfully.",
                "vendor_bill":
                    _vendor_bill_response(
                        bill
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def accounts_payable_summary(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        VendorBillService._check_permission(
            user,
            "bills.read",
        )

        bills = (
            VendorBillRepository
            .list_outstanding(
                organization=(
                    user.organization
                ),
            )
        )

        net_bills = []

        total_outstanding = Decimal("0")

        for bill in bills:
            net_payable = (
                VendorDebitNoteService
                .get_vendor_bill_net_payable(
                    organization=user.organization,
                    vendor_bill=bill,
                )
            )

            if net_payable <= Decimal("0"):
                continue

            total_outstanding += (
                net_payable
            )

            bill_data = (
                _vendor_bill_response(
                    bill
                )
            )

            bill_data[
                "net_payable"
            ] = str(
                net_payable
            )

            net_bills.append(
                bill_data
            )

        return JsonResponse(
            {
                "total_outstanding": str(
                    total_outstanding
                ),
                "bill_count": len(
                    net_bills
                ),
                "vendor_bills":
                    net_bills,
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def supplier_outstanding(
    request,
    supplier_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        ObjectId(supplier_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid supplier ID."
            },
            status=400,
        )

    try:
        VendorBillService._check_permission(
            user,
            "bills.read",
        )

        supplier = Supplier.objects(
            organization=user.organization,
            id=supplier_id,
        ).first()

        if not supplier:
            return JsonResponse(
                {
                    "error":
                        "Supplier not found."
                },
                status=404,
            )

        bills = (
            VendorBillRepository
            .list_outstanding(
                organization=(
                    user.organization
                ),
                supplier=supplier,
            )
        )

        net_bills = []

        total_outstanding = Decimal("0")

        for bill in bills:
            net_payable = (
                VendorDebitNoteService
                .get_vendor_bill_net_payable(
                    organization=user.organization,
                    vendor_bill=bill,
                )
            )

            if net_payable <= Decimal("0"):
                continue

            total_outstanding += (
                net_payable
            )

            bill_data = (
                _vendor_bill_response(
                    bill
                )
            )

            bill_data[
                "net_payable"
            ] = str(
                net_payable
            )

            net_bills.append(
                bill_data
            )

        return JsonResponse(
            {
                "supplier": {
                    "id": str(
                        supplier.id
                    ),
                    "code": supplier.code,
                    "name": supplier.name,
                },
                "total_outstanding": str(
                    total_outstanding
                ),
                "bill_count": len(
                    net_bills
                ),
                "vendor_bills":
                    net_bills,
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def cancel_vendor_bill(
    request,
    bill_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        ObjectId(bill_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid vendor bill ID."
            },
            status=400,
        )

    try:
        bill = (
            VendorBillRepository.get_by_id(
                organization=user.organization,
                bill_id=bill_id,
            )
        )

        if not bill:
            return JsonResponse(
                {
                    "error":
                        "Vendor bill not found."
                },
                status=404,
            )

        bill = (
            VendorBillService.cancel_bill(
                user=user,
                organization=user.organization,
                bill=bill,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Vendor bill cancelled "
                    "successfully.",
                "vendor_bill":
                    _vendor_bill_response(
                        bill
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def cancel_purchase_return(
    request,
    purchase_return_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Authentication required."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        try:
            ObjectId(
                purchase_return_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid purchase return ID."
            )

        purchase_return = (
            PurchaseReturnRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                purchase_return_id=(
                    purchase_return_id
                ),
            )
        )

        if not purchase_return:
            return JsonResponse(
                {
                    "error":
                        "Purchase return not found."
                },
                status=404,
            )

        purchase_return = (
            PurchaseReturnService
            .cancel_purchase_return(
                user=user,
                organization=(
                    user.organization
                ),
                purchase_return=(
                    purchase_return
                ),
            )
        )

        return JsonResponse(
            {
                "message":
                    "Purchase return cancelled "
                    "successfully.",
                "purchase_return":
                    _purchase_return_response(
                        purchase_return
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def _vendor_debit_note_response(
    debit_note,
):
    return {
        "id": str(
            debit_note.id
        ),
        "debit_note_number":
            debit_note.debit_note_number,
        "status":
            debit_note.status,
        "purchase_return": {
            "id": str(
                debit_note.purchase_return.id
            ),
            "return_number":
                debit_note
                .purchase_return
                .return_number,
        },
        "vendor_bill": {
            "id": str(
                debit_note.vendor_bill.id
            ),
            "bill_number":
                debit_note
                .vendor_bill
                .bill_number,
        },
        "purchase_order": {
            "id": str(
                debit_note.purchase_order.id
            ),
            "po_number":
                debit_note
                .purchase_order
                .po_number,
        },
        "supplier": {
            "id": str(
                debit_note.supplier.id
            ),
            "name":
                debit_note.supplier.name,
        },
        "debit_note_date": (
            debit_note.debit_note_date.isoformat()
            if debit_note.debit_note_date
            else None
        ),
        "items": [
            {
                "product": {
                    "id": str(
                        item.product.id
                    ),
                    "sku":
                        item.product.sku,
                    "name":
                        item.product.name,
                },
                "quantity":
                    str(item.quantity),
                "unit_price":
                    str(item.unit_price),
                "tax_rate":
                    str(item.tax_rate),
                "discount":
                    str(item.discount),
                "line_subtotal":
                    str(
                        item.line_subtotal
                    ),
                "line_tax":
                    str(item.line_tax),
                "line_total":
                    str(item.line_total),
            }
            for item in debit_note.items
        ],
        "subtotal":
            str(debit_note.subtotal),
        "tax_amount":
            str(debit_note.tax_amount),
        "discount_amount":
            str(
                debit_note.discount_amount
            ),
        "total_amount":
            str(debit_note.total_amount),
        "applied_amount":
            str(debit_note.applied_amount),
        "remaining_credit":
            str(
                debit_note.remaining_credit
            ),
        "reason":
            debit_note.reason,
        "notes":
            debit_note.notes,
        "created_by": {
            "id": str(
                debit_note.created_by.id
            ),
            "email":
                debit_note.created_by.email,
        },
        "issued_at": (
            debit_note.issued_at.isoformat()
            if debit_note.issued_at
            else None
        ),
        "cancelled_at": (
            debit_note.cancelled_at.isoformat()
            if debit_note.cancelled_at
            else None
        ),
        "created_at": (
            debit_note.created_at.isoformat()
            if debit_note.created_at
            else None
        ),
    }

def vendor_debit_notes(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Authentication required."
            },
            status=401,
        )

    organization = user.organization

    if request.method == "GET":
        try:
            VendorDebitNoteService._check_permission(
                user,
                "vendor_debit_notes.read",
            )

            notes = (
                VendorDebitNoteRepository
                .list_by_organization(
                    organization=organization,
                )
            )

            return JsonResponse(
                {
                    "count":
                        notes.count(),
                    "vendor_debit_notes": [
                        _vendor_debit_note_response(
                            note
                        )
                        for note in notes
                    ],
                },
                status=200,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    if request.method == "POST":
        try:
            payload = json.loads(
                request.body
            )

            purchase_return_id = (
                payload.get(
                    "purchase_return_id"
                )
            )

            if not purchase_return_id:
                raise ValueError(
                    "purchase_return_id is required."
                )

            try:
                ObjectId(
                    purchase_return_id
                )
            except (
                InvalidId,
                TypeError,
            ):
                raise ValueError(
                    "Invalid purchase return ID."
                )

            purchase_return = (
                PurchaseReturn.objects(
                    organization=organization,
                    id=purchase_return_id,
                ).first()
            )

            if not purchase_return:
                return JsonResponse(
                    {
                        "error":
                            "Purchase return not found."
                    },
                    status=404,
                )

            debit_note_date = (
                payload.get(
                    "debit_note_date"
                )
            )

            if debit_note_date:
                try:
                    debit_note_date = (
                        datetime.fromisoformat(
                            debit_note_date
                        )
                    )
                except ValueError:
                    raise ValueError(
                        "Invalid debit_note_date."
                    )

            debit_note = (
                VendorDebitNoteService
                .create_from_purchase_return(
                    user=user,
                    organization=organization,
                    purchase_return=(
                        purchase_return
                    ),
                    debit_note_date=(
                        debit_note_date
                    ),
                    reason=payload.get(
                        "reason",
                        "",
                    ),
                    notes=payload.get(
                        "notes",
                        "",
                    ),
                )
            )

            return JsonResponse(
                {
                    "message":
                        "Vendor debit note created "
                        "successfully.",
                    "vendor_debit_note":
                        _vendor_debit_note_response(
                            debit_note
                        ),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "error":
                        "Invalid JSON body."
                },
                status=400,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    return JsonResponse(
        {
            "error":
                "Method not allowed."
        },
        status=405,
    )

def vendor_debit_note_detail(
    request,
    debit_note_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Authentication required."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        VendorDebitNoteService._check_permission(
            user,
            "vendor_debit_notes.read",
        )

        try:
            ObjectId(
                debit_note_id
            )
        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid vendor debit note ID."
            )

        debit_note = (
            VendorDebitNoteRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                debit_note_id=(
                    debit_note_id
                ),
            )
        )

        if not debit_note:
            return JsonResponse(
                {
                    "error":
                        "Vendor debit note not found."
                },
                status=404,
            )

        return JsonResponse(
            {
                "vendor_debit_note":
                    _vendor_debit_note_response(
                        debit_note
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def issue_vendor_debit_note(
    request,
    debit_note_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Authentication required."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        try:
            ObjectId(
                debit_note_id
            )
        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid vendor debit note ID."
            )

        debit_note = (
            VendorDebitNoteRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                debit_note_id=(
                    debit_note_id
                ),
            )
        )

        if not debit_note:
            return JsonResponse(
                {
                    "error":
                        "Vendor debit note not found."
                },
                status=404,
            )

        debit_note = (
            VendorDebitNoteService
            .issue_debit_note(
                user=user,
                organization=(
                    user.organization
                ),
                debit_note=debit_note,
            )
        )

        net_payable = (
            VendorDebitNoteService
            .get_vendor_bill_net_payable(
                organization=(
                    user.organization
                ),
                vendor_bill=(
                    debit_note.vendor_bill
                ),
            )
        )

        return JsonResponse(
            {
                "message":
                    "Vendor debit note issued "
                    "successfully.",
                "vendor_debit_note":
                    _vendor_debit_note_response(
                        debit_note
                    ),
                "vendor_bill_net_payable":
                    str(net_payable),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def cancel_vendor_debit_note(
    request,
    debit_note_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Authentication required."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        try:
            ObjectId(
                debit_note_id
            )
        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid vendor debit note ID."
            )

        debit_note = (
            VendorDebitNoteRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                debit_note_id=(
                    debit_note_id
                ),
            )
        )

        if not debit_note:
            return JsonResponse(
                {
                    "error":
                        "Vendor debit note not found."
                },
                status=404,
            )

        debit_note = (
            VendorDebitNoteService
            .cancel_debit_note(
                user=user,
                organization=(
                    user.organization
                ),
                debit_note=debit_note,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Vendor debit note cancelled "
                    "successfully.",
                "vendor_debit_note":
                    _vendor_debit_note_response(
                        debit_note
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def purchase_order_pdf(
    request,
    purchase_order_id,
):
    user = request.user

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        PDFSecurity.require_permission(
            user=user,
            permission_code="purchase_orders.read",
        )

    except PermissionError as exc:
        message = str(exc)

        status_code = (
            401
            if message == "Not authenticated."
            else 403
        )

        return JsonResponse(
            {
                "error": message
            },
            status=status_code,
        )

    organization = (
        user.organization
    )

    try:
        try:
            ObjectId(
                purchase_order_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid purchase order ID."
            )

        purchase_order = (
            PurchaseOrderRepository
            .get_by_id(
                organization=organization,
                purchase_order_id=(
                    purchase_order_id
                ),
            )
        )

        if not purchase_order:
            return JsonResponse(
                {
                    "error":
                        "Purchase order not found."
                },
                status=404,
            )

        pdf_bytes = (
            PurchaseOrderPDF.generate(
                purchase_order=(
                    purchase_order
                ),
            )
        )
        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type="PURCHASE_ORDER",
            document_id=purchase_order.id,
            document_number=purchase_order.po_number,
        )
        filename = (
            f"{purchase_order.po_number}.pdf"
        )

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

        response[
            "Content-Disposition"
        ] = (
            f'attachment; filename="{filename}"'
        )

        response[
            "Content-Length"
        ] = str(
            len(pdf_bytes)
        )

        return response

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    except Exception:

        return JsonResponse(
            {
                "error":
                    "PDF generation failed."
            },
            status=500,
        )

def vendor_bill_pdf(
    request,
    vendor_bill_id,
):
    user = request.user

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        PDFSecurity.require_permission(
            user=user,
            permission_code="vendor_bills.read",
        )

    except PermissionError as exc:
        message = str(exc)

        status_code = (
            401
            if message == "Not authenticated."
            else 403
        )

        return JsonResponse(
            {
                "error": message
            },
            status=status_code,
        )

    organization = (
        user.organization
    )

    try:
        try:
            ObjectId(
                vendor_bill_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid vendor bill ID."
            )

        vendor_bill = (
            VendorBillRepository
            .get_by_id(
                organization=organization,
                bill_id=vendor_bill_id,
            )
        )

        if not vendor_bill:
            return JsonResponse(
                {
                    "error":
                        "Vendor bill not found."
                },
                status=404,
            )

        pdf_bytes = (
            VendorBillPDF.generate(
                vendor_bill=vendor_bill,
            )
        )
        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type="VENDOR_BILL",
            document_id=vendor_bill.id,
            document_number=vendor_bill.bill_number,
        )
        filename = (
            f"{vendor_bill.bill_number}.pdf"
        )

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

        response[
            "Content-Disposition"
        ] = (
            f'attachment; filename="{filename}"'
        )

        response[
            "Content-Length"
        ] = str(
            len(pdf_bytes)
        )

        return response

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    except Exception:

        return JsonResponse(
            {
                "error":
                    "PDF generation failed."
            },
            status=500,
        )

def vendor_debit_note_pdf(
    request,
    vendor_debit_note_id,
):
    user = request.user

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        PDFSecurity.require_permission(
            user=user,
            permission_code="vendor_debit_notes.read",
        )

    except PermissionError as exc:
        message = str(exc)

        status_code = (
            401
            if message == "Not authenticated."
            else 403
        )

        return JsonResponse(
            {
                "error": message
            },
            status=status_code,
        )

    organization = (
        user.organization
    )

    try:
        try:
            ObjectId(
                vendor_debit_note_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid vendor debit note ID."
            )

        debit_note = (
            VendorDebitNoteRepository
            .get_by_id(
                organization=organization,
                debit_note_id=(
                    vendor_debit_note_id
                ),
            )
        )

        if not debit_note:
            return JsonResponse(
                {
                    "error":
                        "Vendor debit note not found."
                },
                status=404,
            )

        pdf_bytes = (
            VendorDebitNotePDF.generate(
                debit_note=debit_note,
            )
        )
        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type="VENDOR_DEBIT_NOTE",
            document_id=debit_note.id,
            document_number=debit_note.debit_note_number,
        )
        filename = (
            f"{debit_note.debit_note_number}.pdf"
        )

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

        response[
            "Content-Disposition"
        ] = (
            f'attachment; filename="{filename}"'
        )

        response[
            "Content-Length"
        ] = str(
            len(pdf_bytes)
        )

        return response

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    except Exception:

        return JsonResponse(
            {
                "error":
                    "PDF generation failed."
            },
            status=500,
        )
    
def supplier_payment_pdf(
    request,
    payment_id,
):
    user = request.user

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        PDFSecurity.require_permission(
            user=user,
            permission_code="supplier_payments.read",
        )

    except PermissionError as exc:
        message = str(exc)

        status_code = (
            401
            if message == "Not authenticated."
            else 403
        )

        return JsonResponse(
            {
                "error": message
            },
            status=status_code,
        )

    organization = (
        user.organization
    )

    try:
        try:
            ObjectId(
                payment_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid supplier payment ID."
            )

        payment = (
            SupplierPaymentRepository
            .get_by_id(
                organization=organization,
                payment_id=payment_id,
            )
        )

        if not payment:
            return JsonResponse(
                {
                    "error":
                        "Supplier payment not found."
                },
                status=404,
            )

        pdf_bytes = (
            SupplierPaymentReceiptPDF
            .generate(
                payment=payment,
            )
        )
        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type="SUPPLIER_PAYMENT",
            document_id=payment.id,
            document_number=payment.payment_number,
        )
        filename = (
            f"{payment.payment_number}.pdf"
        )

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

        response[
            "Content-Disposition"
        ] = (
            f'attachment; filename="{filename}"'
        )

        response[
            "Content-Length"
        ] = str(
            len(pdf_bytes)
        )

        return response

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    except Exception:

        return JsonResponse(
            {
                "error":
                    "PDF generation failed."
            },
            status=500,
        )

def goods_receipt_pdf(
    request,
    grn_id,
):
    user = request.user

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        PDFSecurity.require_permission(
            user=user,
            permission_code="goods_receipts.read",
        )

    except PermissionError as exc:
        message = str(exc)

        status_code = (
            401
            if message == "Not authenticated."
            else 403
        )

        return JsonResponse(
            {
                "error": message
            },
            status=status_code,
        )

    organization = (
        user.organization
    )

    try:
        try:
            ObjectId(
                grn_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid goods receipt ID."
            )

        goods_receipt = (
            GoodsReceiptRepository
            .get_by_id(
                organization=organization,
                goods_receipt_id=grn_id,
            )
        )

        if not goods_receipt:
            return JsonResponse(
                {
                    "error":
                        "Goods receipt not found."
                },
                status=404,
            )

        pdf_bytes = (
            GoodsReceiptPDF.generate(
                goods_receipt=goods_receipt,
            )
        )
        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type="GOODS_RECEIPT",
            document_id=goods_receipt.id,
            document_number=goods_receipt.grn_number,
        )
        filename = (
            f"{goods_receipt.grn_number}.pdf"
        )

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

        response[
            "Content-Disposition"
        ] = (
            f'attachment; filename="{filename}"'
        )

        response[
            "Content-Length"
        ] = str(
            len(pdf_bytes)
        )

        return response

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    except Exception:

        return JsonResponse(
            {
                "error":
                    "PDF generation failed."
            },
            status=500,
        )

def purchase_order_email(
    request,
    purchase_order_id,
):
    return (
        DocumentEmailAPIService
        .handle(
            request=request,
            document_type="PURCHASE_ORDER",
            document_id=purchase_order_id,
        )
    )


def vendor_bill_email(
    request,
    vendor_bill_id,
):
    return (
        DocumentEmailAPIService
        .handle(
            request=request,
            document_type="VENDOR_BILL",
            document_id=vendor_bill_id,
        )
    )


def vendor_debit_note_email(
    request,
    debit_note_id,
):
    return (
        DocumentEmailAPIService
        .handle(
            request=request,
            document_type="VENDOR_DEBIT_NOTE",
            document_id=debit_note_id,
        )
    )


def supplier_payment_email(
    request,
    payment_id,
):
    return (
        DocumentEmailAPIService
        .handle(
            request=request,
            document_type="SUPPLIER_PAYMENT",
            document_id=payment_id,
        )
    )


def goods_receipt_email(
    request,
    goods_receipt_id,
):
    return (
        DocumentEmailAPIService
        .handle(
            request=request,
            document_type="GOODS_RECEIPT",
            document_id=goods_receipt_id,
        )
    )