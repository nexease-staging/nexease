"""Link reviewed drafts to a tenant's quotation through the normal creation endpoints."""
import base64
import json
from decimal import Decimal
from functools import wraps
from io import BytesIO
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.views.decorators.http import require_GET
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .models import BusinessRecord


def quotation_conversion(kind):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            number = request.GET.get("quotation")
            if request.method != "POST" or not number:
                return view(request, *args, **kwargs)
            from .views import permitted
            permission = "invoices.create" if kind == "invoice" else "sales_orders.create"
            if not all(permitted(request, p) for p in ("invoices.read", permission)):
                return R.forbidden(message="Quotation or creation permission required.", request=request)
            records = BusinessRecord.objects(organization=request.api_organization, kind="quotation", key=number)
            if not records.first():
                return R.not_found(message="Quotation not found.", request=request)
            # One atomic claim across both creation paths. An order can be invoiced through fulfilment.
            claimed = records.filter(data__conversion__exists=False).update_one(
                set__data__conversion={"kind":kind,"status":"processing"})
            if not claimed:
                return R.error(code="QUOTATION_CONVERSION",message="Refresh the quotation to view its conversion status.",status=409,request=request)
            response = view(request, *args, **kwargs)
            if response.status_code < 300:
                data = json.loads(response.content)["data"]
                doc = data["sales_order"] if kind == "order" else data
                records.update_one(set__data__conversion={"kind":kind,"status":"created","id":doc["id"],
                    "number":doc["so_number" if kind=="order" else "invoice_number"]})
            elif response.status_code in (400,403,404,422,429):
                records.update_one(unset__data__conversion=1)
            return response
        return wrapped
    return decorate


@api_login_required
@require_GET
def quotation_pdf(request, number):
    from .billing import settings
    from .print_documents import document_styles
    from .views import permitted
    if not permitted(request,"invoices.read"):
        return R.forbidden(message="Sales read permission required.",request=request)
    org = request.api_organization
    record = BusinessRecord.objects(organization=org,kind="quotation",key=number).first()
    if not record:
        return R.not_found(message="Quotation not found.",request=request)
    data = record.data
    styles = document_styles()
    def paragraph(value, style="Normal"):
        return Paragraph(escape(str(value)).replace("\n","<br/>"),styles[style])
    story = []
    logo = settings(org).get("logo")
    if logo:
        image = Image(BytesIO(base64.b64decode(logo.split(",",1)[-1])))
        image._restrictSize(110,48)
        image.hAlign = "LEFT"
        story.append(image)
    story.extend([paragraph(org.name,"Title"),paragraph("Quotation "+record.key,"Heading2"),
        paragraph("Prepared for "+data["customer"]),paragraph("Date "+data["date"])])
    if data.get("valid_until"):
        story.append(paragraph("Valid until "+data["valid_until"]))
    rows = [["Item","Qty","Rate ₹","Discount ₹","GST %","Total ₹"]]
    tax_total = Decimal(0)
    discount_total = Decimal(0)
    from .payroll import money
    for item in data["items"]:
        subtotal = Decimal(money(Decimal(item["quantity"]) * Decimal(item["unit_price"])))
        discount = Decimal(item["discount"])
        discount_total += discount
        tax_total += Decimal(item["total"]) - subtotal + discount
        rows.append([item[k] for k in ("name","quantity","unit_price","discount","tax_rate","total")])
    story.extend([Spacer(1,12),Table([[paragraph(v) for v in row] for row in rows],
        colWidths=[135,38,70,72,46,75],repeatRows=1),
        paragraph("Discount ₹"+money(discount_total)), paragraph("GST ₹"+money(tax_total)),
        paragraph("Quotation total ₹"+data["total"],"Heading2"),paragraph(data.get("notes",""))])
    output = BytesIO()
    SimpleDocTemplate(output,title="Quotation "+number).build(story)
    response = HttpResponse(output.getvalue(),content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{record.key}.pdf"'
    response["Cache-Control"] = "private, no-store"
    return response
