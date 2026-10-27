import json
from decimal import Decimal
from bson import ObjectId
from bson.errors import InvalidId
from django.http import JsonResponse, HttpResponse
from apps.finance.documents.sales_order_pdf import (
    SalesOrderPDF,
)
from apps.finance.services.document_email_delivery_service import (
    DocumentEmailDeliveryService,
)
from apps.finance.documents.pdf_security import (
    PDFSecurity,
)
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.sales.services.customer_service import (
    CustomerService,
)
from datetime import datetime

from apps.products.models import Product
from apps.inventory.models import Warehouse
from apps.sales.models import (
    Customer,
    SalesOrder,
    Invoice,
    CustomerPayment,
)
from apps.sales.services.sales_order_service import (
    SalesOrderService,
)

from apps.finance.documents.invoice_pdf import (
    InvoicePDF,
)
from apps.sales.services.invoice_service import (
    InvoiceService,
)

from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.sales.services.payment_service import (
    PaymentService,
)
from apps.finance.documents.customer_payment_receipt_pdf import (
    CustomerPaymentReceiptPDF,
)
from apps.sales.repositories.payment_repository import (
    PaymentRepository,
)

from apps.sales.repositories.sales_return_repository import (
    SalesReturnRepository,
)

from apps.sales.services.sales_return_service import (
    SalesReturnService,
)
from apps.finance.documents.credit_note_pdf import (
    CreditNotePDF,
)


from apps.sales.repositories.credit_note_repository import (
    CreditNoteRepository,
)

from apps.sales.services.credit_note_service import (
    CreditNoteService,
)

from apps.sales.models import (
    SalesReturn,
)
from apps.finance.services.document_audit_service import (
    DocumentAuditService,
)
from apps.finance.services.document_email_api_service import (
    DocumentEmailAPIService,
)
def _customer_response(customer):
    return {
        "id": str(customer.id),
        "code": customer.code,
        "name": customer.name,
        "email": customer.email or "",
        "phone": customer.phone,
        "gstin": customer.gstin,
        "billing_address": customer.billing_address,
        "shipping_address": customer.shipping_address,
        "city": customer.city,
        "state": customer.state,
        "country": customer.country,
        "pincode": customer.pincode,
        "is_active": customer.is_active,
        "created_at": (
            customer.created_at.isoformat()
            if customer.created_at
            else None
        ),
        "updated_at": (
            customer.updated_at.isoformat()
            if customer.updated_at
            else None
        ),
    }


def customer_list(request):
    """
    GET  /sales/customers/
    POST /sales/customers/
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
            customers = CustomerService.list_customers(
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
            _customer_response(customer)
            for customer in customers
        ]

        return JsonResponse(
            {
                "count": len(data),
                "customers": data,
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
                    "error":
                    "Missing required fields.",
                    "fields": missing_fields,
                },
                status=400,
            )

        try:
            customer = CustomerService.create_customer(
                user=user,
                organization=user.organization,
                name=data.get("name", ""),
                code=data.get("code", ""),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                gstin=data.get("gstin", ""),
                billing_address=data.get(
                    "billing_address",
                    "",
                ),
                shipping_address=data.get(
                    "shipping_address",
                    "",
                ),
                city=data.get("city", ""),
                state=data.get("state", ""),
                country=data.get(
                    "country",
                    "India",
                ),
                pincode=data.get(
                    "pincode",
                    "",
                ),
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
                "Customer created successfully.",
                "customer":
                _customer_response(customer),
            },
            status=201,
        )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )


def customer_detail(
    request,
    customer_id,
):
    """
    GET /sales/customers/<id>/
    PUT /sales/customers/<id>/
    """

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(customer_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid customer ID."},
            status=400,
        )

    if request.method == "GET":
        try:
            customer = CustomerService.get_customer(
                user=user,
                organization=user.organization,
                customer_id=customer_id,
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
            _customer_response(customer),
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

        try:
            customer = CustomerService.update_customer(
                user=user,
                organization=user.organization,
                customer_id=customer_id,
                name=data.get("name"),
                email=data.get("email"),
                phone=data.get("phone"),
                gstin=data.get("gstin"),
                billing_address=data.get(
                    "billing_address"
                ),
                shipping_address=data.get(
                    "shipping_address"
                ),
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
                "Customer updated successfully.",
                "customer":
                _customer_response(customer),
            },
            status=200,
        )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )


def customer_deactivate(
    request,
    customer_id,
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
        ObjectId(customer_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid customer ID."},
            status=400,
        )

    try:
        customer = CustomerService.deactivate_customer(
            user=user,
            organization=user.organization,
            customer_id=customer_id,
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
            "Customer deactivated successfully.",
            "customer":
            _customer_response(customer),
        },
        status=200,
    )


def customer_activate(
    request,
    customer_id,
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
        ObjectId(customer_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid customer ID."},
            status=400,
        )

    try:
        customer = CustomerService.activate_customer(
            user=user,
            organization=user.organization,
            customer_id=customer_id,
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
            "Customer activated successfully.",
            "customer":
            _customer_response(customer),
        },
        status=200,
    )

def _sales_order_response(sales_order):
    items = []

    for item in sales_order.items:
        items.append(
            {
                "product": {
                    "id": str(item.product.id),
                    "sku": item.product.sku,
                    "name": item.product.name,
                },
                "quantity": str(item.quantity),
                "fulfilled_quantity": str(
                    item.fulfilled_quantity
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
        )

    return {
        "id": str(sales_order.id),
        "so_number": sales_order.so_number,
        "status": sales_order.status,

        "customer": {
            "id": str(
                sales_order.customer.id
            ),
            "code":
                sales_order.customer.code,
            "name":
                sales_order.customer.name,
        },

        "warehouse": {
            "id": str(
                sales_order.warehouse.id
            ),
            "code":
                sales_order.warehouse.code,
            "name":
                sales_order.warehouse.name,
        },

        "order_date": (
            sales_order.order_date.isoformat()
            if sales_order.order_date
            else None
        ),

        "expected_delivery_date": (
            sales_order
            .expected_delivery_date
            .isoformat()
            if sales_order.expected_delivery_date
            else None
        ),

        "items": items,

        "subtotal": str(
            sales_order.subtotal
        ),

        "tax_amount": str(
            sales_order.tax_amount
        ),

        "discount_amount": str(
            sales_order.discount_amount
        ),

        "total_amount": str(
            sales_order.total_amount
        ),

        "notes": sales_order.notes,

        "created_by": {
            "id": str(
                sales_order.created_by.id
            ),
            "email":
                sales_order.created_by.email,
        },

        "confirmed_at": (
            sales_order.confirmed_at.isoformat()
            if sales_order.confirmed_at
            else None
        ),

        "fulfilled_at": (
            sales_order.fulfilled_at.isoformat()
            if sales_order.fulfilled_at
            else None
        ),

        "cancelled_at": (
            sales_order.cancelled_at.isoformat()
            if sales_order.cancelled_at
            else None
        ),

        "created_at": (
            sales_order.created_at.isoformat()
            if sales_order.created_at
            else None
        ),

        "updated_at": (
            sales_order.updated_at.isoformat()
            if sales_order.updated_at
            else None
        ),
    }

def _build_sales_order_request_items(
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

    items = []

    for raw_item in raw_items:

        if not isinstance(
            raw_item,
            dict,
        ):
            raise ValueError(
                "Each sales order item "
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
                        "quantity"
                    ),
                "unit_price":
                    raw_item.get(
                        "unit_price"
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


def _parse_datetime(
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
        return datetime.fromisoformat(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        raise ValueError(
            f"Invalid {field_name}. "
            "Use ISO format."
        )

def sales_order_list(request):
    """
    GET  /sales/orders/
    POST /sales/orders/
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

        status = request.GET.get(
            "status"
        )

        try:
            sales_orders = (
                SalesOrderService
                .list_sales_orders(
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
            _sales_order_response(
                sales_order
            )
            for sales_order
            in sales_orders
        ]

        return JsonResponse(
            {
                "count": len(data),
                "sales_orders": data,
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
                        "JSON body must "
                        "be an object."
                },
                status=400,
            )

        customer_id = data.get(
            "customer_id"
        )

        warehouse_id = data.get(
            "warehouse_id"
        )

        if not customer_id:
            return JsonResponse(
                {
                    "error":
                        "customer_id is required."
                },
                status=400,
            )

        if not warehouse_id:
            return JsonResponse(
                {
                    "error":
                        "warehouse_id is required."
                },
                status=400,
            )

        try:
            ObjectId(customer_id)
            ObjectId(warehouse_id)

        except (
            InvalidId,
            TypeError,
        ):
            return JsonResponse(
                {
                    "error":
                        "Invalid customer or "
                        "warehouse ID."
                },
                status=400,
            )

        customer = Customer.objects(
            organization=user.organization,
            id=customer_id,
        ).first()

        if not customer:
            return JsonResponse(
                {
                    "error":
                        "Customer not found."
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
            order_date = _parse_datetime(
                data.get(
                    "order_date"
                ),
                "order_date",
                required=True,
            )

            expected_delivery_date = (
                _parse_datetime(
                    data.get(
                        "expected_delivery_date"
                    ),
                    "expected_delivery_date",
                )
            )

            raw_items = (
                _build_sales_order_request_items(
                    organization=user.organization,
                    raw_items=data.get(
                        "items"
                    ),
                )
            )

            sales_order = (
                SalesOrderService
                .create_sales_order(
                    user=user,
                    organization=user.organization,
                    customer=customer,
                    warehouse=warehouse,
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
                    "Sales order created successfully.",

                "sales_order":
                    _sales_order_response(
                        sales_order
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

def sales_order_detail(
    request,
    sales_order_id,
):
    """
    GET /sales/orders/<id>/
    PUT /sales/orders/<id>/
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

    try:
        ObjectId(
            sales_order_id
        )

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid sales order ID."
            },
            status=400,
        )

    if request.method == "GET":

        try:
            sales_order = (
                SalesOrderService
                .get_sales_order(
                    user=user,
                    organization=user.organization,
                    sales_order_id=sales_order_id,
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
            _sales_order_response(
                sales_order
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

        customer = None
        warehouse = None

        if "customer_id" in data:

            customer_id = data.get(
                "customer_id"
            )

            try:
                ObjectId(
                    customer_id
                )

            except (
                InvalidId,
                TypeError,
            ):
                return JsonResponse(
                    {
                        "error":
                            "Invalid customer ID."
                    },
                    status=400,
                )

            customer = Customer.objects(
                organization=user.organization,
                id=customer_id,
            ).first()

            if not customer:
                return JsonResponse(
                    {
                        "error":
                            "Customer not found."
                    },
                    status=404,
                )

        if "warehouse_id" in data:

            warehouse_id = data.get(
                "warehouse_id"
            )

            try:
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
                            "Invalid warehouse ID."
                    },
                    status=400,
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
            order_date = None

            if "order_date" in data:
                order_date = (
                    _parse_datetime(
                        data.get(
                            "order_date"
                        ),
                        "order_date",
                        required=True,
                    )
                )

            expected_delivery_date = None

            if (
                "expected_delivery_date"
                in data
            ):
                expected_delivery_date = (
                    _parse_datetime(
                        data.get(
                            "expected_delivery_date"
                        ),
                        "expected_delivery_date",
                    )
                )

            raw_items = None

            if "items" in data:
                raw_items = (
                    _build_sales_order_request_items(
                        organization=user.organization,
                        raw_items=data.get(
                            "items"
                        ),
                    )
                )

            sales_order = (
                SalesOrderService
                .update_sales_order(
                    user=user,
                    organization=user.organization,
                    sales_order_id=sales_order_id,
                    customer=customer,
                    warehouse=warehouse,
                    order_date=order_date,
                    expected_delivery_date=(
                        expected_delivery_date
                    ),
                    raw_items=raw_items,
                    notes=(
                        data.get(
                            "notes"
                        )
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
                    "Sales order updated successfully.",

                "sales_order":
                    _sales_order_response(
                        sales_order
                    ),
            },
            status=200,
        )

    return JsonResponse(
        {
            "error":
                "Method not allowed."
        },
        status=405,
    )

def sales_order_confirm(
    request,
    sales_order_id,
):
    """
    Confirm a draft sales order and
    reserve its inventory.
    """

    if request.method != "PUT":
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
            sales_order_id
        )

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid sales order ID."
            },
            status=400,
        )

    try:
        sales_order = (
            SalesOrderService
            .confirm_sales_order(
                user=user,
                organization=user.organization,
                sales_order_id=sales_order_id,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    return JsonResponse(
        {
            "message":
                "Sales order confirmed successfully.",

            "sales_order":
                _sales_order_response(
                    sales_order
                ),
        },
        status=200,
    )

def sales_order_cancel(
    request,
    sales_order_id,
):
    """
    Cancel a sales order and release
    inventory reservations when required.
    """

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
        ObjectId(
            sales_order_id
        )

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid sales order ID."
            },
            status=400,
        )

    try:
        sales_order = (
            SalesOrderService.cancel_sales_order(
                user=user,
                organization=user.organization,
                sales_order_id=sales_order_id,
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
                "Sales order cancelled successfully.",
            "sales_order":
                _sales_order_response(
                    sales_order
                ),
        },
        status=200,
    )

def _build_sales_fulfilment_items(
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
            "Fulfilment must contain at least one item."
        )

    items = []

    product_ids = set()

    for raw_item in raw_items:

        if not isinstance(
            raw_item,
            dict,
        ):
            raise ValueError(
                "Each fulfilment item "
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
                "Duplicate product in fulfilment."
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
                "quantity":
                    raw_item.get(
                        "quantity"
                    ),
            }
        )

    return items

def sales_order_fulfill(
    request,
    sales_order_id,
):
    """
    Partially or fully dispatch
    a confirmed sales order.
    """

    if request.method != "PUT":
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
            sales_order_id
        )

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid sales order ID."
            },
            status=400,
        )

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
                    "JSON body must be an object."
            },
            status=400,
        )

    try:
        raw_items = (
            _build_sales_fulfilment_items(
                organization=user.organization,
                raw_items=data.get(
                    "items"
                ),
            )
        )

        sales_order = (
            SalesOrderService
            .fulfill_sales_order(
                user=user,
                organization=user.organization,
                sales_order_id=sales_order_id,
                raw_items=raw_items,
                notes=data.get(
                    "notes",
                    "",
                ),
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    return JsonResponse(
        {
            "message":
                "Sales order fulfilled successfully.",

            "sales_order":
                _sales_order_response(
                    sales_order
                ),
        },
        status=200,
    )

def _invoice_response(invoice):
    items = []

    for item in invoice.items:
        items.append(
            {
                "product": {
                    "id": str(item.product.id),
                    "sku": item.product.sku,
                    "name": item.product.name,
                },
                "quantity": str(item.quantity),
                "unit_price": str(item.unit_price),
                "tax_rate": str(item.tax_rate),
                "discount": str(item.discount),
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
        )

    return {
        "id": str(invoice.id),
        "invoice_number":
            invoice.invoice_number,
        "status": invoice.status,

        "sales_order": {
            "id": str(
                invoice.sales_order.id
            ),
            "so_number":
                invoice.sales_order.so_number,
        } if invoice.sales_order else None,

        "customer": {
            "id": str(
                invoice.customer.id
            ),
            "code":
                invoice.customer.code,
            "name":
                invoice.customer.name,
        },

        "invoice_date": (
            invoice.invoice_date.isoformat()
            if invoice.invoice_date
            else None
        ),

        "due_date": (
            invoice.due_date.isoformat()
            if invoice.due_date
            else None
        ),

        "items": items,

        "subtotal": str(
            invoice.subtotal
        ),

        "tax_amount": str(
            invoice.tax_amount
        ),

        "discount_amount": str(
            invoice.discount_amount
        ),

        "total_amount": str(
            invoice.total_amount
        ),

        "amount_paid": str(
            invoice.amount_paid
        ),

        "balance_due": str(
            invoice.balance_due
        ),

        "billing": {
            "name":
                invoice.billing_name,
            "address":
                invoice.billing_address,
            "city":
                invoice.billing_city,
            "state":
                invoice.billing_state,
            "country":
                invoice.billing_country,
            "pincode":
                invoice.billing_pincode,
            "gstin":
                invoice.customer_gstin,
        },

        "notes":
            invoice.notes,

        "created_by": {
            "id": str(
                invoice.created_by.id
            ),
            "email":
                invoice.created_by.email,
        },

        "issued_at": (
            invoice.issued_at.isoformat()
            if invoice.issued_at
            else None
        ),

        "paid_at": (
            invoice.paid_at.isoformat()
            if invoice.paid_at
            else None
        ),

        "cancelled_at": (
            invoice.cancelled_at.isoformat()
            if invoice.cancelled_at
            else None
        ),

        "created_at": (
            invoice.created_at.isoformat()
            if invoice.created_at
            else None
        ),

        "updated_at": (
            invoice.updated_at.isoformat()
            if invoice.updated_at
            else None
        ),
    }

def invoice_list(request):
    """
    GET  /sales/invoices/
    POST /sales/invoices/
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
            InvoiceService._check_permission(
                user,
                "invoices.read",
            )

            InvoiceService._check_organization(
                user,
                user.organization,
            )

            if status:
                status = status.strip().upper()

                if status not in (
                    InvoiceService
                    .VALID_STATUSES
                ):
                    raise ValueError(
                        "Invalid invoice status."
                    )

                invoices = (
                    InvoiceRepository
                    .list_by_status(
                        organization=(
                            user.organization
                        ),
                        status=status,
                    )
                )

            else:
                invoices = (
                    InvoiceRepository
                    .list_by_organization(
                        organization=(
                            user.organization
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

        data = [
            _invoice_response(invoice)
            for invoice in invoices
        ]

        return JsonResponse(
            {
                "count": len(data),
                "invoices": data,
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

        sales_order_id = data.get(
            "sales_order_id"
        )

        if not sales_order_id:
            return JsonResponse(
                {
                    "error":
                    "sales_order_id is required."
                },
                status=400,
            )

        try:
            ObjectId(
                sales_order_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            return JsonResponse(
                {
                    "error":
                    "Invalid sales order ID."
                },
                status=400,
            )

        sales_order = SalesOrder.objects(
            organization=user.organization,
            id=sales_order_id,
        ).first()

        if not sales_order:
            return JsonResponse(
                {
                    "error":
                    "Sales order not found."
                },
                status=404,
            )

        invoice_date = None
        due_date = None

        try:
            if data.get(
                "invoice_date"
            ):
                invoice_date = (
                    _parse_datetime(
                        data.get(
                            "invoice_date"
                        ),
                        "invoice_date",
                        required=True,
                    )
                )

            if data.get(
                "due_date"
            ):
                due_date = (
                    _parse_datetime(
                        data.get(
                            "due_date"
                        ),
                        "due_date",
                    )
                )

            invoice = (
                InvoiceService
                .generate_from_sales_order(
                    user=user,
                    organization=user.organization,
                    sales_order=sales_order,
                    invoice_date=invoice_date,
                    due_date=due_date,
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
                    "Invoice generated successfully.",
                "invoice":
                    _invoice_response(
                        invoice
                    ),
            },
            status=201,
        )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )

def invoice_detail(
    request,
    invoice_id,
):
    """
    GET /sales/invoices/<id>/
    """

    if request.method != "GET":
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
        ObjectId(invoice_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid invoice ID."
            },
            status=400,
        )

    try:
        InvoiceService._check_permission(
            user,
            "invoices.read",
        )

        InvoiceService._check_organization(
            user,
            user.organization,
        )

        invoice = (
            InvoiceRepository.get_by_id(
                organization=user.organization,
                invoice_id=invoice_id,
            )
        )

        if not invoice:
            return JsonResponse(
                {
                    "error":
                    "Invoice not found."
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
        _invoice_response(
            invoice
        ),
        status=200,
    )

def invoice_issue(
    request,
    invoice_id,
):
    """
    PUT /sales/invoices/<id>/issue/
    """

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
        ObjectId(invoice_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid invoice ID."
            },
            status=400,
        )

    try:
        invoice = (
            InvoiceService.issue_invoice(
                user=user,
                organization=user.organization,
                invoice_id=invoice_id,
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
                "Invoice issued successfully.",
            "invoice":
                _invoice_response(invoice),
        },
        status=200,
    )

def invoice_cancel(
    request,
    invoice_id,
):
    """
    PUT /sales/invoices/<id>/cancel/
    """

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
        ObjectId(invoice_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid invoice ID."
            },
            status=400,
        )

    try:
        invoice = (
            InvoiceService.cancel_invoice(
                user=user,
                organization=user.organization,
                invoice_id=invoice_id,
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
                "Invoice cancelled successfully.",
            "invoice":
                _invoice_response(invoice),
        },
        status=200,
    )

def customer_outstanding(
    request,
    customer_id,
):
    """
    GET /sales/customers/<id>/outstanding/
    """

    if request.method != "GET":
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
        ObjectId(customer_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid customer ID."
            },
            status=400,
        )

    customer = Customer.objects(
        organization=user.organization,
        id=customer_id,
    ).first()

    if not customer:
        return JsonResponse(
            {
                "error":
                    "Customer not found."
            },
            status=404,
        )

    try:
        result = (
            InvoiceService
            .get_customer_outstanding(
                user=user,
                organization=user.organization,
                customer=customer,
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

    invoices = []

    for invoice in result["invoices"]:
        invoices.append(
            {
                "id":
                    invoice["id"],
                "invoice_number":
                    invoice[
                        "invoice_number"
                    ],
                "status":
                    invoice["status"],
                "invoice_date": (
                    invoice[
                        "invoice_date"
                    ].isoformat()
                    if invoice[
                        "invoice_date"
                    ]
                    else None
                ),
                "due_date": (
                    invoice[
                        "due_date"
                    ].isoformat()
                    if invoice[
                        "due_date"
                    ]
                    else None
                ),
                "total_amount":
                    str(
                        invoice[
                            "total_amount"
                        ]
                    ),
                "amount_paid":
                    str(
                        invoice[
                            "amount_paid"
                        ]
                    ),
                "balance_due":
                    str(
                        invoice[
                            "balance_due"
                        ]
                    ),
            }
        )

    return JsonResponse(
        {
            "customer": {
                "id": str(
                    customer.id
                ),
                "code":
                    customer.code,
                "name":
                    customer.name,
            },
            "invoice_count":
                result["invoice_count"],
            "total_outstanding":
                str(
                    result[
                        "total_outstanding"
                    ]
                ),
            "invoices":
                invoices,
        },
        status=200,
    )

def accounts_receivable_summary(
    request,
):
    """
    GET /sales/accounts-receivable/
    """

    if request.method != "GET":
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
        result = (
            InvoiceService
            .get_organization_receivables(
                user=user,
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

    customers = []

    for item in result["customers"]:
        customer = item[
            "customer"
        ]

        customers.append(
            {
                "customer": {
                    "id":
                        str(customer.id),
                    "code":
                        customer.code,
                    "name":
                        customer.name,
                },
                "invoice_count":
                    item[
                        "invoice_count"
                    ],
                "total_outstanding":
                    str(
                        item[
                            "total_outstanding"
                        ]
                    ),
            }
        )

    return JsonResponse(
        {
            "invoice_count":
                result["invoice_count"],
            "customer_count":
                result["customer_count"],
            "total_outstanding":
                str(
                    result[
                        "total_outstanding"
                    ]
                ),
            "customers":
                customers,
        },
        status=200,
    )

def _payment_response(payment):
    allocations = []

    for allocation in payment.allocations:
        allocations.append(
            {
                "invoice": {
                    "id": str(
                        allocation.invoice.id
                    ),
                    "invoice_number":
                        allocation.invoice.invoice_number,
                },
                "amount": str(
                    allocation.amount
                ),
            }
        )

    return {
        "id": str(payment.id),
        "payment_number":
            payment.payment_number,

        "customer": {
            "id": str(
                payment.customer.id
            ),
            "code":
                payment.customer.code,
            "name":
                payment.customer.name,
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

        "allocations":
            allocations,

        "notes":
            payment.notes,

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

def payment_list(request):
    """
    GET  /sales/payments/
    POST /sales/payments/
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
            InvoiceService._check_permission(
                user,
                "invoices.read",
            )

            InvoiceService._check_organization(
                user,
                user.organization,
            )

            payments = (
                PaymentRepository
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
            _payment_response(payment)
            for payment in payments
        ]

        return JsonResponse(
            {
                "count": len(data),
                "payments": data,
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
                        "JSON body must be an object."
                },
                status=400,
            )

        invoice_id = data.get(
            "invoice_id"
        )

        if not invoice_id:
            return JsonResponse(
                {
                    "error":
                        "invoice_id is required."
                },
                status=400,
            )

        try:
            ObjectId(
                invoice_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            return JsonResponse(
                {
                    "error":
                        "Invalid invoice ID."
                },
                status=400,
            )

        invoice = Invoice.objects(
            organization=user.organization,
            id=invoice_id,
        ).first()

        if not invoice:
            return JsonResponse(
                {
                    "error":
                        "Invoice not found."
                },
                status=404,
            )

        payment_date = None

        try:
            if data.get(
                "payment_date"
            ):
                payment_date = (
                    _parse_datetime(
                        data.get(
                            "payment_date"
                        ),
                        "payment_date",
                        required=True,
                    )
                )

            payment = (
                PaymentService
                .record_invoice_payment(
                    user=user,
                    organization=user.organization,
                    invoice=invoice,
                    amount=data.get(
                        "amount"
                    ),
                    payment_method=data.get(
                        "payment_method",
                        "",
                    ),
                    payment_date=payment_date,
                    reference_number=data.get(
                        "reference_number",
                        "",
                    ),
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
                    "Payment recorded successfully.",
                "payment":
                    _payment_response(
                        payment
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

def payment_detail(
    request,
    payment_id,
):
    """
    GET /sales/payments/<id>/
    """

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
            payment_id
        )

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid payment ID."
            },
            status=400,
        )

    try:
        InvoiceService._check_permission(
            user,
            "invoices.read",
        )

        InvoiceService._check_organization(
            user,
            user.organization,
        )

        payment = (
            PaymentRepository.get_by_id(
                organization=user.organization,
                payment_id=payment_id,
            )
        )

        if not payment:
            return JsonResponse(
                {
                    "error":
                        "Payment not found."
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
        _payment_response(
            payment
        ),
        status=200,
    )

def invoice_payment_history(
    request,
    invoice_id,
):
    """
    GET /sales/invoices/<id>/payments/
    """

    if request.method != "GET":
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
        ObjectId(invoice_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {"error": "Invalid invoice ID."},
            status=400,
        )

    try:
        InvoiceService._check_permission(
            user,
            "invoices.read",
        )

        InvoiceService._check_organization(
            user,
            user.organization,
        )

        invoice = Invoice.objects(
            organization=user.organization,
            id=invoice_id,
        ).first()

        if not invoice:
            return JsonResponse(
                {"error": "Invoice not found."},
                status=404,
            )

        payments = (
            PaymentRepository.list_by_invoice(
                organization=user.organization,
                invoice=invoice,
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

    payment_data = [
        _payment_response(payment)
        for payment in payments
    ]

    return JsonResponse(
        {
            "invoice": {
                "id": str(invoice.id),
                "invoice_number":
                    invoice.invoice_number,
                "status":
                    invoice.status,
                "total_amount":
                    str(invoice.total_amount),
                "amount_paid":
                    str(invoice.amount_paid),
                "balance_due":
                    str(invoice.balance_due),
            },
            "payment_count":
                len(payment_data),
            "payments":
                payment_data,
        },
        status=200,
    )

def customer_payment_history(
    request,
    customer_id,
):
    """
    GET /sales/customers/<id>/payments/
    """

    if request.method != "GET":
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
        ObjectId(customer_id)

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {"error": "Invalid customer ID."},
            status=400,
        )

    try:
        InvoiceService._check_permission(
            user,
            "invoices.read",
        )

        InvoiceService._check_organization(
            user,
            user.organization,
        )

        customer = Customer.objects(
            organization=user.organization,
            id=customer_id,
        ).first()

        if not customer:
            return JsonResponse(
                {"error": "Customer not found."},
                status=404,
            )

        payments = (
            PaymentRepository.list_by_customer(
                organization=user.organization,
                customer=customer,
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

    payment_data = [
        _payment_response(payment)
        for payment in payments
    ]

    total_received = sum(
        (
            payment.amount
            for payment in payments
        ),
        Decimal("0"),
    )

    return JsonResponse(
        {
            "customer": {
                "id": str(customer.id),
                "code": customer.code,
                "name": customer.name,
            },
            "payment_count":
                len(payment_data),
            "total_received":
                str(total_received),
            "payments":
                payment_data,
        },
        status=200,
    )

def _sales_return_response(
    sales_return,
):
    return {
        "id": str(
            sales_return.id
        ),
        "return_number":
            sales_return.return_number,
        "status":
            sales_return.status,
        "sales_order": {
            "id": str(
                sales_return.sales_order.id
            ),
            "so_number":
                sales_return.sales_order.so_number,
        },
        "invoice": {
            "id": str(
                sales_return.invoice.id
            ),
            "invoice_number":
                sales_return.invoice.invoice_number,
        },
        "customer": {
            "id": str(
                sales_return.customer.id
            ),
            "code":
                sales_return.customer.code,
            "name":
                sales_return.customer.name,
        },
        "warehouse": {
            "id": str(
                sales_return.warehouse.id
            ),
            "code":
                sales_return.warehouse.code,
            "name":
                sales_return.warehouse.name,
        },
        "return_date": (
            sales_return.return_date.isoformat()
            if sales_return.return_date
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
                    str(item.line_subtotal),
                "line_tax":
                    str(item.line_tax),
                "line_total":
                    str(item.line_total),
                "reason":
                    item.reason,
            }
            for item
            in sales_return.items
        ],
        "subtotal":
            str(sales_return.subtotal),
        "tax_amount":
            str(sales_return.tax_amount),
        "discount_amount":
            str(
                sales_return.discount_amount
            ),
        "total_amount":
            str(sales_return.total_amount),
        "reason":
            sales_return.reason,
        "notes":
            sales_return.notes,
        "created_by": {
            "id": str(
                sales_return.created_by.id
            ),
            "email":
                sales_return.created_by.email,
        },
        "confirmed_at": (
            sales_return.confirmed_at.isoformat()
            if sales_return.confirmed_at
            else None
        ),
        "cancelled_at": (
            sales_return.cancelled_at.isoformat()
            if sales_return.cancelled_at
            else None
        ),
        "created_at": (
            sales_return.created_at.isoformat()
            if sales_return.created_at
            else None
        ),
        "updated_at": (
            sales_return.updated_at.isoformat()
            if sales_return.updated_at
            else None
        ),
    }

def sales_returns(
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
            SalesReturnService._check_permission(
                user,
                "sales_returns.read",
            )

            returns = (
                SalesReturnRepository
                .list_by_organization(
                    organization=organization,
                )
            )

            return JsonResponse(
                {
                    "count":
                        returns.count(),
                    "sales_returns": [
                        _sales_return_response(
                            item
                        )
                        for item
                        in returns
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

            invoice_id = payload.get(
                "invoice_id"
            )

            if not invoice_id:
                raise ValueError(
                    "invoice_id is required."
                )

            try:
                ObjectId(
                    invoice_id
                )

            except (
                InvalidId,
                TypeError,
            ):
                raise ValueError(
                    "Invalid invoice ID."
                )

            from apps.sales.models import (
                Invoice,
            )

            invoice = Invoice.objects(
                organization=organization,
                id=invoice_id,
            ).first()

            if not invoice:
                return JsonResponse(
                    {
                        "error":
                            "Invoice not found."
                    },
                    status=404,
                )

            raw_items = payload.get(
                "items"
            )

            if not isinstance(
                raw_items,
                list,
            ):
                raise ValueError(
                    "items must be a list."
                )

            service_items = []

            for item_data in raw_items:
                product_id = (
                    item_data.get(
                        "product_id"
                    )
                )

                if not product_id:
                    raise ValueError(
                        "product_id is required."
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
                            item_data.get(
                                "quantity"
                            ),
                        "reason":
                            item_data.get(
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

            sales_return = (
                SalesReturnService
                .create_return(
                    user=user,
                    organization=organization,
                    invoice=invoice,
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
                        "Sales return created "
                        "successfully.",
                    "sales_return":
                        _sales_return_response(
                            sales_return
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

def sales_return_detail(
    request,
    return_id,
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
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        SalesReturnService._check_permission(
            user,
            "sales_returns.read",
        )

        try:
            ObjectId(
                return_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid sales return ID."
            )

        sales_return = (
            SalesReturnRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                return_id=return_id,
            )
        )

        if not sales_return:
            return JsonResponse(
                {
                    "error":
                        "Sales return not found."
                },
                status=404,
            )

        return JsonResponse(
            {
                "sales_return":
                    _sales_return_response(
                        sales_return
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

def confirm_sales_return(
    request,
    return_id,
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
                return_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid sales return ID."
            )

        sales_return = (
            SalesReturnRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                return_id=return_id,
            )
        )

        if not sales_return:
            return JsonResponse(
                {
                    "error":
                        "Sales return not found."
                },
                status=404,
            )

        sales_return = (
            SalesReturnService
            .confirm_return(
                user=user,
                organization=(
                    user.organization
                ),
                sales_return=sales_return,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Sales return confirmed "
                    "successfully.",
                "sales_return":
                    _sales_return_response(
                        sales_return
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

def _credit_note_response(
    credit_note,
):
    return {
        "id": str(
            credit_note.id
        ),
        "credit_note_number":
            credit_note.credit_note_number,
        "status":
            credit_note.status,
        "invoice": {
            "id": str(
                credit_note.invoice.id
            ),
            "invoice_number":
                credit_note.invoice.invoice_number,
        },
        "sales_return": {
            "id": str(
                credit_note.sales_return.id
            ),
            "return_number":
                credit_note.sales_return.return_number,
        },
        "customer": {
            "id": str(
                credit_note.customer.id
            ),
            "code":
                credit_note.customer.code,
            "name":
                credit_note.customer.name,
        },
        "credit_note_date": (
            credit_note.credit_note_date.isoformat()
            if credit_note.credit_note_date
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
                    str(item.line_subtotal),
                "line_tax":
                    str(item.line_tax),
                "line_total":
                    str(item.line_total),
            }
            for item in credit_note.items
        ],
        "subtotal":
            str(credit_note.subtotal),
        "tax_amount":
            str(credit_note.tax_amount),
        "discount_amount":
            str(
                credit_note.discount_amount
            ),
        "total_amount":
            str(credit_note.total_amount),
        "applied_amount":
            str(credit_note.applied_amount),
        "remaining_credit":
            str(
                credit_note.remaining_credit
            ),
        "reason":
            credit_note.reason,
        "notes":
            credit_note.notes,
        "created_by": {
            "id": str(
                credit_note.created_by.id
            ),
            "email":
                credit_note.created_by.email,
        },
        "issued_at": (
            credit_note.issued_at.isoformat()
            if credit_note.issued_at
            else None
        ),
        "cancelled_at": (
            credit_note.cancelled_at.isoformat()
            if credit_note.cancelled_at
            else None
        ),
        "created_at": (
            credit_note.created_at.isoformat()
            if credit_note.created_at
            else None
        ),
    }

def credit_notes(
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
            CreditNoteService._check_permission(
                user,
                "credit_notes.read",
            )

            notes = (
                CreditNoteRepository
                .list_by_organization(
                    organization=organization,
                )
            )

            return JsonResponse(
                {
                    "count":
                        notes.count(),
                    "credit_notes": [
                        _credit_note_response(
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

            sales_return_id = (
                payload.get(
                    "sales_return_id"
                )
            )

            if not sales_return_id:
                raise ValueError(
                    "sales_return_id is required."
                )

            try:
                ObjectId(
                    sales_return_id
                )

            except (
                InvalidId,
                TypeError,
            ):
                raise ValueError(
                    "Invalid sales return ID."
                )

            sales_return = (
                SalesReturn.objects(
                    organization=organization,
                    id=sales_return_id,
                ).first()
            )

            if not sales_return:
                return JsonResponse(
                    {
                        "error":
                            "Sales return not found."
                    },
                    status=404,
                )

            credit_note_date = (
                payload.get(
                    "credit_note_date"
                )
            )

            if credit_note_date:
                try:
                    credit_note_date = (
                        datetime.fromisoformat(
                            credit_note_date
                        )
                    )

                except ValueError:
                    raise ValueError(
                        "Invalid credit_note_date."
                    )

            credit_note = (
                CreditNoteService
                .create_from_sales_return(
                    user=user,
                    organization=organization,
                    sales_return=sales_return,
                    credit_note_date=(
                        credit_note_date
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
                        "Credit note created "
                        "successfully.",
                    "credit_note":
                        _credit_note_response(
                            credit_note
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


def credit_note_detail(
    request,
    credit_note_id,
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
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        CreditNoteService._check_permission(
            user,
            "credit_notes.read",
        )

        try:
            ObjectId(
                credit_note_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid credit note ID."
            )

        credit_note = (
            CreditNoteRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                credit_note_id=(
                    credit_note_id
                ),
            )
        )

        if not credit_note:
            return JsonResponse(
                {
                    "error":
                        "Credit note not found."
                },
                status=404,
            )

        return JsonResponse(
            {
                "credit_note":
                    _credit_note_response(
                        credit_note
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

def issue_credit_note(
    request,
    credit_note_id,
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
                credit_note_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid credit note ID."
            )

        credit_note = (
            CreditNoteRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                credit_note_id=(
                    credit_note_id
                ),
            )
        )

        if not credit_note:
            return JsonResponse(
                {
                    "error":
                        "Credit note not found."
                },
                status=404,
            )

        credit_note = (
            CreditNoteService
            .issue_credit_note(
                user=user,
                organization=(
                    user.organization
                ),
                credit_note=credit_note,
            )
        )

        net_receivable = (
            CreditNoteService
            .get_invoice_net_receivable(
                organization=(
                    user.organization
                ),
                invoice=(
                    credit_note.invoice
                ),
            )
        )

        return JsonResponse(
            {
                "message":
                    "Credit note issued "
                    "successfully.",
                "credit_note":
                    _credit_note_response(
                        credit_note
                    ),
                "invoice_net_receivable":
                    str(net_receivable),
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

def cancel_credit_note(
    request,
    credit_note_id,
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
                credit_note_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid credit note ID."
            )

        credit_note = (
            CreditNoteRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                credit_note_id=(
                    credit_note_id
                ),
            )
        )

        if not credit_note:
            return JsonResponse(
                {
                    "error":
                        "Credit note not found."
                },
                status=404,
            )

        credit_note = (
            CreditNoteService
            .cancel_credit_note(
                user=user,
                organization=(
                    user.organization
                ),
                credit_note=credit_note,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Credit note cancelled "
                    "successfully.",
                "credit_note":
                    _credit_note_response(
                        credit_note
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

def invoice_pdf(
    request,
    invoice_id,
):
    user = request.user

    # ==================================================
    # METHOD PROTECTION
    # ==================================================

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    # ==================================================
    # AUTHENTICATION + ACTIVE USER + PERMISSION
    # ==================================================

    try:

        PDFSecurity.require_permission(
            user=user,
            permission_code="invoices.read",
        )

    except PermissionError as exc:

        message = str(
            exc
        )

        status_code = (
            401
            if message == "Not authenticated."
            else 403
        )

        return JsonResponse(
            {
                "error":
                    message
            },
            status=status_code,
        )

    # ==================================================
    # ORGANIZATION
    # ==================================================

    organization = (
        user.organization
    )

    # ==================================================
    # INVOICE LOOKUP + PDF GENERATION
    # ==================================================

    try:

        # ----------------------------------------------
        # Validate ObjectId
        # ----------------------------------------------

        try:

            ObjectId(
                invoice_id
            )

        except (
            InvalidId,
            TypeError,
        ):

            raise ValueError(
                "Invalid invoice ID."
            )

        # ----------------------------------------------
        # Tenant-scoped invoice lookup
        # ----------------------------------------------

        invoice = (
            InvoiceRepository
            .get_by_id(
                organization=organization,
                invoice_id=invoice_id,
            )
        )

        if not invoice:

            return JsonResponse(
                {
                    "error":
                        "Invoice not found."
                },
                status=404,
            )

        # ----------------------------------------------
        # Generate PDF
        # ----------------------------------------------

        pdf_bytes = (
            InvoicePDF.generate(
                invoice=invoice,
            )
        )
        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type="INVOICE",
            document_id=invoice.id,
            document_number=invoice.invoice_number,
        )
        filename = (
            f"{invoice.invoice_number}.pdf"
        )

        # ----------------------------------------------
        # PDF response
        # ----------------------------------------------

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
            len(
                pdf_bytes
            )
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

def sales_order_pdf(
    request,
    sales_order_id,
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
            permission_code="sales_orders.read",
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
                "error":
                    message
            },
            status=status_code,
        )

    organization = (
        user.organization
    )

    try:
        try:
            ObjectId(
                sales_order_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid sales order ID."
            )

        sales_order = (
            SalesOrderRepository
            .get_by_id(
                organization=organization,
                sales_order_id=sales_order_id,
            )
        )

        if not sales_order:
            return JsonResponse(
                {
                    "error":
                        "Sales order not found."
                },
                status=404,
            )

        pdf_bytes = (
            SalesOrderPDF.generate(
                sales_order=sales_order,
            )
        )
        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type="SALES_ORDER",
            document_id=sales_order.id,
            document_number=sales_order.so_number,
        )
        filename = (
            f"{sales_order.so_number}.pdf"
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

def credit_note_pdf(
    request,
    credit_note_id,
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
            permission_code="credit_notes.read",
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
                "error":
                    message
            },
            status=status_code,
        )

    organization = (
        user.organization
    )

    try:
        try:
            ObjectId(
                credit_note_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid credit note ID."
            )

        credit_note = (
            CreditNoteRepository
            .get_by_id(
                organization=organization,
                credit_note_id=credit_note_id,
            )
        )

        if not credit_note:
            return JsonResponse(
                {
                    "error":
                        "Credit note not found."
                },
                status=404,
            )

        pdf_bytes = (
            CreditNotePDF.generate(
                credit_note=credit_note,
            )
        )
        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type="CREDIT_NOTE",
            document_id=credit_note.id,
            document_number=credit_note.credit_note_number,
        )

        filename = (
            f"{credit_note.credit_note_number}.pdf"
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

def customer_payment_pdf(
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
            permission_code="customer_payments.read",
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
                "error":
                    message
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
                "Invalid customer payment ID."
            )

        payment = (
            PaymentRepository
            .get_by_id(
                organization=organization,
                payment_id=payment_id,
            )
        )

        if not payment:
            return JsonResponse(
                {
                    "error":
                        "Customer payment not found."
                },
                status=404,
            )

        pdf_bytes = (
            CustomerPaymentReceiptPDF
            .generate(
                payment=payment,
            )
        )
        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type="CUSTOMER_PAYMENT",
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

def invoice_email(
    request,
    invoice_id,
):
    return (
        DocumentEmailAPIService
        .handle(
            request=request,
            document_type="INVOICE",
            document_id=invoice_id,
        )
    )

def sales_order_email(
    request,
    sales_order_id,
):
    return (
        DocumentEmailAPIService
        .handle(
            request=request,
            document_type="SALES_ORDER",
            document_id=sales_order_id,
        )
    )


def credit_note_email(
    request,
    credit_note_id,
):
    return (
        DocumentEmailAPIService
        .handle(
            request=request,
            document_type="CREDIT_NOTE",
            document_id=credit_note_id,
        )
    )


def customer_payment_email(
    request,
    payment_id,
):
    return (
        DocumentEmailAPIService
        .handle(
            request=request,
            document_type="CUSTOMER_PAYMENT",
            document_id=payment_id,
        )
    )

