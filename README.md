> **SaaS Edition:** Start with [START_HERE_SAAS.md](START_HERE_SAAS.md). It describes owner setup, subscriptions, AI, payment configuration and current limits.

> **Professional Update (24 October 2026):** Start with [UPDATE_PROFESSIONAL.md](UPDATE_PROFESSIONAL.md). It supersedes older workflow/accounting limitations below where explicitly described.

# NexEase — updated business management source

This ZIP contains the combined Django/MongoDB backend and Next.js frontend, based on your two uploaded archives. It includes existing modules plus the new features listed below. It is a source-code release for staging review, not a claim that every requested statutory or industry-specific feature is complete.

**Start with `SETUP_AND_UPGRADE.md`. Read `FEATURE_STATUS.md` before using live payroll, stock or tax records.**

## Included changes

- NexEase branding, green-and-cream interface, dark/light setting, collapsible sidebar groups.
- Public business page with signup/login, feature descriptions and an honest customer-story placeholder.
- Business scope during signup and in organisation settings: retail, wholesale, labour supply, manufacturing business, services, construction and mixed. Profile-based navigation; existing permissions still apply.
- Employees, client sites, labour assignments, site timesheets, leave/advance registers and labour billing workpapers.
- Monthly/daily/hourly/piece-rate payroll, overtime, additions, reviewed deductions, configurable PF/ESI policy, draft/approve/paid workflow, payslip print view and Excel export.
- Thirteen migration types, Excel template downloads, example sheets, column guides and editable column mapping. Added vendor-bill, customer-payment and supplier-payment import dispatch.
- Direct draft invoices without sales orders or available stock; quick purchase orders and vendor bills; permitted creation of missing masters and review notifications.
- GST registration/review register and GSTR-1/3B/9 **preparation workpapers** with a separate source reconciliation sheet.
- Original inventory, sales, purchasing, accounting, banking, authorisation and background-job modules retained.

## Contents

- `apps/`, `config/`, `core/`, `manage.py`: backend.
- `frontend/`: frontend source and dependency lockfile.
- `migration_samples/`: 13 ready-to-fill Excel templates.
- `tests_nexease/`: isolated regression checks for the additions.
- `FEATURE_STATUS.md`: implemented behaviour and outstanding limitations.
- `VALIDATION.md`: test results and environment.
- `CHANGELOG.md`: technical changes and upgrade notes.

Generated dependency/build folders (`node_modules`, `.next`, Python environments, compiled caches) are intentionally excluded. They are recreated during installation. No split-file joining is needed.
