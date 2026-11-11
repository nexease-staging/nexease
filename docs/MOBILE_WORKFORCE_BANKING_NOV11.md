# Mobile workforce, GST review and banking — 11 November 2026

## Changes
- Banking: account, transaction, transfer and statement lists use labelled mobile cards.
- Shared BusinessWorkspace registers: labels come from the actual schema, keeping employee, site, assignment, leave, advance, monthly-input, expense and GST-register values associated with their fields. CSV export/add/edit actions use accessible icons.
- Payroll: gross, deductions, net payable, paid, salary due and advance balance retain distinct labels on mobile.
- Attendance: employee/site and editable hours/overtime/billable days retain their labels, values, disabled states and selection handlers.
- GST source review: document, party, taxable value and review status are readable as cards.
- Desktop table presentation and all server operations remain unchanged.

## Verification and acceptance
Web build/type-check, frontend regression tests, lint and mobile static export are run for this batch. Physical Android build and visual QA are not implied.
Check payroll against source amounts; attendance selection and edits; all four Banking tabs; GST prefill and linked-state disabling; shared register CSV export/add/edit with appropriate roles.

No database command is required. This bundle also includes the prior finance batch and can be imported from commit 91fa101 or 79c5256.

## Remaining
Full visual/browser accessibility review, compact toolbar migration on remaining pages, form consistency/autosave and unsaved-change guards, advanced reports and administration layouts, and real Android camera/notifications/keyboard/offline validation. This is not a declaration that every UI requirement is complete.
