"""Invoice page KPIs without loading inventory, purchasing, charts or activity."""
from django.views.decorators.http import require_GET
from apps.core.api.decorators import api_login_required, api_rate_limit
from apps.authorization.services import AuthorizationService
from apps.core.services.api_response_service import APIResponseService as R
from apps.sales.services.customer_payment_api_service import CustomerPaymentAPIService
from apps.finance.services.main_dashboard_service import MainDashboardService


@api_login_required
@api_rate_limit(scope='invoice_overview.read', limit=120, window_seconds=60)
@require_GET
def invoice_overview(request):
    # Preserve the dashboard report permission used by these KPIs previously.
    if not AuthorizationService.has_permission(request.api_user, 'accounting_reports.read'):
        return R.forbidden(message='Permission denied.', request=request)
    organization = request.api_organization
    summary = CustomerPaymentAPIService.get_receivable_summary(organization=organization)
    period = MainDashboardService._normalize_period()
    sales = MainDashboardService._get_total_sales(organization=organization, period=period)
    return R.success(data={
        'kpis': {'receivables': summary['total_outstanding'], 'total_sales': f'{sales:.2f}'},
        'alerts': {'overdue_invoices': summary['overdue_invoice_count']},
    }, request=request)
