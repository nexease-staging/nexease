# Release readiness — 11 November 2026

## Verified remotely
- PR #4 is open, draft and mergeable. Its checked head was `8f8ebaa`; `main` was `51ee883`. An earlier temporary `mergeable=false` result did not represent a persistent conflict.
- The connected GitHub combined-status endpoint returned no commit statuses. This does not prove all possible check-run categories are absent. No Actions workflows existed in this checkout before this batch.
- In the owner-confirmed Render workspace, the Singapore frontend, backend and background worker each report a latest live deploy of `51ee883`, dated 9 November. All three track `main` with automatic deploy enabled.
- The older Oregon frontend/backend staging services and worker are suspended. Do not resume or change them as part of this release by accident.
- These are deployment metadata checks, not authenticated browser, database, inbox or device acceptance tests. No service configuration, merge or deployment was changed.

## Fixed in this batch
- Quotation SMTP failures after send begins now become `review_required`, not automatic retries. A lost acknowledgement must not generate repeated enquiries. Known pre-send configuration failures retain bounded retries. A crash leaving `sending` remains held; no automatic replay is introduced.
- Quotation, subscription and partner delivery queues are isolated from one another in the worker. A queue exception no longer prevents later queues or ordinary background jobs from being polled in that iteration. A failed database heartbeat can still terminate the worker; shared database availability is a genuine dependency.
- Three original test fixtures were updated for the existing membership/tenant/quota contract. Production guards were not weakened: the GST error-response test isolates provider errors, the annual-period fixture names its paid plan, and the IRP retry test has an explicit e-invoice allowance.
- Added GitHub Actions checks for both backend suites and frontend lint/tests/build. They use mocked local data and a test API URL, not deployment secrets. The workflow must actually run on GitHub after push; local results do not certify the GitHub runner.

## Next release steps
1. Import/push this batch to the existing upgrade branch. Check both `NexEase release checks` jobs on PR #4.
2. Review the accumulated PR and remaining limitations in UPGRADE_STATUS.md. Keep it unmerged until the desired release scope and staging test results are accepted.
3. Plan rollout carefully: merging into `main` automatically triggers all three Singapore services. Client and server changes should be deployed in a controlled order, backend first. Do not assume simultaneous automatic builds provide that order.
4. Run `ensure_reliability_indexes` on the intended hosted database, verify worker processing, and smoke-test login, invoice creation/retry, payment, email and partner access. Local `.env` commands do not prove the hosted database or service uses the same settings.
5. Rebuild and test the Android app against the intended backend. No APK or Play Store release is included here.

## Still not complete
The original all-screen/all-endpoint audit, all-module transactional accounting, remaining UI migration, additional recurring/reminder automation, real MongoDB failure testing, actual inbox delivery and physical-device acceptance remain pending. This batch stabilizes the current release; it does not certify completion of the full feature list.

## Local verification
- Standalone suite: 297 tests passed, including four new SMTP/worker failure tests.
- Original Django application suite: 966 tests passed.
- Workflow YAML parsed and its two jobs, triggers and read-only permissions were checked locally. GitHub execution is pending push.
- No frontend implementation changed in this batch; its build/tests were not repeated merely for documentation or backend-only changes.
