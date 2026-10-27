> **SaaS Edition:** Start with [START_HERE_SAAS.md](START_HERE_SAAS.md). It describes owner setup, subscriptions, AI, payment configuration and current limits.

> **Professional Update (24 October 2026):** Start with [UPDATE_PROFESSIONAL.md](UPDATE_PROFESSIONAL.md). It supersedes older workflow/accounting limitations below where explicitly described.

# Requested feature status

Updated 22 October 2026. See UPDATE_AUTOMATION.md for the new workflow, numbering coverage and boundaries.

This table distinguishes working additions from capabilities that remain partial. “Complete for every business” is not a verified property of this release.

| Request | Delivered | Remaining boundary |
|---|---|---|
| Preserve all existing features | Original backend/frontend modules retained; regression suite passes in the documented mock environment | Not every browser workflow was exercised against real MongoDB |
| Complete remaining migration + sample Excel | Added employees, vendor bills, customer payments and supplier payments to the existing ten types; target/source mapping editor; 14 downloadable workbooks (including employees) with example/guide sheets | One payment allocation per row; related masters and issued/posted documents must already exist. This is not a universal importer for arbitrary ERP formats |
| Payroll and labour assignment | Employee/site/assignment/timesheet registers; overlap checks; monthly/daily/hourly/piece pay; overtime; allowances/bonus/arrears; PF/ESI rates and wage bases; reviewed TDS/PT/LWF; leave/advance registers; approval locking; payslip print view; Excel register/payment workpaper; site billing export | Automatic mode reads approved site work and explicitly paid leave, allocates advance recovery, tracks partial salary payments and creates site invoice drafts. Exceptions and statutory inputs still require review. No automatic annual salary-TDS computation, full-and-final settlement, gratuity/bonus eligibility engine, statutory PF/ESI return files, bank payout API, biometric import or employee self-service. Recording paid does not transfer money or create accounting journals |
| Business scope at organisation creation | Seven profiles; stored in MongoDB; editable settings; profile-based sidebar | Profile selection changes focus/navigation, not security permissions or all statutory rules. Manufacturing profile does not add BOM/MRP/shop-floor production |
| NexEase name/theme | Frontend branding, page metadata, backend default application name, green/cream colours | Internal identifiers/database collection names retained for compatibility |
| Collapsible sidebar groups | Click section headings to expand/collapse; existing narrow sidebar mode retained | Group state is session/component state, not cross-device preference |
| Dark/light switch | Administration → Settings; saved locally in browser | Full visual accessibility review of every original chart/dialog remains outstanding |
| Direct invoices / missing masters / notifications | Draft invoices without SO or stock availability; new customer/product records when permitted; quick PO/vendor-bill entry with supplier/product creation; review notifications | These actions do not dispatch/receive stock. Direct invoices need separate stock reconciliation. Existing order-linked returns require an order; direct-document return automation is not implemented. Notifications cover these new quick-entry paths, not every possible update in all legacy modules |
| Retail / wholesale / labour / manufacturer and other scopes | Retail, wholesale, labour supply, manufacturing business, services, construction and mixed profiles | No industry-specific regulatory certification or manufacturing production engine |
| Complete GST/taxation and GSTR reports | Registration details; reviewed tax register; Excel workpapers labelled GSTR-1/3B/9; separate invoice/bill/credit/debit-note reconciliation | **Not complete statutory returns.** No official GST JSON schema export, GSTN filing, e-invoice/IRN, e-way bill, GSTR-2B reconciliation, automatic place-of-supply/HSN decisions, amendment/advance/RCM/ITC reversal engine, annual-return reconciliation or full direct-tax compliance. Existing aggregate invoice tax is not silently split into tax heads |
| Business landing page + signup/login + customers | Public feature page and signup/login links; customer-story area | No invented endorsements. Replace the placeholder only with genuine customer feedback and permission |
| Full updated package | Combined backend + frontend source, sample workbooks and setup/test guides in one ZIP | No live deployment, real database, credentials or generated dependency/build folders included |

## Operating details

- New record lists currently display/export at most 1,000 records per collection; payroll history displays up to 120 runs. Larger installations need pagination before rollout.
- Employee/site records can be edited and deactivated; no destructive delete UI was added.
- Approved payroll snapshots are immutable through the new UI/API. Correct inputs before approval. Reversal/correction runs and payroll-to-ledger posting are not included.
- PF/ESI coverage and contribution wages are explicit reviewed inputs. Policy values are not silently set to potentially outdated statutory defaults. State-specific PT/LWF and annual TDS remain reviewed amounts.
- Approved timesheets produce billing workpapers; they do not automatically issue invoices or populate attendance. Leave and advance registers are supporting records, not automatic balance/recovery engines.
- The payslip print action uses browser printing of the current view; it is not a separate statutory payslip PDF renderer.
- New financial/master creation uses existing MongoEngine services and collections. Multi-document transactional guarantees and high-concurrency financial writes need real MongoDB integration/load testing; in-memory tests do not establish these guarantees.
- Business-scope navigation preserves all existing data. Change back to Mixed to display all module groups, subject to permissions.

## Sources used to define the reporting boundary

Reviewed 21 October 2026. These are authoritative workflow references, not a claim of complete compliance implementation:

- GST GSTR-1: https://tutorial.gst.gov.in/userguide/returns/GSTR_1.htm
- GST GSTR-3B: https://tutorial.gst.gov.in/userguide/returns/GSTR3B.htm
- GST GSTR-9: https://tutorial.gst.gov.in/userguide/returns/Manual_gstr9.htm
- ESIC official contribution information: https://roap.esic.gov.in/
- EPFO employer resources: https://www.epfindia.gov.in/site_en/For_Employers.php

Use the applicable current official rules and your payroll/tax professional's review for each period before making statutory payments or filings.
