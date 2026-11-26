"""Setup checklist: what is still missing before the business runs smoothly in NexEase.

GET /api/v1/business/setup-status/

Each item is a yes/no fact the server can check, with the page that fixes it. Counts use
indexed organisation filters and stop at the first match, so the call stays cheap.
"""

from django.views.decorators.http import require_GET

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R

from .models import BusinessRecord as Record


def exists(queryset):
    return queryset.limit(1).count(with_limit_and_skip=True) > 0


def checks(request):
    from apps.accounts.models import User
    from apps.core.services.user_mailbox_service import get_mailbox
    from apps.finance.models import BankAccount
    from apps.inventory.models import Inventory
    from apps.products.models import Product
    from apps.sales.models import Customer, Invoice
    from .billing import settings as invoice_settings

    org, user = request.api_organization, request.api_user
    document = invoice_settings(org)
    mailbox = get_mailbox(user, org)
    has_goods = exists(Product.objects(organization=org, is_active=True, item_type="goods"))
    gst = Record.objects(organization=org, kind="gst_settings").first()
    return [
        ("profile", "Business profile", "Name, phone, email and address on invoices and payslips.", "/settings/organization",
         all(str(getattr(org, f, "") or "").strip() for f in ("name", "phone", "email", "address"))),
        ("gst", "GST registration", "Your GSTIN and return frequency, for correct tax on invoices.", "/taxation",
         bool(gst and str(gst.data.get("gstin") or "").strip()) or (gst is not None and gst.data.get("registration") == "unregistered")),
        ("logo", "Logo on invoices", "Upload your logo so invoices look like yours.", "/settings/invoices",
         bool(str(document.get("logo") or "").strip())),
        ("bank_details", "Bank details on invoices", "Account number and IFSC printed for customers to pay.", "/settings/invoices",
         bool(str(document.get("bank_details") or "").strip())),
        ("email", "Email sending", "Connect your mailbox to email invoices and payslips.", "/settings#email",
         bool(mailbox and mailbox.get("email") == user.email.strip().lower())),
        ("bank_account", "Bank or cash account", "Where payments are received and paid from.", "/banking",
         exists(BankAccount.objects(organization=org, is_active=True))),
        ("products", "Items", "Add the goods and services you sell or buy.", "/products",
         exists(Product.objects(organization=org, is_active=True))),
        ("customers", "Customers", "Add customers so invoices fill their details automatically.", "/customers",
         exists(Customer.objects(organization=org))),
        ("opening_stock", "Opening stock", "Enter the stock you have today, so stock levels are right.", "/inventory",
         (not has_goods) or exists(Inventory.objects(organization=org, quantity__gt=0))),
        ("first_invoice", "First invoice", "Issue your first invoice.", "/invoices",
         exists(Invoice.objects(organization=org, status__ne="DRAFT"))),
        ("team", "Invite your team", "Give staff their own login with the right role.", "/settings/users",
         User.objects(organization=org, is_active=True).limit(2).count(with_limit_and_skip=True) > 1),
    ]


@api_login_required
@require_GET
def setup_status(request):
    items = []
    for key, title, description, href, done in checks(request):
        items.append({"key": key, "title": title, "description": description, "href": href, "done": bool(done)})
    done = sum(1 for i in items if i["done"])
    return R.success(data={"items": items, "done": done, "total": len(items),
                           "percent": round(done * 100 / len(items)) if items else 100}, request=request)
