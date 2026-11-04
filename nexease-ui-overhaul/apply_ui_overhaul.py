#!/usr/bin/env python3
"""Wire the NexEase UI overhaul into the existing frontend. Usage:  python apply_ui_overhaul.py <path-to>/frontend
Idempotent. Each step fails loudly (and writes nothing) if the target text is not found."""
import pathlib, re, shutil, sys

pkg = pathlib.Path(__file__).resolve().parent            # .../nexease-ui-overhaul
target = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
if not target or not (target / "src").is_dir():
    sys.exit("Usage: python apply_ui_overhaul.py <path to your frontend folder (contains src/)>")
src = target / "src"

def read(p): return p.read_text(encoding="utf-8")
def write(p, s): p.write_text(s, encoding="utf-8")
def need(cond, msg):
    if not cond: sys.exit("PATCH FAILED: " + msg)

# 1. copy new files (backing up the old invoices page once)
inv = src / "app/(protected)/invoices/page.tsx"
if inv.exists() and "InvoicesView" not in read(inv):
    shutil.copy(inv, inv.with_name("page.tsx.bak"))
for f in (pkg / "frontend/src").rglob("*"):
    if f.is_file():
        dest = src / f.relative_to(pkg / "frontend/src")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, dest)

# 2. globals.css: import tokens, replace Arial with the Inter stack
g = src / "app/globals.css"; s = read(g)
if "nexease-ui.css" not in s:
    need(s.startswith('@import "tailwindcss";'), 'globals.css should start with @import "tailwindcss";')
    s = s.replace('@import "tailwindcss";', '@import "tailwindcss";\n@import "../styles/nexease-ui.css";', 1)
s = s.replace("Arial,Helvetica,sans-serif", "var(--nx-font)")
write(g, s)

# 3. app-shell: mount floating create button + command palette
p = src / "components/layout/app-shell.tsx"; s = read(p)
if "QuickCreate" not in s:
    need("<Assistant/><NexFeedback/>" in s, "app-shell.tsx: <Assistant/><NexFeedback/> not found")
    s = s.replace('import Assistant from "@/features/saas/assistant";',
        'import Assistant from "@/features/saas/assistant";\nimport QuickCreate from "@/components/layout/quick-create";\nimport CommandPalette from "@/components/layout/command-palette";', 1)
    s = s.replace("<Assistant/><NexFeedback/>", '<Assistant/><NexFeedback/><QuickCreate variant="fab"/><CommandPalette/>', 1)
    write(p, s)

# 4. app-header: desktop Create menu + search trigger before the notification bell
p = src / "components/layout/app-header.tsx"; s = read(p)
if "QuickCreate" not in s:
    need("<NotificationMenu/>" in s, "app-header.tsx: <NotificationMenu/> not found")
    s = s.replace("import NotificationMenu from", 'import QuickCreate from \'@/components/layout/quick-create\';\nimport {CommandPaletteTrigger} from \'@/components/layout/command-palette\';\nimport NotificationMenu from', 1)
    s = s.replace("<NotificationMenu/>", '<CommandPaletteTrigger/><QuickCreate variant="header"/><NotificationMenu/>', 1)
    write(p, s)

# 5. dashboard: replace the dark hero with the new overview (KPI grid and charts are kept)
p = src / "features/dashboard/components/dashboard-shell.tsx"; s = read(p)
if "DashboardOverview" not in s:
    s, n = re.subn(r'<section className="relative overflow-hidden rounded-3xl bg-slate-950.*?</section>',
                   '<DashboardOverview data={dashboard} isLoading={isLoading} />', s, count=1, flags=re.S)
    need(n == 1, "dashboard-shell.tsx: hero <section> not found")
    kpi_import = 'import DashboardKPIGrid from "@/features/dashboard/components/dashboard-kpi-grid";'
    need(kpi_import in s, "dashboard-shell.tsx: KPI grid import not found")
    s = s.replace(kpi_import, kpi_import + '\nimport DashboardOverview from "@/features/dashboard/components/dashboard-overview";', 1)
    s = s.replace("bg-[#f3f6fa]", "bg-[var(--nx-surface-muted)]")
    write(p, s)

print("UI overhaul applied. Old invoices page saved as page.tsx.bak. Next: npm run test:run && npm run build")
