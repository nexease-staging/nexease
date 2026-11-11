# Mobile master lists — 11 November 2026

Products, Customers and Suppliers now opt into a shared responsive record layout.
Below 768px, rows become two-column labelled cards with the name first and actions last. Long names, GSTINs, emails and monetary values wrap rather than disappear off-screen. Desktop tables retain their headers and existing ordering. The same row markup and handlers are used at both widths; records and actions are not duplicated.

Customers and Suppliers now use PageHeader, IconButton and FilterSheet, matching Products. Search retains all existing backend search fields; the shorter placeholder does not limit matching. Status filter and pagination behaviour are unchanged.

Permission checks and backend data retrieval are unchanged. Cost-price restrictions continue to use the API's restricted/null value. No database migration or backend configuration change is required.

Validation: frontend regression suite, ESLint, TypeScript/web build and Android static export. See delivery message for final results. Native compilation and phone/browser visual acceptance are separate.

Acceptance on web at 390px and Android:
- Search a long customer/supplier name; filter active/inactive; change pages.
- Check contact details and GSTIN remain readable.
- Check product cost, sale price, stock, units and status have their correct labels.
- Create, edit and activate/deactivate using an authorized account.
- Repeat with a read-only account; unavailable actions must remain absent.
- At desktop width, verify the regular table remains usable.
- Scroll to the final row and confirm AI/bottom navigation do not prevent access.

Remaining UI scope: other module lists/forms, physical-device accessibility and layout checks, camera/notification acceptance. This does not certify the entire UI or Android app complete.
