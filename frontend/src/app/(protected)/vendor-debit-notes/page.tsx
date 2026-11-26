"use client";

import { useState } from "react";
import { FileSpreadsheet, Plus, ReceiptText } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, StatusBadge, useDebounced } from "@/components/list/list-kit";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import SearchSelect from "@/components/search-select";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { useSupplierList } from "@/features/suppliers/hooks";
import { useDocumentRowActions } from "@/features/documents/components/document-row-actions";
import { debitNoteStatus } from "@/features/purchase/status";
import { statusChips } from "@/features/sales/status";
import VendorDebitNoteDetailDialog from "@/features/vendor-debit-notes/components/vendor-debit-note-detail-dialog";
import VendorDebitNoteDialog from "@/features/vendor-debit-notes/components/vendor-debit-note-dialog";
import { useVendorDebitNoteList } from "@/features/vendor-debit-notes/hooks";
import type { VendorDebitNoteStatus } from "@/features/vendor-debit-notes/types";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate, formatMoney } from "@/lib/format";

const tabs = statusChips(debitNoteStatus);
const sorts = [
  ["-debit_note_date", "Newest first"],
  ["debit_note_date", "Oldest first"],
  ["-total_amount", "Highest amount"],
  ["-remaining_credit", "Highest remaining credit"],
  ["debit_note_number", "Debit note number"],
] as const;

export default function VendorDebitNotesPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "vendor_debit_notes.read");
  const canCreate = hasPermission(permissions, "vendor_debit_notes.create");

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [supplierId, setSupplierId] = useState("");
  const [status, setStatus] = useState<VendorDebitNoteStatus | "">("");
  const [sort, setSort] = useState<string>("-debit_note_date");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);
  const docs = useDocumentRowActions();

  const suppliers = useSupplierList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.suppliers ?? [];
  const query = useVendorDebitNoteList({ page, page_size: 25, supplier_id: supplierId || undefined, status: status || undefined, search: search || undefined, sort });
  const notes = query.data?.vendor_debit_notes ?? [];

  if (!authentication) return null;
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={ReceiptText} title="Debit notes unavailable" description="You do not have permission to view supplier debit notes." /></div>;
  }
  const filtered = Boolean(search || status || supplierId);

  function exportCsv() {
    void downloadCsv(`NexEase-debit-notes-page-${page}`, notes, [
      { header: "Debit note", value: (r) => r.debit_note_number },
      { header: "Supplier", value: (r) => r.supplier.name },
      { header: "Bill", value: (r) => r.vendor_bill?.bill_number },
      { header: "Purchase return", value: (r) => r.purchase_return?.return_number },
      { header: "Date", value: (r) => r.debit_note_date?.slice(0, 10) },
      { header: "Status", value: (r) => debitNoteStatus[r.status]?.label ?? r.status },
      { header: "Total", value: (r) => r.total_amount },
      { header: "Applied", value: (r) => r.applied_amount },
      { header: "Remaining", value: (r) => r.remaining_credit },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Debit notes"
        primary={canCreate ? { label: "New debit note", icon: Plus, onClick: () => setCreateOpen(true) } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !notes.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search debit note no. or notes" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(supplierId) || sort !== "-debit_note_date"}
        chips={{ options: tabs, value: status, label: "Filter by status", onChange: (v) => { setStatus(v); setPage(1); } }}
        footer={<Pager pagination={query.data?.pagination} noun="debit notes" onPage={setPage} />}
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!notes.length}
          emptyIcon={ReceiptText}
          emptyTitle={filtered ? "No debit notes match these filters" : "No debit notes yet"}
          emptyDescription={filtered ? "Try a different search or clear the filters." : "Create one from a confirmed purchase return to reduce what you owe the supplier."}
        >
          <CompactList label="Debit notes" columns={[{ label: "Supplier / debit note" }, { label: "Bill" }, { label: "Applied", align: "end" }, { label: "Remaining" }]}>
            {notes.map((r) => (
              <CompactRow
                key={r.id}
                openLabel={`View debit note ${r.debit_note_number}`}
                onOpen={() => setDetailId(r.id)}
                title={r.supplier.name}
                subtitle={`${r.debit_note_number} · ${formatDate(r.debit_note_date)}`}
                meta={[r.vendor_bill?.bill_number ?? "—", <span key="applied" className="block text-right tabular-nums">{formatMoney(r.applied_amount)}</span>]}
                amount={formatMoney(r.remaining_credit)}
                amountHint={`of ${formatMoney(r.total_amount)}`}
                badge={<StatusBadge status={r.status} map={debitNoteStatus} />}
                actions={r.status === "DRAFT" ? [] : docs.actionsFor({ documentType: "VENDOR_DEBIT_NOTE", documentId: r.id, documentNumber: r.debit_note_number, recipient: r.supplier.email })}
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
        <button type="button" className="nx-button nx-secondary" onClick={() => { setSupplierId(""); setSort("-debit_note_date"); setSearchInput(""); setStatus(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>

      {docs.dialog}
      <VendorDebitNoteDialog open={createOpen} onClose={() => setCreateOpen(false)} onCreated={(id) => { setCreateOpen(false); setDetailId(id); }} />
      <VendorDebitNoteDetailDialog
        open={detailId !== null}
        debitNoteId={detailId}
        canIssue={hasPermission(permissions, "vendor_debit_notes.issue")}
        canCancel={hasPermission(permissions, "vendor_debit_notes.cancel")}
        onClose={() => setDetailId(null)}
        onChanged={() => void query.refetch()}
      />
    </>
  );
}
