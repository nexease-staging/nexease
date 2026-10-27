import json
from bson import ObjectId
from bson.errors import InvalidId
from django.http import JsonResponse
from mongoengine.errors import ValidationError

from apps.products.models import Product
from apps.products.services.product_service import ProductService

def product_list(request):
    """
    Return all products belonging to the
    authenticated user's organization.
    """

    if request.method == "POST":
        return product_create(request)


    if request.method != "GET":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        search_term = request.GET.get("search")

        active_only = (
            request.GET.get("active") == "true"
        )

        products = ProductService.list_products(
            user=user,
            organization=user.organization,
            search_term=search_term,
            active_only=active_only,
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

    data = []

    for product in products:
        data.append(
            {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "description": product.description,
                "brand": product.brand,
                "unit": product.unit,
                "cost_price": str(
                    product.cost_price
                ),
                "selling_price": str(
                    product.selling_price
                ),
                "barcode": product.barcode,
                "is_active": product.is_active,
                "category": {
                    "id": str(
                        product.category.id
                    ),
                    "name": product.category.name,
                },
            }
        )

    return JsonResponse(
        {
            "count": len(data),
            "products": data,
        },
        status=200,
    )

def product_search(request):
    """
    Search products by SKU or product name.
    """

    if request.method != "GET":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    search_term = request.GET.get(
        "q",
        ""
    ).strip()

    if not search_term:
        return JsonResponse(
            {
                "error": "Search term is required."
            },
            status=400,
        )

    try:
        products = ProductService.search_products(
            user=user,
            organization=user.organization,
            search_term=search_term,
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

    data = []

    for product in products:
        data.append(
            {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "unit": product.unit,
                "cost_price": str(
                    product.cost_price
                ),
                "selling_price": str(
                    product.selling_price
                ),
                "is_active": product.is_active,
            }
        )

    return JsonResponse(
        {
            "count": len(data),
            "products": data,
        },
        status=200,
    )

def product_detail(request, product_id):
    """
    Retrieve or update a product belonging to the
    authenticated user's organization.
    """

    if request.method not in ["GET", "PUT"]:
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(product_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid product ID."
            },
            status=400,
        )

    # -------------------------------------------------
    # GET PRODUCT
    # -------------------------------------------------

    if request.method == "GET":

        try:
            product = ProductService.get_product(
                user=user,
                organization=user.organization,
                product_id=product_id,
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
                status=404,
            )

        return JsonResponse(
            {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "description": product.description,
                "brand": product.brand,
                "unit": product.unit,
                "cost_price": str(
                    product.cost_price
                ),
                "selling_price": str(
                    product.selling_price
                ),
                "barcode": product.barcode,
                "is_active": product.is_active,
                "category": {
                    "id": str(
                        product.category.id
                    ),
                    "name": product.category.name,
                },
            },
            status=200,
        )

    # -------------------------------------------------
    # PUT / UPDATE PRODUCT
    # -------------------------------------------------

    try:
        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error": "Invalid JSON."
            },
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {
                "error": "JSON body must be an object."
            },
            status=400,
        )

    category = None

    if "category_id" in data:

        category_id = data.get(
            "category_id"
        )

        try:
            ObjectId(category_id)

        except (InvalidId, TypeError):
            return JsonResponse(
                {
                    "error": "Invalid category ID."
                },
                status=400,
            )

        from apps.products.models import Category

        category = Category.objects(
            id=category_id,
            organization=user.organization,
        ).first()

        if not category:
            return JsonResponse(
                {
                    "error": "Category not found."
                },
                status=404,
            )

    try:

        product = ProductService.update_product(
            user=user,
            organization=user.organization,
            product_id=product_id,

            name=data.get(
                "name"
            ),

            description=data.get(
                "description"
            ),

            category=category,

            brand=data.get(
                "brand"
            ),

            unit=data.get(
                "unit"
            ),

            cost_price=data.get(
                "cost_price"
            ),

            selling_price=data.get(
                "selling_price"
            ),

            barcode=data.get(
                "barcode"
            ),
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
            "message": "Product updated successfully.",
            "product": {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "description": product.description,
                "brand": product.brand,
                "unit": product.unit,
                "cost_price": str(
                    product.cost_price
                ),
                "selling_price": str(
                    product.selling_price
                ),
                "barcode": product.barcode,
                "is_active": product.is_active,
                "category": {
                    "id": str(
                        product.category.id
                    ),
                    "name": product.category.name,
                },
            },
        },
        status=200,
    )

def product_create(request):
    """
    Create a new product for the authenticated
    user's organization.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        data = json.loads(
            request.body
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error": "Invalid JSON."
            },
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {
                "error": "JSON body must be an object."
            },
            status=400,
        )

    required_fields = [
        "sku",
        "name",
        "category_id",
        "unit",
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

    category_id = data.get(
        "category_id"
    )

    try:
        ObjectId(category_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid category ID."
            },
            status=400,
        )

    from apps.products.models import Category

    category = Category.objects(
        id=category_id,
        organization=user.organization,
    ).first()

    if not category:
        return JsonResponse(
            {
                "error": "Category not found."
            },
            status=404,
        )

    try:
        product = ProductService.create_product(
            user=user,
            organization=user.organization,
            sku=data.get("sku"),
            name=data.get("name"),
            category=category,
            unit=data.get("unit"),
            cost_price=data.get(
                "cost_price",
                0,
            ),
            selling_price=data.get(
                "selling_price",
                0,
            ),
            description=data.get(
                "description",
                "",
            ),
            brand=data.get(
                "brand",
                "",
            ),
            barcode=data.get(
                "barcode",
                "",
            ),
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
            "message": "Product created successfully.",
            "product": {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "description": product.description,
                "brand": product.brand,
                "unit": product.unit,
                "cost_price": str(
                    product.cost_price
                ),
                "selling_price": str(
                    product.selling_price
                ),
                "barcode": product.barcode,
                "is_active": product.is_active,
                "category": {
                    "id": str(
                        product.category.id
                    ),
                    "name": product.category.name,
                },
            },
        },
        status=201,
    )

def product_deactivate(request, product_id):
    """
    Deactivate a product without deleting it.
    """

    if request.method != "PUT":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(product_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid product ID."
            },
            status=400,
        )

    try:
        product = ProductService.deactivate_product(
            user=user,
            organization=user.organization,
            product_id=product_id,
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
            "message": "Product deactivated successfully.",
            "product": {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "is_active": product.is_active,
            },
        },
        status=200,
    )

def product_activate(request, product_id):
    """
    Reactivate an inactive product.
    """

    if request.method != "PUT":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(product_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid product ID."
            },
            status=400,
        )

    if not user.organization:
        return JsonResponse(
            {
                "error": "User has no organization."
            },
            status=400,
        )

    try:
        product = ProductService.activate_product(
            user=user,
            organization=user.organization,
            product_id=product_id,
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
            "message": "Product activated successfully.",
            "product": {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "is_active": product.is_active,
            },
        },
        status=200,
    )