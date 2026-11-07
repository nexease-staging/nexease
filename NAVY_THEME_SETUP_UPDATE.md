# Navy theme, mobile UI and dashboard setup update

## Included
- Deep navy application header with emerald actions, using NexEase's brand palette.
- Right-side mobile menu button, icon-labelled module groups, close button, compact drawer and mobile form action rows. Existing bottom shortcuts and permissions remain available.
- Search and notification icons have explicit header contrast, fixing the blank white search control shown in the screenshot.
- Dashboard figures, donut totals, titles, chart axes, grids, tooltips and legends use light/dark theme tokens. Other screens using slate-950 or black utility tokens also receive the dark-mode text fix.
- Business setup prompts disappear one at a time when completed. When all visible tasks are complete, the entire panel disappears.
- Completion is based on the organisation's saved invoice logo, invoice bank-details field, and the current user's connected mailbox. Entering an organisation email alone does not mean a sending mailbox is connected.
- Invoice-setting and mailbox updates refresh the dashboard configuration cache. Cleared settings show their setup task again.
- Public welcome page uses navy/emerald styling and the included laptop-and-phone dashboard illustration at frontend/public/nexease-devices-preview.png. It is labelled illustrative, uses fictional demo data, and contains no original customer names.
- The four-column footer is now rendered at the bottom of the welcome page, as well as the pricing/deadline pages. The previous placement inside the unused testimonial branch was corrected.

## Run
Use the same instructions in REFERENCE_UI_UPDATE.md. Preserve your working .env and encryption keys.
Both backend and frontend must be updated together for saved setup-status detection. Rebuild the APK for the mobile changes.
Hard-refresh your browser after starting/deploying the new frontend.

## Validation
- TypeScript check passed.
- 188 frontend tests passed (34 test files), including completed/partial setup, permission filtering, invoice flow/totals, menus and signup.
- 15 isolated backend/signup tests passed, including mailbox status scoped to user and organisation, changed-email reconnection, empty bank details and absence of mailbox secrets in configuration responses.
- Contrast calculations on the explicit text/background tokens are recorded in NAVY_THEME_VALIDATION.md.
- Physical-device testing and live provider checks are still required; this source package is not a signed APK/AAB.
- Additional GoGSTBill functional parity remains outside this UI update; see REFERENCE_FEATURE_GAPS.md.
