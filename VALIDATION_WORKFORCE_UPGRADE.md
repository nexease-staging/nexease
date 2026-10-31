# Validation — Workforce and billing upgrade

Validated on 28 October 2026 against the uploaded NexEase_SaaS_Final source.

- 118 NexEase backend tests passed (including 13 new upgrade tests).
- 883 original application regression tests passed.
- 108 frontend tests passed across 15 test files.
- Next.js production build and TypeScript compilation passed.
- Python runtime used the package's pinned Django 6.1, MongoEngine 0.29.3 and ReportLab 5.0.0 dependencies.
- New tests cover GST heads, rejection before partial master creation, service-only stock behaviour, immutable HSN snapshots, ten PDF presets and multipage output, source-deduplicated GST workpapers, balanced service/GST journals and credit reversals, draft/permission/tenant guards, exports exceeding 1,000 records, formula escaping, payslip PDFs/ZIPs and AI employee/category creation.
- Desktop Workforce, invoice settings, main dashboard and mobile Workforce checked using synthetic API fixtures in Chromium. These checks do not validate the user's Atlas data or live browser microphone service.
- Generated invoice PDFs were rasterised and inspected. Payslip PDF and archive content were also checked.

Tests use an isolated in-memory MongoDB mock. No user database was contacted; no production data, billing, OpenAI request, payroll disbursement, message delivery or GST filing was performed. Browser voice/provider availability and live email/WhatsApp delivery are not integration-tested.

Run the local acceptance checklist in UPGRADE_WORKFORCE_AND_BILLING.md before using live business records.
