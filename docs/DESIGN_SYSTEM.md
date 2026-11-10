# NexEase design system — incremental adoption

## Contract
Keep NexEase branding: navy app chrome, green primary actions, neutral surfaces. Use the existing `frontend/src/styles/nexease-ui.css` token source rather than introducing a second brand. Typography follows its `--nx-font`. Spacing follows 4/8 px increments. Interactive targets are at least 44 px; icon glyphs use Lucide at 18–20 px with consistent stroke. Primary Save/Create actions retain text; icon actions require accessible names and desktop titles/tooltips.

Critical labels and money must not be ellipsized. Compact amounts must expose exact values on tap. A business name may truncate. All text/background combinations require a measured 4.5:1 contrast audit before design-system acceptance; that audit is still pending.

## Implemented in this patch
- `IconButton`: shared 44 px icon action with aria-label and title.
- `FilterSheet`: labelled native modal dialog; bottom sheet on mobile; explicit close and Done controls.
- `StatCard`: wraps labels/captions, shows full value, optional exact-value disclosure. Linked cards avoid nested interactive disclosure.
- Invoice toolbar: compact title/actions, main create action in toolbar, customer filter in sheet.
- KPI strip and status chips: horizontal mobile scrolling, full-width search with short placeholder.
- Invoice cards: compact party/status, dates, balance and existing actions.
- Mobile shell: no global create FAB; one compact AI control above safe-area-aware bottom navigation, content bottom padding.
- Native status bar: light icons over navy; keyboard focus scrolls into view.

## Required shared component migration — not yet complete
PageHeader, Toolbar, KpiCard, SearchInput, FilterChips, DataCard/DataTable, StatusBadge, AmountPill, Button, FormField, Select, DatePicker, MoneyInput, Modal, BottomSheet, ConfirmDialog, Toast, EmptyState, Skeleton, Tabs and Pagination must be consolidated against existing equivalents. This patch does not claim all one-off implementations have been replaced.

## Screen acceptance checklist
At 390×844, verify three invoice cards are visible with real data; all status chips reachable; no overlays cover data; filter dismissal/focus/back behavior works; exact amounts accessible. Verify tablet/desktop, dark mode, 200% text scale and screen-reader names. Test Android status/navigation bars, keyboard and hardware back on a real APK. None of these physical/browser checks is implied by a passing build.

## Forms
Target: mobile single column, labels above controls, inline errors, currency/date conventions, sticky Cancel/Save, pending-submit protection and unsaved-change warning. Long-form draft autosave remains outstanding. Avoid silently changing issued financial documents during UI migration.
