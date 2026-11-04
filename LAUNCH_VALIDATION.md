# Validation of launch update

Checked 04 Nov 2026. Source: latest NexEase_Complete_Fixed.zip version 13, retaining unrelated project content.

## Passed

- `npx tsc --noEmit` with the installed project dependencies.
- `npm run build`: Next.js 16.4.3 production build, 77 generated pages, including /pricing, /deadlines and Apple icon metadata. Favicon decoding passed the production compiler after ensuring RGBA ICO images.
- Full frontend Vitest suite: **29 files, 172 tests passed**. Four added tests cover service category switching, actual PDF link, correct combo savings, day/time formatting, zero clamp, one-second updates and filing-scheme filtering.
- Backend targeted suite: **27 tests passed**, including 21 new launch tests plus six existing mailbox/AI regression tests. Tests use isolated Mongomock, real MongoEngine models, real stock services, actual proposal state transitions and domain permissions. Provider HTTP responses are mocked.
- Exact request `add bisleri 100 qty in stock`: prepare endpoint resolves the active existing product and unique warehouse; confirm endpoint creates the inventory movement. No product is added. Duplicate confirmation returns the saved result without another movement. Tests cover pre-existing quantity 20 -> 120, first balance creation, unknown and cross-tenant identifiers, multiple warehouses, explicit warehouse codes, negative removals, nonfinite/zero/overprecision quantities, reserved-stock protection and denied permissions.
- GST tests cover nested public taxpayer responses, legal/trade name, address and state code mapping, missing private contact fields, GSTIN mismatch rejection, cached authentication, raw-token header and missing-configuration failure.
- Calendar tests cover monthly versus quarterly dates, IST offset, period-specific override replacement and rejection of timezone-free dates.
- Python compilation of affected backend modules.
- Supplied-logo favicon source inspected visually. Pricing PDF is bundled as a real downloadable PDF, not a print dialog.

## Limits

- Backend tests ran on available Python 3.12.14, Django 5.2.19, MongoEngine 0.29.3 and Mongomock 4.3.0. Existing project pins (including Django 6.1) are unchanged. A test under the exact production Python/Django versions and real Atlas deployment is still required.
- No live paid OpenAI or GST-provider request, actual customer database write, payment or production deployment was performed. Integration access, account billing and credentials require a staging acceptance test.
- Browser visual QA could not run: managed preview injected `--host`/`--strictPort` flags into `next dev`, which rejected them. Working application scripts were not changed to compensate for preview infrastructure. Production build, TypeScript and DOM tests passed.
- A public GST lookup cannot supply private taxpayer information. Current statutory extensions, non-GST deadlines and customer-specific applicability require verified calendar configuration.
- Existing installed APKs do not change when web source changes. Rebuild/reinstall bundled apps to receive new frontend actions and branding.

## Tier/sidebar follow-up - 05 Nov 2026

Added one-time catalogue migration for existing stored prices, tier-based effective features, API/legacy Finance restrictions, tenant configuration filtering and client route guards. Default desktop sidebar remains expanded; group state is now a single open section, initially null. Removed only the two requested dashboard panels. Added backend tier/migration tests and frontend accordion, branding, direct-route and dashboard tests. Verification results for this follow-up are recorded after execution below.

Follow-up results: **36 backend tests passed**, **177 frontend tests passed across 30 files**, TypeScript passed and Next.js production build passed (77 pages). The backend tests include native API tenant checks without relying on middleware request.user and logout after expiry. No live provider calls or production deployment were performed. Earlier runtime/browser limitations remain as described above.
