"use client";

import { useState } from "react";
import { FileSpreadsheet, Plus, RotateCcw } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, StatusBadge, useDebounced } from "@/components/list/list-kit";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import SearchSelect from "@/components/search-select";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { useCustomerList } from "@/features/customers/hooks";
import { salesReturnStatus, statusChips } from "@/features/sales/status";
import SalesReturnDetailDialog from "@/features/sales-returns/components/sales-return-detail-dialog";
import SalesReturnDialog from "@/features/sales-returns/components/sales-return-dialog";
import { useSalesReturnList } from "@/features/sales-returns/hooks";
import type { SalesReturnStatus } from "@/features/sales-returns/types";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate, formatMoney } from "@/lib/format";

const tabs = statusChips(salesReturnStatus);
const sorts = [
  ["-return_date", "Newest first"],
  ["return_date", "Oldest first"],
  ["-total_amount", "Highest amount"],
  ["return_number", "Return number"],
] as const;

export default function SalesReturnsPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "sales_returns.read");
  const canCreate = hasPermission(permissions, "sales_returns.create");

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [customerId, setCustomerId] = useState("");
  const [status, setStatus] = useState<SalesReturnStatus | "">("");
  const [sort, setSort] = useState<string>("-return_date");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);

  const customers = useCustomerList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.customers ?? [];
  const query = useSalesReturnList({ page, page_size: 25, customer_id: customerId || undefined, status: status || undefined, search: search || undefined, sort });
  const returns = query.data?.sales_returns ?? [];

  if (!authentication) return null;
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={RotateCcw} title="Sales returns unavailable" description="You do not have permission to view sales returns." /></div>;
  }
  const filtered = Boolean(search || status || customerId);

  function exportCsv() {
    void downloadCsv(`NexEase-sales-returns-page-${page}`, returns, [
      { header: "Return", value: (r) => r.return_number },
      { header: "Customer", value: (r) => r.customer.name },
      { header: "Invoice", value: (r) => r.invoice?.invoice_number },
      { header: "Sales order", value: (r) => r.sales_order?.so_number },
      { header: "Date", value: (r) => r.return_date?.slice(0, 10) },
      { header: "Status", value: (r) => salesReturnStatus[r.status]?.label ?? r.status },
      { header: "Total", value: (r) => r.total_amount },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Sales returns"
        primary={canCreate ? { label: "New return", icon: Plus, onClick: () => setCreateOpen(true) } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !returns.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search return no. or notes" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(customerId) || sort !== "-return_date"}
        chips={{ options: tabs, value: status, label: "Filter by status", onChange: (v) => { setStatus(v); setPage(1); } }}
        footer={<Pager pagination={query.data?.pagination} noun="returns" onPage={setPage} />}
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!returns.length}
          emptyIcon={RotateCcw}
          emptyTitle={filtered ? "No returns match these filters" : "No sales returns yet"}
          emptyDescription={filtered ? "Try a different search or clear the filters." : "Record goods a customer sends back against a delivered, invoiced order."}
        >
          <CompactList label="Sales returns" columns={[{ label: "Customer / return" }, { label: "Invoice" }, { label: "Sales order" }, { label: "Amount" }]}>
            {returns.map((r) => (
              <CompactRow
                key={r.id}
                openLabel={`View sales return ${r.return_number}`}
                onOpen={() => setDetailId(r.id)}
                title={r.customer.name}
                subtitle={`${r.return_number} · ${formatDate(r.return_date)}`}
                meta={[r.invoice?.invoice_number ?? "—", r.sales_order?.so_number ?? "—"]}
                amount={formatMoney(r.total_amount)}
                badge={<StatusBadge status={r.status} map={salesReturnStatus} />}
              />
            ))}
          </CompactList>
        </ListState>
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <label className="block">Customer
          <SearchSelect className="nx-input" value={customerId} onChange={(e) => { setCustomerId(e.target.value); setPage(1); }}>
            <option value="">All customers</option>
            {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </SearchSelect>
        </label>
        <label className="block">Sort by
          <select className="nx-input" value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }}>
            {sorts.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <button type="button" className="nx-button nx-secondary" onClick={() => { setCustomerId(""); setSort("-return_date"); setSearchInput(""); setStatus(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>

      <SalesReturnDialog open={createOpen} onClose={() => setCreateOpen(false)} onCreated={(id) => { setCreateOpen(false); setDetailId(id); }} />
      <SalesReturnDetailDialog
        open={detailId !== null}
        salesReturnId={detailId}
        canConfirm={hasPermission(permissions, "sales_returns.confirm")}
        canCancel={hasPermission(permissions, "sales_returns.cancel")}
        onClose={() => setDetailId(null)}
        onChanged={() => void query.refetch()}
      />
    </>
  );
}
