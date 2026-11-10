# Mobile operations lists — 11 November 2026

Eight additional list tables now use the shared mobile card layout:
Warehouses, Inventory, Stock Movements, Stock Transfers, Sales Orders, Purchase Orders, Goods Receipts and Vendor Bills.

The desktop table remains the same. On mobile, fields have explicit labels; full values can wrap; action rows wrap and retain 44px targets. Transfer routes have a full-width field. Permissions, pagination, filtering, calculations and mutations are unchanged.

The action-row rule now targets the Actions label explicitly. Read-only tables and conditional permission columns therefore retain their final data label (for example Available or Created by).

Validation: TypeScript/production web build, lint and Android static export. Each changed table was checked for matching header/cell label counts. This is a presentation-only change; no backend or database migration.

Device acceptance:
- View every changed page at 390px and desktop width.
- Compare displayed totals, dates, warehouses, quantities and statuses with the original documents.
- Check read-only users see Available/Status labels without action controls.
- Check long transfer routes and multi-action rows wrap without covering values.
- Open detail/edit dialogs and test paging/filtering.
- Confirm downloaded documents and mutations behave as before.

This is not full UI completion. Remaining work includes other reporting/finance/workforce lists, legacy toolbar/form standardization, visual/accessibility review and physical Android camera, notification and keyboard tests.
