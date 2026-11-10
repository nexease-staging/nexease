# Partner commission implementation — 10 November 2026

## Confirmed rules
- First subscription payment: 20% of the subscription amount excluding GST.
- Subsequent renewal payments: 10% of the subscription amount excluding GST.
- Renewal notifications: 7, 3 and 1 day before expiry, email and in-app, IST. No expiry-day notification by default.

## Implemented scope
Owner/operator approval and immutable referral assignment before first checkout; integer-paise commission calculation; one persistent commission row per payment/gateway mode; deterministic ordering by verified payment date; updates for verified partial/full refunds; test/live isolation; JSON review statement. The gateway reconciliation path records historical verified invoices for referred customers, then rebuilds their review entries. Historical receipts do not activate an old subscription period. Replaying reconciliation does not create extra commission rows.

Amounts are **review-only, not payable or paid**. The confirmed base excludes GST. Gross payment minus verified GST gives the subscription base; refunds reduce it by the refund amount excluding verified refunded GST. Missing or stale tax evidence produces a held entry with no calculated amount. No tax rate is assumed. Refund clawback terms, payout schedule and minimum threshold remain undecided. No transfers or GL partner liabilities are posted. A fully refunded first payment stays first in the sequence, with zero commission; the later payment remains 10%. These policies require commercial review before payout automation.

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

## GST-exclusive update
A ₹1,180 receipt with verified GST of ₹180 has a ₹1,000 commission base: ₹200 first-payment commission or ₹100 renewal commission. These numbers illustrate arithmetic, not an assumed GST rate for every payment.

The gateway currently verifies gross receipts but does not establish a trusted GST breakdown. An operator must record the GST from the subscription tax invoice and any credit note. The command records an audit event and ties evidence to the exact payment/refund totals. A later refund invalidates old evidence and holds the commission until reviewed again. Explicit verified zero GST is supported; missing GST is never treated as zero.

```powershell
.\.venv\Scripts\python.exe manage.py review_commission_tax --payment PAYMENT_ID --mode test --gst-paise 18000 --refund-gst-paise 0 --source "Subscription invoice INV-001" --reason "Checked subscription tax invoice"
```

Values above are examples, not production inputs. Statements show held entry counts and exclude uncalculated amounts from the review total. Existing commission rows need rebuilding/reconciliation to adopt the new basis; do not pay legacy including-tax rows. Twelve focused tests pass, including GST exclusion, absent/stale evidence, partial refunds and invalid tax breakdowns. Payouts and deployment remain unchanged.
