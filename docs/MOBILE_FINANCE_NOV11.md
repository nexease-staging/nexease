# Mobile finance and reporting lists — 11 November 2026

Changed screens: Accounts Payable, Accounts Receivable (both tables), General Ledger, Trial Balance, Journal Entries, Customer Payments, Chart of Accounts, Credit Notes and Vendor Debit Notes.

The shared responsive card presentation retains the original table on desktop. On mobile financial records put the document/account identifier first, with explicit field labels and wrapping values. General-ledger descriptions span the card. Trial-balance footer totals have a separate labelled two-column layout; the summary is not mistaken for a data row.

No calculation, data retrieval, authorization, posting, payment, filtering or export logic changed. No database command is required.

Validation: web production build/TypeScript; targeted financial-report regression tests (10 tests); lint and Android static export. Final delivery records build results. Real browser/Android visual and screen-reader acceptance remain outstanding.

Acceptance checklist:
- Compare each mobile card against the same desktop row.
- Check long account names, document references and negative balances.
- Check TB debit and credit totals separately and confirm they match the desktop report.
- Use receivables aging filters and both customer-summary/detail tables.
- Open source documents, payment/detail dialogs and exports where available.
- Check permissions with a read-only user; no action should become newly available.
- Check 390px portrait, landscape, dark mode and large text.

Remaining: workforce/tax/banking layouts, remaining toolbars/forms, all-screen visual/accessibility audit and physical-device camera/notifications/keyboard testing. This checkpoint does not certify the entire UI/Android upgrade complete.
