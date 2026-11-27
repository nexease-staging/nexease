from .invoice_edit import edit as edit_invoice
from .payslip_distribution import distribute as distribute_payslips
from .reorder import rule as reorder_rule, balances as product_stock_balances
from .ewaybill import eway_bills
from .einvoice import einvoices, einvoice_pdf
from .delivery_challan import challans
from . import upgrade_api
from . import gst_lookup
from . import enhancements, barcode_catalog
from . import workforce
from . import billing
from .purchase_entry import quick_purchase
from .taxation import gst_report
from . import gst_compliance
from .direct_entry import direct_invoice
from . import inventory_insights
from . import payments_hub
from . import mobile_home
from . import report_engine
from . import finance_hub
from . import tally_api
from . import share_center
from . import mobile_app
from . import tally_signals  # noqa: F401  (keeps updated_at current for Tally sync)
from . import workforce_approvals
from .setup_status import setup_status
from django.urls import path
from . import views, flow_api, pro_api
from .gst_review_sources import review_sources
from .hsn_suggestions import suggestions as hsn_suggestions

urlpatterns=[path("stock-balances/",product_stock_balances),path("invoices/<str:invoice_id>/edit/",edit_invoice),path("workforce/payslip-distribution/<str:run_id>/",distribute_payslips),path("reorder/<str:product_id>/",reorder_rule),path("hsn-suggestions/",hsn_suggestions),path("gst/review-sources/",review_sources),path("employee-payables/",upgrade_api.employee_payables),path("worker-health/",upgrade_api.worker_health),path("barcode/catalog/",barcode_catalog.catalog),path("barcode/export/",barcode_catalog.export_catalog),path("barcode/generate-missing/",barcode_catalog.generate_missing),path("gst-lookup/",gst_lookup.lookup),path("invoices/zip/",enhancements.invoice_zip),path("workforce/populate-inputs/",enhancements.populate_inputs),path("barcode/lookup/",enhancements.barcode_lookup),path("barcode/labels/",enhancements.barcode_labels),path("workforce/overview/",workforce.overview),path("workforce/approvals/",workforce_approvals.approvals),path("workforce/reports/<str:kind>/",workforce.report),path("workforce/payslips/<str:run_id>/",workforce.payslips),path("invoice-settings/",billing.invoice_settings),path("invoices/<str:invoice_id>/details/",billing.invoice_details),path("expenses-export/",pro_api.expenses_export),path("lookup/",pro_api.lookup),path("modules/",pro_api.modules),path("payment-accounts/",pro_api.payment_accounts),path("bulk-assign/",pro_api.bulk_assign),path("books-sync/",pro_api.books_sync),path("accountant-export/",pro_api.accountant_export),path("invoices/<str:invoice_id>/descriptions/",pro_api.invoice_descriptions),path("numbers/",flow_api.numbers),path("client-lookup/",flow_api.clients),path("daily-work/",flow_api.daily_work),path("balances/",flow_api.balances),path("labour-invoice/",flow_api.labour_invoice),path("workers/",views.worker_lookup),path("labour/export/",views.labour_export),path("quick-purchases/",quick_purchase),path("gst/export/",gst_report),path("direct-invoices/",direct_invoice),path("inventory-insights/",inventory_insights.insights),path("reports/run/",report_engine.run_report),path("setup-status/",setup_status),path("mobile/home/",mobile_home.home),path("mobile/parties/",mobile_home.parties),path("payments/register/",payments_hub.register),path("payments/outstanding/",payments_hub.outstanding),path("payments/receive/",payments_hub.receive),path("payments/pay/",payments_hub.pay),path('configuration/',views.configuration),path('records/<str:kind>/',views.records),path('records/<str:kind>/<str:record_id>/',views.records),path('payroll/',views.payroll),path('payroll/<str:run_id>/export/',views.payroll_export)]

from .mobile_insights import insights
from .manufacturing import orders as manufacturing_orders
from . import jobs, recipes
from .quotation_actions import quotation_pdf
from .quotations import quotations
from .sales_reports import report as sales_report

urlpatterns[:0] = [
    path("bank-statements/insights/", insights, {"section": "banking"}),
    path("workforce/insights/", insights, {"section": "workforce"}),
    path("sales/insights/", insights, {"section": "sales"}),
    path("purchase/insights/", insights, {"section": "purchase"}),
    path("collections/insights/", insights, {"section": "collections"}),
    path("finance/overview/", finance_hub.overview),
    path("finance/statements/<str:kind>/", finance_hub.statement),
    path("manufacturing/insights/", insights, {"section": "production"}),
    path("manufacturing/", manufacturing_orders),
    path("manufacturing/<str:order_id>/", manufacturing_orders),
    path("quotations/<slug:number>/pdf/", quotation_pdf),
    path("invoice-templates/preview/", billing.template_preview),
    path("quotations/", quotations),
    path("sales-reports/", sales_report),
    path("e-way-bills/", eway_bills),
    path("e-invoices/", einvoices),
    # GST compliance: IMS inbox, GSTR-2B reconciliation, GSTR-1 / GSTR-3B
    path("gst/overview/", gst_compliance.overview),
    path("gst/ims/", gst_compliance.ims),
    path("gst/ims/action/", gst_compliance.ims_action),
    path("gst/ims/link/", gst_compliance.link_bill),
    path("gst/ims/template/", gst_compliance.template),
    path("gst/returns/<str:form>/", gst_compliance.returns),
    path("e-invoices/<str:invoice_id>/pdf/", einvoice_pdf),
    path("delivery-challans/", challans),
    path("delivery-challans/<str:doc_id>/", challans),
    # Tally connector: desktop agent endpoints and the Tally section
    path("tally/agent/pair/", tally_api.agent_pair),
    path("tally/agent/poll/", tally_api.agent_poll),
    path("tally/agent/jobs/<str:job_id>/", tally_api.agent_job),
    path("tally/status/", tally_api.status),
    path("tally/pair/", tally_api.pairing),
    path("tally/devices/<str:device_id>/revoke/", tally_api.revoke_device),
    path("tally/companies/<str:company_id>/", tally_api.company),
    path("tally/settings/", tally_api.sync_settings),
    path("tally/resync/", tally_api.resync),
    path("tally/jobs/", tally_api.jobs),
    path("tally/jobs/<str:job_id>/retry/", tally_api.retry_job),
    path("tally/issues/", tally_api.issues),
    path("tally/issues/retry/", tally_api.retry_issues),
    path("tally/overview/", tally_api.overview),
    path("tally/parties/", tally_api.parties),
    path("tally/parties/<str:guid>/", tally_api.party_detail),
    path("tally/stock/", tally_api.stock),
    path("tally/daybook/", tally_api.daybook),
    path("tally/vouchers/<str:guid>/", tally_api.voucher),
    path("tally/registers/", tally_api.registers),
    path("tally/trial-balance/", tally_api.trial_balance),
    # Production jobs and item recipes (bill of materials, made to order)
    path("jobs/", jobs.jobs),
    path("jobs/settings/", jobs.job_settings),
    path("jobs/<str:job_id>/", jobs.jobs),
    path("recipes/", recipes.recipes),
    path("recipes/<str:product_id>/", recipes.recipes),
    # Phone app screens
    path("mobile/transactions/", mobile_app.transactions),
    path("mobile/dashboard/", mobile_app.dashboard),
    path("mobile/items/", mobile_app.items),
    path("mobile/document/", mobile_app.document),
    # Share documents and statements on WhatsApp / email
    path("share/prepare/", share_center.prepare),
    path("share/pdf/", share_center.pdf),
    path("share/email/", share_center.email),
    path("share/log/", share_center.log),
    path("share/history/", share_center.history),
    path("share/links/<str:token>/revoke/", share_center.revoke),
    path("share/l/<str:token>/", share_center.public_link),
]
