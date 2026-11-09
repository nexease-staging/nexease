"""Per-product reorder levels and one bell alert per low-stock episode/user."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError, NotUniqueError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.products.models import Product
from apps.inventory.models import Inventory
from .models import BusinessRecord as Record
from .views import payload, permitted, audit


def stock_total(org, product):
    return sum(
        (i.quantity for i in Inventory.objects(organization=org, product=product)),
        Decimal(0),
    )


@api_login_required
@require_http_methods(["GET", "POST"])
def rule(request, product_id):
    if not permitted(request, "inventory.read"):
        return R.forbidden(
            message="Inventory read permission required.", request=request
        )
    try:
        org = request.api_organization
        product = Product.objects(
            organization=org, id=product_id, is_active=True, item_type="goods"
        ).first()
        if not product:
            raise ValueError("Select an active goods product.")
        record = Record.objects(
            organization=org, kind="reorder_rule", key=str(product.id)
        ).first()
        if request.method == "POST":
            if not permitted(request, "products.update"):
                return R.forbidden(
                    message="Product update permission required.", request=request
                )
            raw = payload(request)
            value = Decimal(str(raw.get("level", "")))
            if (
                not value.is_finite()
                or value < 0
                or value != value.quantize(Decimal(".01"))
            ):
                raise ValueError(
                    "Enter a non-negative reorder level with up to two decimal places."
                )
            enabled = raw.get("enabled", True)
            if not isinstance(enabled, bool):
                raise ValueError("Enabled must be true or false.")
            Record.objects(
                organization=org, kind="reorder_rule", key=str(product.id)
            ).update_one(
                upsert=True,
                set__data={"level": str(value), "enabled": enabled},
                set__created_by=request.api_user,
                inc__revision=1,
            )
            audit(request, "reorder_rule", product.id, "update")
            record = Record.objects(
                organization=org, kind="reorder_rule", key=str(product.id)
            ).first()
        return R.success(
            data={
                "product_id": str(product.id),
                "product_name": product.name,
                "quantity": str(stock_total(org, product)),
                "level": record.data["level"] if record else "0",
                "enabled": record.data.get("enabled", True) if record else False,
            },
            request=request,
        )
    except (ValueError, TypeError, InvalidOperation, ValidationError) as e:
        return R.validation_error(message=str(e), request=request)


def scan(user):
    from apps.authorization.services import AuthorizationService
    from apps.core.services.notification_service import NotificationService

    if (
        not user
        or not user.is_active
        or not AuthorizationService.has_permission(user, "inventory.read")
    ):
        return
    org = user.organization
    rules = list(
        Record.objects(organization=org, kind="reorder_rule", data__enabled=True)
    )
    if not rules:
        return
    products = {
        str(p.id): p
        for p in Product.objects(
            organization=org, id__in=[r.key for r in rules], is_active=True
        )
    }
    totals = {}
    for stock in (
        Inventory.objects(organization=org, product__in=list(products.values()))
        .no_dereference()
        .only("product", "quantity")
    ):
        key = str(stock.product.id)
        totals[key] = totals.get(key, Decimal(0)) + stock.quantity
    for rule in rules:
        product = products.get(rule.key)
        if not product:
            continue
        quantity = totals.get(rule.key, Decimal(0))
        low = quantity < Decimal(rule.data["level"])
        key = str(user.id) + ":" + rule.key
        try:
            Record(
                organization=org,
                kind="reorder_alert_state",
                key=key,
                data={"low": False},
                created_by=user,
            ).save(force_insert=True)
        except NotUniqueError:
            pass
        if not low:
            Record.objects(
                organization=org, kind="reorder_alert_state", key=key
            ).update_one(set__data__low=False)
        else:
            state = Record.objects(
                organization=org, kind="reorder_alert_state", key=key, data__low=False
            ).modify(new=True, set__data__low=True, inc__revision=1)
            if not state:
                continue
            try:
                NotificationService.create_notification(
                    organization=org,
                    recipient=user,
                    notification_type="SYSTEM",
                    title=("Reorder: " + product.name)[:200],
                    message=f'{product.name}: quantity {quantity} {product.unit} is below reorder level {rule.data["level"]}.',
                    severity="WARNING",
                    resource_type="product",
                    resource_id=str(product.id),
                    action_url="/inventory",
                    background_job_key=f"reorder:{key}:{state.revision}",
                )
            except Exception:
                Record.objects(id=state.id, revision=state.revision).update_one(
                    set__data__low=False
                )
                raise


@api_login_required
@require_http_methods(["GET"])
def balances(request):
    if not permitted(request, "inventory.read"):
        return R.forbidden(
            message="Inventory read permission required.", request=request
        )
    try:
        ids = request.GET.get("product_ids", "").split(",")
        if not 1 <= len(ids) <= 100 or any(not value for value in ids):
            raise ValueError("Select 1–100 products.")
        products = list(
            Product.objects(organization=request.api_organization, id__in=ids)
        )
        result = {str(p.id): Decimal(0) for p in products}
        for row in (
            Inventory.objects(
                organization=request.api_organization, product__in=products
            )
            .no_dereference()
            .only("product", "quantity")
        ):
            pid = str(row.product.id)
            result[pid] += row.quantity
        return R.success(
            data={"quantities": {pid: str(value) for pid, value in result.items()}},
            request=request,
        )
    except (ValueError, ValidationError) as e:
        return R.validation_error(message=str(e), request=request)
