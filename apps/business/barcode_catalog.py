"""Read-only catalogue/export plus explicit backfill for older empty barcodes."""
from datetime import datetime
from io import BytesIO
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from mongoengine.queryset.visitor import Q
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.products.models import Product
from .views import permitted, audit


def _rows(request):
    rows = Product.objects(organization=request.api_organization).order_by('name', 'id')
    query = request.GET.get('q', '').strip()[:100]
    if query:
        rows = rows.filter(Q(name__icontains=query) | Q(sku__icontains=query) | Q(barcode__icontains=query))
    return rows


@api_login_required
@require_http_methods(['GET'])
def catalog(request):
    if not permitted(request, 'products.read'):
        return R.forbidden(message='Product read permission required.', request=request)
    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            raise ValueError()
    except ValueError:
        return R.validation_error(message='Page must be a positive integer.', request=request)
    rows = _rows(request)
    return R.success(data={'total':rows.count(), 'page':page, 'page_size':50,
        'can_generate':permitted(request,'products.update'),
        'results':[{'id':str(p.id), 'name':p.name, 'sku':p.sku, 'barcode':p.barcode or '',
                    'item_type':p.item_type, 'is_active':p.is_active}
                   for p in rows.skip((page-1)*50).limit(50)]}, request=request)


@api_login_required
@require_http_methods(['GET'])
def export_catalog(request):
    if not permitted(request, 'products.read'):
        return R.forbidden(message='Product read permission required.', request=request)
    from openpyxl import Workbook
    from openpyxl.cell import WriteOnlyCell
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet('Barcodes')
    sheet.append(['SKU', 'Product / service', 'Barcode number', 'Type', 'Status'])
    # Force text to preserve leading zeroes and prevent spreadsheet formulas.
    for product in _rows(request).no_cache():
        values = [product.sku, product.name, product.barcode or '', product.item_type,
                  'Active' if product.is_active else 'Inactive']
        cells=[]
        for value in values:
            cell=WriteOnlyCell(sheet,value=str(value));cell.data_type='s';cells.append(cell)
        sheet.append(cells)
    output=BytesIO();workbook.save(output)
    response=HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition']='attachment; filename="NexEase-Barcode-List.xlsx"'
    response['Cache-Control']='no-store'
    return response


@api_login_required
@require_http_methods(['POST'])
def generate_missing(request):
    if not permitted(request, 'products.update'):
        return R.forbidden(message='Product update permission required.', request=request)
    updated=0
    for product in Product.objects(Q(barcode='') | Q(barcode=None), organization=request.api_organization).only('id'):
        # Compare-and-set so a concurrently scanned supplier code is never overwritten.
        updated += Product.objects(Q(barcode='') | Q(barcode=None), id=product.id,
            organization=request.api_organization).update_one(
                set__barcode=Product.automatic_barcode(product.id), set__updated_at=datetime.utcnow())
    audit(request,'products','barcode-catalog',f'Generated {updated} missing barcodes')
    return R.success(data={'updated':updated}, message=f'Generated barcodes for {updated} items.', request=request)
