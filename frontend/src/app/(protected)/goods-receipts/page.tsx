"use client";

import { useState } from "react";
import { FileSpreadsheet, PackageCheck, Plus } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, useDebounced } from "@/components/list/list-kit";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { useDocumentRowActions } from "@/features/documents/components/document-row-actions";
import GoodsReceiptDetailDialog from "@/features/goods-receipts/components/goods-receipt-detail-dialog";
import GoodsReceiptDialog from "@/features/goods-receipts/components/goods-receipt-dialog";
import { useGoodsReceiptList } from "@/features/goods-receipts/hooks";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate } from "@/lib/format";

const sorts = [
  ["-created_at", "Newest first"],
  ["created_at", "Oldest first"],
  ["-received_at", "Received (latest)"],
  ["received_at", "Received (earliest)"],
  ["grn_number", "GRN number"],
] as const;

export default function GoodsReceiptsPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "goods_receipts.read");
  const canCreate = hasPermission(permissions, "goods_receipts.create");

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [sort, setSort] = useState<string>("-created_at");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);
  const docs = useDocumentRowActions();

  const query = useGoodsReceiptList({ page, page_size: 25, search: search || undefined, sort });
  const receipts = query.data?.goods_receipts ?? [];

  if (!authentication) return null;
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={PackageCheck} title="Goods receipts unavailable" description="You do not have permission to view goods receipts." /></div>;
  }

  function exportCsv() {
    void downloadCsv(`NexEase-goods-receipts-page-${page}`, receipts, [
      { header: "GRN", value: (r) => r.grn_number },
      { header: "Supplier", value: (r) => r.supplier.name },
      { header: "PO", value: (r) => r.purchase_order?.po_number },
      { header: "Warehouse", value: (r) => r.warehouse?.name },
      { header: "Received", value: (r) => r.received_at?.slice(0, 10) },
      { header: "Items", value: (r) => r.item_count },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Goods receipts"
        subtitle="Stock received against purchase orders."
        primary={canCreate ? { label: "Receive goods", icon: Plus, onClick: () => setCreateOpen(true) } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !receipts.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search GRN or PO number" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={sort !== "-created_at"}
        footer={<Pager pagination={query.data?.pagination} noun="receipts" onPage={setPage} />}
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!receipts.length}
          emptyIcon={PackageCheck}
          emptyTitle={search ? "No receipts match" : "No goods received yet"}
          emptyDescription={search ? "Try a different number." : "Receive stock against a confirmed purchase order to update inventory."}
          emptyAction={canCreate && !search ? <button type="button" className="nx-button" onClick={() => setCreateOpen(true)}><Plus size={16} />Receive goods</button> : null}
        >
          <CompactList label="Goods receipts" columns={[{ label: "Supplier / GRN" }, { label: "PO" }, { label: "Warehouse" }, { label: "Items" }]}>
            {receipts.map((r) => (
              <CompactRow
                key={r.id}
                openLabel={`View goods receipt ${r.grn_number}`}
                onOpen={() => setDetailId(r.id)}
                title={r.supplier.name}
                subtitle={`${r.grn_number} · ${formatDate(r.received_at)}`}
                meta={[r.purchase_order?.po_number ?? "—", r.warehouse?.name ?? "—"]}
                amount={<span className="text-[13px] font-semibold">{r.item_count} item{r.item_count === 1 ? "" : "s"}</span>}
                actions={docs.actionsFor({ documentType: "GOODS_RECEIPT", documentId: r.id, documentNumber: r.grn_number, recipient: r.supplier.email }, { email: false })}
              />
            ))}
          </CompactList>
        </ListState>
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <label className="block">Sort by
          <select className="nx-input" value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }}>
            {sorts.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <button type="button" className="nx-button nx-secondary" onClick={() => { setSort("-created_at"); setSearchInput(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>

      {docs.dialog}
      <GoodsReceiptDialog open={createOpen} onClose={() => setCreateOpen(false)} onCreated={(id) => { setCreateOpen(false); setDetailId(id); }} />
      <GoodsReceiptDetailDialog open={detailId !== null} goodsReceiptId={detailId ?? ""} onClose={() => setDetailId(null)} />
    </>
  );
}
