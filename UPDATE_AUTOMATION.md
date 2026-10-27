> **Professional Update (24 October 2026):** Start with [UPDATE_PROFESSIONAL.md](UPDATE_PROFESSIONAL.md). It supersedes older workflow/accounting limitations below where explicitly described.

# NexEase workforce automation update — 22 October 2026

This is the full source package for the NexEase version you have been testing in F:\NexEase. It adds a shorter workforce workflow, employee migration, balances and numbering preferences. Keep using nexease_testing while reviewing it.

## Install over the NexEase test version

1. Stop the backend, frontend and background worker with Ctrl+C in their terminals.
2. Make a backup copy of F:\NexEase and back up the test database before using the new workflows.
3. Extract the ZIP to a separate temporary folder. Open its inner NexEase folder, which contains manage.py.
4. Copy that inner folder's contents into F:\NexEase and choose Replace for the updated source files. Do not place another NexEase folder inside F:\NexEase.
5. The archive contains no .env, .env.local, .venv, node_modules, .next, database or uploads. Keep your existing configuration and local files. Do not replace .env with .env.example.
6. In the backend terminal:

```powershell
cd F:\NexEase
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

7. In the worker terminal:

```powershell
cd F:\NexEase
.\.venv\Scripts\python.exe manage.py run_background_worker
```

8. In the frontend terminal:

```powershell
cd F:\NexEase\frontend
npm run dev
```

Open http://127.0.0.1:3000 and refresh. This update adds blinker as a Python dependency; it adds no JavaScript dependencies. No SQL migration command or production database upgrade is needed for the already-running NexEase test version. MongoEngine creates the new collection indexes when used.

## Daily workflow

1. Import employees through Migration → Employees, or add them in People & payroll. Download the sample workbook and fill its Data sheet. Employee code, name, joining date, pay basis and rate are required for imports. Keep employee codes, phone numbers, bank accounts, UAN and IFSC as text in Excel. Duplicate employee codes can be skipped; imports do not overwrite employees.
2. Create a customer once. Under Labour & client sites, choose that customer for a site. An empty site address/phone is filled from the customer. Enter the site's daily billing rate.
3. Assign employees to the site and shift for a date range. Leave the assignment rate blank to use the site's rate. You enter assignments once for their period.
4. Use Daily attendance. Assigned workers appear automatically. Tick those who attended, adjust hours/overtime/billable days if needed, and approve. Do not select absent workers. Regular hours and overtime are separate. This creates approved timesheets without re-entering worker/site/rate details.
5. In People & payroll choose the month and Automatic from daily work. Calculate, review and approve. Paid days are unique dates with approved work plus explicitly approved paid leave; multiple shifts on the same date do not create multiple paid days. Monthly pay uses calendar days as its denominator.
6. Record salary payments against individual employees with an external payment reference. Partial payments reduce the remaining salary balance. Recording a payment does not initiate a bank transfer or post an accounting journal.
7. Once all site attendance for the month is complete, use Bill approved site work. Select site/month, dates and your reviewed tax rate. NexEase fetches the client and totals and creates one draft invoice. Review and issue it in Invoices; record client receipts there.

## What balances mean

- Salary outstanding: approved net salaries minus recorded salary payments. Draft payroll does not create a payable.
- Advance outstanding: recorded advances less opening/manual recovered amounts and deductions in approved payroll. Draft payroll does not recover an advance. Automatic recovery is capped at earnings remaining after other deductions and carries the rest forward.
- Unbilled work: approved work not yet linked through the site invoice workflow.
- Client outstanding: unpaid issued/partially paid invoices for the site-linked customer, after recorded receipts. It includes all of that customer's invoices. Approving payroll does not make a customer invoice payable.

Example: Ravi works 24 days at ₹700/day. An outstanding ₹2,000 advance gives ₹16,800 earnings, ₹2,000 recovery and ₹14,800 net salary before other deductions. A ₹10,000 salary payment leaves ₹4,800 payable. If the client rate is ₹950/day, the site work is ₹22,800 before reviewed tax. The client balance arises when that invoice is issued.

## Automatic and manual numbering

Settings → Numbering lists prefixes, minimum digit counts, default modes and next numbers. On saving a new numbered record, choose automatic or manual. Employee/site codes may be left blank for automatic numbering. Existing master forms may display AUTO until the save-time choice; AUTO is replaced before the record is stored.

Supported display references: employees, sites, customers, suppliers, product SKUs, warehouses, sales orders, invoices, purchase orders, goods receipts, vendor bills, customer/supplier payments, sales/purchase returns, credit/debit notes, stock transfers, bank transactions, bank transfers, bank statements and journals. Internal database IDs, legal identifiers, bank account numbers, customer/supplier external references and category names are not renumbered.

Numbers are organisation-scoped, checked for collisions and reserved atomically. Next numbers cannot move backwards; failed/cancelled attempts can leave sequence gaps. Existing saved numbers and imported historical references are preserved. Automatic previews are provisional, not reservations. Default modes apply in the updated UI; direct integrations should send their intended numbering preference. Changing a prefix does not rename existing records. Financial-year resets are not automatic.

## Review boundaries

- Automatic payroll uses approved timesheets and leave explicitly classified as paid. Holiday/weekly-off calendars, half-day policy, other leave classifications and piece units need reviewed manual monthly inputs. Do not assume a full month's attendance when there are no approved source entries.
- Monthly inputs remain the place for reviewed contribution wage bases, allowances, bonus, arrears, TDS/PT/LWF and other deductions. Statutory rates/eligibility are not inferred. This is not a universal statutory payroll engine.
- Source work/leave in approved automatic payroll is locked; advances already recovered through approved payroll cannot be edited. There is no reversal/correction-run workflow yet.
- A site invoice links and locks the site's month. Retrying returns the same invoice. Cancelling it does not automatically unlock/rebill work; review corrections separately. Previously created manual invoices are not automatically matched to timesheets, so reconcile these before using site billing.
- Daily bulk attendance validates the batch first, but a storage failure mid-write can leave a partially recorded batch. Reload the board: recorded rows are shown and cannot be submitted again. This is not a multi-document database transaction.
- Salary payments and invoices use separate records and review steps. Payments are recorded, not transferred. Tax exports remain workpapers, not GSTN return filing.
- Validation uses an isolated MongoDB mock, not your Atlas database. Review with sample data before client use. UI tests and a production build pass; no full browser/Atlas end-to-end certification is claimed.

## Administrator recovery after a server crash

Workforce writes are serialised per organisation. A process killed during a write can leave a lock. Stop every backend/worker instance, inspect the last operation, then use:

```powershell
.\.venv\Scripts\python.exe manage.py recover_workforce_lock --organization YOUR_ORGANIZATION_ID --confirm-workers-stopped
```

Never clear a lock while a writer is still running. Recovery removes only the lock, not any business records. Inspect any partial attendance batch before retrying.
