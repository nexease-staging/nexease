# NexEase UI overhaul: install

Back up first (or work on a Git branch). Nothing in `apps/`, `config/` or the API is touched.

```powershell
Set-Location E:\NexEase\frontend
python ..\nexease-ui-overhaul\apply_ui_overhaul.py .      # copies files and patches 4 existing files
npm.cmd ci                                                 # no new packages: lucide-react, Tailwind 4 already installed
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000/api/v1"
npm.cmd run test:run
npm.cmd run build
npm.cmd run dev
```

The script is safe to re-run. If a target text is not found it stops and changes nothing for that step.
The previous invoices page is kept as `src/app/(protected)/invoices/page.tsx.bak`.

## What changes
| Area | File |
|---|---|
| Tokens, badges, tables, sheets (light + dark) | `src/styles/nexease-ui.css` (imported from `globals.css`) |
| Shared pieces | `components/ui/{badge,stat-card,page-header,empty-state}.tsx`, `lib/format.ts` |
| Invoices | `features/invoices/components/invoices-view.tsx` + new `invoices/page.tsx` |
| Dashboard | `features/dashboard/components/dashboard-overview.tsx` (replaces the dark hero) |
| Fewer clicks | `components/layout/quick-create.tsx` (header menu + mobile + button), `command-palette.tsx` (Ctrl/Cmd+K) |
| Wiring | patches `app-shell.tsx`, `app-header.tsx`, `dashboard-shell.tsx`, `globals.css` |

Deep links: `/invoices?new=1` (full invoice), `/invoices?new=direct` (quick invoice), `/invoices?status=ISSUED`.

## Not verified here
Files were syntax-checked with TypeScript and the patch script was run against a copy of your ZIP, but
dependencies could not be installed in this environment, so there was no full type-check, `npm run build`,
Vitest run or browser/device check. Run the commands above and test on a phone and in dark mode.

## Next steps (same tokens)
Restyle `dashboard-kpi-grid.tsx`, the other list pages (purchase orders, bills, customers) with the same
`nx-table` / card-list pattern, and `app-sidebar.tsx` (active pill, icon sizing).
