# Partner commission implementation — 10 November 2026

## Confirmed rules
- First subscription payment: 20%.
- Subsequent renewal payments: 10%.
- Renewal notifications: 7, 3 and 1 day before expiry, email and in-app, IST. No expiry-day notification by default.

## Implemented scope
Owner/operator approval and immutable referral assignment before first checkout; integer-paise commission calculation; one persistent commission row per payment/gateway mode; deterministic ordering by verified payment date; updates for verified partial/full refunds; test/live isolation; JSON review statement. The gateway reconciliation path records historical verified invoices for referred customers, then rebuilds their review entries. Historical receipts do not activate an old subscription period. Replaying reconciliation does not create extra commission rows.

Amounts are **review-only, not payable or paid**. The provisional review base is the verified receipt less verified refunds, including tax already in that receipt. The user confirmed percentages, not the tax basis, refund clawback terms, payout schedule or minimum threshold. No transfers or GL partner liabilities are posted. A fully refunded first payment stays first in the sequence, with zero commission; the later payment remains 10%. These policies require commercial review before payout automation.

## Operator commands (staging first)
Use the project's virtual-environment Python. These commands change staging data when approve/assign is selected; substitute actual IDs and addresses.

```powershell
.\.venv\Scripts\python.exe manage.py ensure_reliability_indexes
.\.venv\Scripts\python.exe manage.py manage_partner approve --partner PARTNER001 --name "Partner Name" --email "partner@example.com" --reason "Owner approved partner"
.\.venv\Scripts\python.exe manage.py manage_partner assign --partner PARTNER001 --organization ORGANIZATION_ID --reason "Confirmed referral before checkout"
.\.venv\Scripts\python.exe manage.py manage_partner statement --partner PARTNER001 --mode test
```

The statement is read-only. Live and test commissions never mix. Existing customers with checkouts cannot be retroactively assigned through this command. Retry a rejected concurrent operation after the other operation completes.

## Reminders
`.env.example` now specifies `SUBSCRIPTION_ALERT_DAYS=7,3,1`. The code uses this schedule if the variable is absent; an explicitly empty variable still disables scheduling. Existing environments are not overwritten. `SUBSCRIPTION_ALERTS_ENABLED` remains false until the sender and worker are verified in staging. Enable it deliberately after testing delivery. This update has not modified Render environment variables or sent mail.

## Remaining limitations
No public partner signup/login/approval UI, referral-link attribution, partner-facing portal or payout workflow is implemented in this increment. Operator access is required. Statements are JSON review data, not issued accounting documents. Commission records may change when older receipts arrive. Historical gateway enumeration currently has the existing 300-invoice cap; completeness must be reviewed before any payout. Referred subscriptions require additional historical payment verification calls, so production latency/load verification is still required. Automated repair of interrupted commission rebuilds and full transaction/GL integration remain outstanding. Do not treat this increment as completion of the wider upgrade.

## Tests
Nine focused tests cover 20%/10%, replay idempotence, out-of-order receipts, partial/full refunds, half-up paise rounding, tenant/mode isolation, immutable attribution, missing-date rejection, the approved reminder schedule and gateway historical refund/current-access behavior. Provider calls are mocked; no live payments or email are sent.

Full standalone backend regression suite after this update: 241 tests passed in the isolated MongoMock environment. GitHub upload was attempted but denied by the connected integration (HTTP 403); no Render deployment or live configuration change occurred.
