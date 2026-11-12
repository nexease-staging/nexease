# Invoice usability — 13 November 2026

- Both direct invoice creation forms have a per-line ₹/% segmented selector. A percentage applies to quantity × unit price before tax; it is converted to a two-decimal rupee discount in the existing request contract.
- Conversion uses integer/rational arithmetic with half-up paise rounding. Negative, invalid, >100% and above-line-value discounts reject saving. Empty inputs preview as zero.
- Percentage mode is a creation-form convenience, not a new persisted backend field. Existing stored invoices and edit forms continue to use rupee discount amounts. Order-derived invoices keep the order's existing calculation.
- Mobile invoice cards open through a full-card button. Payment controls remain separate. The redundant eye icon is removed; desktop invoice numbers are keyboard-accessible view buttons and rows remain clickable.
- Detail view puts customer/dates/balance, items and totals first. Description/print details and editing are expandable below; document/status actions follow. The mobile facts area uses two columns.
- No database migration or change to backend GST/posting rules.

Validation: full frontend suite and focused invoice tests; web build/TypeScript, lint and Android static export. Physical-device/browser visual acceptance remains required. Check percentage toggles on multiple lines, 100% discounts, rounding, card/payment clicks and detail ordering on web and APK.

This batch does not complete the broad remaining-upgrades list. Shared card click behaviour across all other modules, remaining form/toolbar migration, draft autosave, accessibility/visual audit and native-device tests remain outstanding.
