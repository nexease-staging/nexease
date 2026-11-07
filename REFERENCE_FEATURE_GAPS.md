# Reference coverage and remaining feature work

This package is a reference-based UI refresh of NexEase. It is NOT a claim that every capability of GoGSTBill has been implemented or certified. The supplied recordings show only part of that product.

## Included, connected to existing NexEase services
- Organisation/admin signup, business type and optional saved address.
- Role-aware module navigation, desktop menus and mobile drawer.
- Dashboard date filters, live existing KPIs/trends/aging/status and top customer/supplier data.
- Customer/supplier/product forms and existing stock, sales, purchases, return and finance routes.
- Direct/order invoice drafts, invoice detail, issue/payment/cancel actions, PDF and email actions.
- Existing e-invoice, e-way bill, delivery challan and GST lookup integrations and plan gates. Production provider setup and organisation credentials are still required.
- Existing workforce/payroll, OCR/AI, subscription/owner functions and background jobs retained.
- NexEase public contact/resources footer.

## Reference controls not added as working features in this release
- Quotation and pro forma document lifecycles and conversion into invoices.
- Batch/serial stock, BOM/manufacturing, customer price lists and enforced credit limits.
- Reference invoice controls for additional-charge tax, round-off, reverse charge, payment mode during creation, and alternate shipping addresses. Existing NexEase additional-detail fields remain available; a new control must not be displayed unless accounting/stock behaviour is implemented.
- Reference UPI QR / payment provider integration and SMS document delivery. Web WhatsApp messaging is not automatic PDF attachment delivery.
- Anonymous GSTIN autofill during signup. Existing authenticated GST lookup remains available after login; provider keys must stay server-side.
- Geography map, new-versus-existing-customer graph, login heatmap, best/least-selling product panels and equivalent additional report aggregations.
- All settings/reports visible in the reference recordings have not been certified equivalent to NexEase settings/reports.

No static map, fake login history, mock customer values, competitor advertisements, or inactive Save & Print/payment buttons have been introduced to imply these capabilities.

## Verification boundary
Frontend unit tests, signup backend tests and production web/mobile-export builds validate the changes specified in REFERENCE_UI_UPDATE.md. They do not substitute for real provider integration checks, device testing, or a full accounting/stock acceptance test. Browser visual preview could not connect to the local development server in the build environment. No signed APK/AAB or hosted deployment is included.

Treat additional feature work as functional implementation with validation, not a cosmetic checkbox.
