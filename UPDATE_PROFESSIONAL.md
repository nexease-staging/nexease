> **SaaS Edition:** Start with [START_HERE_SAAS.md](START_HERE_SAAS.md). It describes owner setup, subscriptions, AI, payment configuration and current limits.

# NexEase Professional Update — start here

24 October 2026. This is the complete application source, not a patch-only archive.

## Upgrade your working installation

1. Stop the backend, frontend and background worker (Ctrl+C in their terminals). Back up your current project and MongoDB database. First test the update against a database copy.
2. Extract the ZIP to a temporary folder. Open its inner `NexEase` folder: it contains `manage.py`, `apps` and `frontend`.
3. Copy the CONTENTS of that inner folder into your existing project folder, accepting source-file replacements. Do not create `NexEase\NexEase`. Keep your existing `.env`, `frontend\.env.local`, uploads and `.venv`. These private/runtime files are not included in the archive.
4. In PowerShell, from your existing project root, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py upgrade_professional
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

If `.venv` does not exist, first run `py -m venv .venv`. Reuse your existing environment files; do not replace credentials with examples.

5. Open another PowerShell terminal in the project root:

```powershell
cd frontend
npm ci
npm run dev
```

6. For queued background jobs, open another terminal in the project root:

```powershell
.\.venv\Scripts\python.exe manage.py run_background_worker --sleep 2 --lease-seconds 300
```

7. Open http://localhost:3000 (or the URL printed by Next.js), log out and log back in. Review custom role permissions: `expenses.read` and `expenses.manage` are new. Existing system Admin roles receive these from the upgrade command.
8. Open Settings → Business modules & books → Prepare / repair system accounts. This creates missing accounts without replacing existing accounts or transactions. Conflicting/inactive account mappings require review.

This upgrade does not reset your approved payroll, employees, attendance, advances or payments. Historical sources are not posted automatically. Do not use seed/demo data commands on your working database. If upgrading from the original IMS rather than the Automation Update, also follow SETUP_AND_UPGRADE.md and its `upgrade_nexease` step.

## Where to use the changes

| Task | Location and steps |
|---|---|
| Find suppliers/customers/items | Type in selection fields; choose a matching result. Product/customer/supplier fields support remote suggestions. Direct invoice and quick purchase also have master lookup; selection fills the matching details. Existing manual new-master entry remains available. |
| Sidebar | Groups start collapsed. Click a heading to expand. Scroll the sidebar separately from the main page. |
| Hide Workforce or Expenses | Settings → Business modules & books. Switch the module off and save. This changes sidebar visibility, not data or role permissions. |
| Assign several workers | Workforce/Labour → Assign a team. Choose site, dates and shift, select workers and enter each worker's customer billing rate. Submit once. In-house staff do not need a site assignment. |
| Daily attendance | Choose date and Site / staff group. Select all shown or Select present yesterday. Review hours, overtime and billable days, then approve selected attendance. Yesterday means approved attendance from the preceding calendar day. |
| Timesheets search | Type the site name/code or worker name/code in the records search. Matching rows are selected on the server. |
| In-house staff | Payroll → Employees: choose employment type `inhouse`, set salary basis/rate and employment dates. In Daily attendance choose In-house staff and approve attendance. Create the monthly payroll run; internal attendance produces no client billable units. |
| Payroll and payments | Review and approve the run; record salary payments with date and payment mode. Outstanding salary and recoverable advances remain visible. Approval records payroll liability; a salary payment reduces it. Client receivables arise from issued client invoices, not from approving payroll. |
| Invoice description | Open a DRAFT invoice. Enter each item's description, select the print checkbox and click Save descriptions BEFORE issuing or downloading the PDF. Checked descriptions print below the item name. |
| Invoice account error | Prepare / repair system accounts, then retry issuing the draft. Missing defaults can also be created during system-account lookup. Existing conflicting accounts are not overwritten. |
| Daily expenses | Expenses: enter date, category, payee, description, amount, payment mode/account and reference. Save once; export CSV from the expense screen. Use a distinct reference per payment. |
| Accountant handover | Settings → Business modules & books → Accountant export. Choose date range and download ZIP with sales, purchases, credit/debit notes, receipts/payments, workforce sources, expenses, GL and TB CSVs. Document status is included; drafts are not posted revenue/expense. |

## Books: important operating details

New expenses and advances post automatically. Payroll approval posts wages/contributions, salary payable, advance recovery and deduction liabilities. Salary payments reduce salary payable. Existing invoice/vendor-bill posting flows remain in use. Purchase/sales orders are commitments and do not themselves post accounting entries.

Cash, bank/UPI/debit card and credit card use their appropriate control accounts; expenses/advances can select a specific permitted ledger. These entries do not initiate bank transfers or create bank-statement transactions/update bank-account operational balances. Reconcile bank activity separately.

Daily expenses record the gross amount. They do not claim GST input tax credit; use the vendor-bill workflow for tax-bearing purchases and review with your accountant. Payroll deductions/contributions post to control liabilities; remittance, statutory eligibility and filings still require review. This release is not a statutory filing certification.

If a source saves but books sync fails, do not enter it again. Settings → Accounting setup & recovery lists pending/historical sources. Review, select and retry. Only sync older records if they are not already represented by manual journals. Historical advances with recovered balances require reviewed opening entries. Source save and posting are separate operations; recovery is explicit and journal creation is idempotent.

Posted expense/advance sources cannot be edited in place. Use reviewed accounting corrections; automated cancellation/reversal of every workforce source is not supplied. Approved payroll period locks remain. Bulk assignment validates before writing; a storage failure may save part of a batch, and identical retries skip existing assignments.

Record grids/search and the historical recovery list have a 1,000-record cap. Narrow searches for large datasets; accountant and expense CSV exports are not limited to the visible grid.

## Welcome page and customer trust

The original NexEase page now presents product benefits, modules, business types, workflow and FAQs, with login/signup. Dashboard amounts are labelled illustrative. The testimonials array in `frontend/src/app/page.tsx` is intentionally empty; add only genuine consented customer quotes. Until then, the page shows an early-user invitation.

## Validation and deployment

934 backend tests and 104 frontend tests passed; Next.js production build passed. Backend tests use isolated mocked MongoDB. Browser checks cover the welcome page and selected workforce interactions using mock API responses. Your Atlas database and live payment/book reconciliation were not tested or modified. See VALIDATION.md.

This package excludes installed dependencies and generated builds; its compact ZIP size is expected. Local `runserver`/`npm run dev` are for development. Retain your established production deployment settings and perform staging acceptance before deployment.
