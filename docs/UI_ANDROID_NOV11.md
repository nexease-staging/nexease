# UI and Android checkpoint — 11 November 2026

## Changes
- Products uses the shared compact page header: filter, refresh and create icon actions; full-width short search; status in the filter bottom sheet.
- Shared PageHeader has a stable mobile title/action row. Mobile descriptions/eyebrows are hidden to conserve list space.
- Header navigation, search and account controls have 44px targets. Organization name remains visible; redundant mobile NexEase header mark is hidden (sidebar branding remains).
- Native and legacy dialogs consume Android Back before route navigation. Native cancel events preserve busy/unsaved-change guards. When the keyboard is reported open, Back hides it first.
- Native dialogs have sticky headers/footers; legacy master drawers respect safe areas. Direct two-column master form grids become single column on mobile.
- Shared filter search inputs reserve space for their search icons. Reduced-motion preference disables decorative animation.
- Existing light status-bar icons, safe-area bottom navigation and content padding remain in place.

## Validation
216 frontend tests passed before adding one further legacy-dialog regression; the final targeted overlay suite contains four tests.
Web production build and Android static export passed. ESLint: zero errors, 18 pre-existing warnings.
No physical Android SDK build, browser screenshot comparison, camera/notification test, Play Store release or live deployment was performed here.

## Install
Import the accompanying bundle into the existing Git repository, merge its HEAD using --ff-only, and push a review branch. Deploy through the normal PR and Render workflow.
Stop the local NexEase frontend before BUILD_ANDROID.cmd because npm ci replaces node_modules.
Use the Singapore backend URL for NEXT_PUBLIC_API_BASE_URL. Reinstall the rebuilt APK; a web deployment alone does not replace bundled mobile assets.

## Phone acceptance
At 390x844 and on your actual phone:
1. Products: title/actions and full-width search; filter opens and preserves selection; refresh and add work.
2. Open product and invoice forms; Back dismisses the current dialog, not the page. During save, Back must not dismiss a guarded form.
3. Focus a low form field; keyboard must not obscure it. Back hides the keyboard before dismissing the form.
4. Open sidebar, account and notifications; check text, edges, scroll and all touch targets.
5. Check invoice amounts/chips, bottom navigation and AI button with long lists.
6. Test camera barcode recognition, photo scan, notifications and downloads on physical Android.
7. Repeat relevant layouts in dark mode, landscape and large text.

## Not complete
This is a shared-shell and Products checkpoint, not the full UI/Android definition of done.
Remaining: mobile card layouts for all legacy tables, conversion of remaining one-off toolbars/forms, all-page loading/error/empty-state audit, accessible contrast/visual verification, unsaved-change/draft autosave across every form, physical camera/notification/offline/back QA, signed release AAB and Play Store publishing.
