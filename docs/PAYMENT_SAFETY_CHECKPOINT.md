# Payment safety checkpoint

## Confirmed defects and fixes
1. Customer and supplier payment decimal parsing accepted NaN, infinity and fractions smaller than one paise. Values now must be finite and exactly representable to two decimal places; no silent rounding is introduced.
2. Customer payment accounting prerequisites were resolved only after bank/payment/invoice mutations. Required bank/journal permissions and tenant-active AR/receiving accounts are now checked before those writes. This prevents these predictable failures from leaving a payment without its journal.
3. Retrying customer/supplier accounting returned any existing journal, including DRAFT. Retries now post the existing draft through normal posting validation, return an existing POSTED journal, and block reversed/other states for review. No replacement duplicate journal is created.

## Read-only staging check
Run after selecting the intended staging database. The command only reads records, reports IDs/status issues and makes no corrections:

```powershell
.\.venv\Scripts\python.exe manage.py audit_customer_payment_links --organization YOUR_ORGANIZATION_ID
```

It checks allocation totals, the payment's bank-transaction count/type/amount/account, journal count/status/totals, and linked invoice tenancy. Default cap is 1,000 payments, configurable up to 10,000. The output explicitly identifies truncation. A report without issues is not certification of balances, GST, GL correctness or the complete accounting chain.

## Still unresolved
Customer-payment writes and journal posting remain separate operations. Unexpected posting failures or process crashes can still leave partial state. Broader transaction architecture, concurrent invoice/bank updates, idempotency for blank payment references, fiscal-year numbering and reconciliation/repair workflows remain open. Do not interpret the prerequisite checks as an atomic transaction guarantee. Supplier preflight and other money entry points are not covered by this change.

## Validation
Three new targeted regressions pass (finite/paise validation in both services; draft/posted/reversed journal behavior; no payment/bank writes when system accounts are missing). The existing invoice API regression class passes 37 tests in the isolated test environment. The full standalone suite result is recorded with the delivery summary.

Final standalone regression: 262 tests passed. Existing invoice API class: 37 tests passed. No live database changes or deployments were performed.
