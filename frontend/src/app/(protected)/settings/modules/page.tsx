import { ModuleSettings, BooksTools, AccountantExport } from "@/features/business/pro-panels";

export default function Page() {
  return (
    <div className="nxl-screen">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Business modules & books</h1>
          <p className="nx-muted">Turn modules on or off, prepare system accounts, and export data for your accountant.</p>
        </div>
      </header>
      <div className="space-y-4">
        <ModuleSettings />
        <BooksTools />
        <AccountantExport />
      </div>
    </div>
  );
}
