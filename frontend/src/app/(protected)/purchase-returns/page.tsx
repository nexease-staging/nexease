"use client";

import { useState } from "react";
import { FileSpreadsheet, Plus, Undo2 } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, StatusBadge, useDebounced } from "@/components/list/list-kit";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import SearchSelect from "@/components/search-select";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { useSupplierList } from "@/features/suppliers/hooks";
import { purchaseReturnStatus } from "@/features/purchase/status";
import { statusChips } from "@/features/sales/status";
import PurchaseReturnDetailDialog from "@/features/purchase-returns/components/purchase-return-detail-dialog";
import PurchaseReturnDialog from "@/features/purchase-returns/components/purchase-return-dialog";
import { usePurchaseReturnList } from "@/features/purchase-returns/hooks";
import type { PurchaseReturnStatus } from "@/features/purchase-returns/types";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate, formatMoney } from "@/lib/format";

const tabs = statusChips(purchaseReturnStatus);
const sorts = [
  ["-return_date", "Newest first"],
  ["return_date", "Oldest first"],
  ["-total_amount", "Highest amount"],
  ["return_number", "Return number"],
] as const;

export default function PurchaseReturnsPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "purchase_returns.read");
  const canCreate = hasPermission(permissions, "purchase_returns.create");

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [supplierId, setSupplierId] = useState("");
  const [status, setStatus] = useState<PurchaseReturnStatus | "">("");
  const [sort, setSort] = useState<string>("-return_date");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);

  const suppliers = useSupplierList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.suppliers ?? [];
  const query = usePurchaseReturnList({ page, page_size: 25, supplier_id: supplierId || undefined, status: status || undefined, search: search || undefined, sort });
  const returns = query.data?.purchase_returns ?? [];

  if (!authentication) return null;
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={Undo2} title="Purchase returns unavailable" description="You do not have permission to view purchase returns." /></div>;
  }
  const filtered = Boolean(search || status || supplierId);

  function exportCsv() {
    void downloadCsv(`NexEase-purchase-returns-page-${page}`, returns, [
      { header: "Return", value: (r) => r.return_number },
      { header: "Supplier", value: (r) => r.supplier.name },
      { header: "Bill", value: (r) => r.vendor_bill?.bill_number },
      { header: "PO", value: (r) => r.purchase_order?.po_number },
      { header: "Date", value: (r) => r.return_date?.slice(0, 10) },
      { header: "Status", value: (r) => purchaseReturnStatus[r.status]?.label ?? r.status },
      { header: "Total", value: (r) => r.total_amount },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Purchase returns"
        primary={canCreate ? { label: "New return", icon: Plus, onClick: () => setCreateOpen(true) } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !returns.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search return no. or notes" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(supplierId) || sort !== "-return_date"}
        chips={{ options: tabs, value: status, label: "Filter by status", onChange: (v) => { setStatus(v); setPage(1); } }}
        footer={<Pager pagination={query.data?.pagination} noun="returns" onPage={setPage} />}
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!returns.length}
          emptyIcon={Undo2}
          emptyTitle={filtered ? "No returns match these filters" : "No purchase returns yet"}
          emptyDescription={filtered ? "Try a different search or clear the filters." : "Record goods you send back to a supplier against a received, billed order."}
        >
          <CompactList label="Purchase returns" columns={[{ label: "Supplier / return" }, { label: "Bill" }, { label: "PO" }, { label: "Amount" }]}>
            {returns.map((r) => (
              <CompactRow
                key={r.id}
                openLabel={`View purchase return ${r.return_number}`}
                onOpen={() => setDetailId(r.id)}
                title={r.supplier.name}
                subtitle={`${r.return_number} · ${formatDate(r.return_date)}`}
                meta={[r.vendor_bill?.bill_number ?? "—", r.purchase_order?.po_number ?? "—"]}
                amount={formatMoney(r.total_amount)}
                badge={<StatusBadge status={r.status} map={purchaseReturnStatus} />}
              />
            ))}
          </CompactList>
        </ListState>
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <label className="block">Supplier
          <SearchSelect className="nx-input" value={supplierId} onChange={(e) => { setSupplierId(e.target.value); setPage(1); }}>
            <option value="">All suppliers</option>
            {suppliers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </SearchSelect>
        </label>
        <label className="block">Sort by
          <select className="nx-input" value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }}>
            {sorts.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <button type="button" className="nx-button nx-secondary" onClick={() => { setSupplierId(""); setSort("-return_date"); setSearchInput(""); setStatus(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>

      <PurchaseReturnDialog open={createOpen} onClose={() => setCreateOpen(false)} onCreated={(id) => { setCreateOpen(false); setDetailId(id); }} />
      <PurchaseReturnDetailDialog
        open={detailId !== null}
        purchaseReturnId={detailId}
        canConfirm={hasPermission(permissions, "purchase_returns.confirm")}
        canCancel={hasPermission(permissions, "purchase_returns.cancel")}
        onClose={() => setDetailId(null)}
        onChanged={() => void query.refetch()}
      />
    </>
  );
}
