"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Capacitor } from "@capacitor/core";
import { ChevronLeft, ChevronRight, ClipboardList, Download, FilePlus2, FileSpreadsheet, FileText, MessageCircle, Plus, Share2 } from "lucide-react";
import { ActionIcon, CompactList, CompactRow, ListScreen, ListState, type ListAction } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import InvoiceDialog from "@/features/invoices/components/invoice-dialog";
import { quotationState, type Quotation } from "@/features/invoices/quotation";
import SalesOrderDialog from "@/features/sales-orders/components/sales-order-dialog";
import { apiBinaryRequest, apiRequest } from "@/lib/api/client";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadBlob } from "@/lib/browser/download";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate, formatMoney } from "@/lib/format";

export default function Quotations() {
  const { authentication } = useAuth();
  const can = (key: string) => hasPermission(authentication?.role.permissions ?? [], key);
  const native = Capacitor.isNativePlatform();
  const [page, setPage] = useState(1);
  const [openNumber, setOpenNumber] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [order, setOrder] = useState<Quotation>();
  const [invoice, setInvoice] = useState<Quotation>();
  const [sharing, setSharing] = useState("");

  const query = useQuery({
    queryKey: ["quotations", page],
    queryFn: async () => (await apiRequest<{ rows: Quotation[]; more: boolean }>(`/business/quotations/?page=${page}`)).data,
  });
  const rows = query.data?.rows ?? [];

  async function pdf(number: string) {
    setSharing(number);
    try {
      const { blob } = await apiBinaryRequest(`/business/quotations/${encodeURIComponent(number)}/pdf/`);
      await downloadBlob(blob, number + ".pdf");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Unable to prepare quotation PDF.", "error");
    } finally {
      setSharing("");
    }
  }

  function rowActions(q: Quotation): ListAction[] {
    const actions: ListAction[] = [{ icon: native ? Share2 : Download, label: `${native ? "Share" : "Download"} PDF ${q.number}`, busy: sharing === q.number, onClick: () => void pdf(q.number) }];
    if (!native) {
      const text = `Quotation ${q.number} for ${formatMoney(q.total)}${q.valid_until ? `, valid until ${formatDate(q.valid_until)}` : ""}.`;
      actions.push({ icon: MessageCircle, label: `WhatsApp ${q.number}`, onClick: () => window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener,noreferrer") });
    }
    return actions;
  }

  function exportCsv() {
    void downloadCsv(`NexEase-quotations-page-${page}`, rows, [
      { header: "Quotation", value: (q) => q.number },
      { header: "Customer", value: (q) => q.customer },
      { header: "Date", value: (q) => q.date },
      { header: "Valid until", value: (q) => q.valid_until },
      { header: "Status", value: (q) => quotationState(q).label },
      { header: "Converted to", value: (q) => q.conversion?.number ?? "" },
      { header: "Total", value: (q) => q.total },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Quotations"
        subtitle="Estimates you can turn into an order or invoice in one tap."
        primary={can("invoices.create") ? { label: "New quotation", icon: Plus, onClick: () => setCreateOpen(true) } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !rows.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        footer={
          page > 1 || query.data?.more ? (
            <footer className="nxl-pager">
              <span>Page {page}</span>
              <span className="flex gap-1.5">
                <ActionIcon icon={ChevronLeft} label="Previous page" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)} />
                <ActionIcon icon={ChevronRight} label="Next page" size="sm" disabled={!query.data?.more} onClick={() => setPage(page + 1)} />
              </span>
            </footer>
          ) : null
        }
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!rows.length}
          emptyIcon={FileText}
          emptyTitle="No quotations yet"
          emptyDescription="Send a price estimate, then convert it when the customer agrees."
          emptyAction={can("invoices.create") ? <button type="button" className="nx-button" onClick={() => setCreateOpen(true)}><Plus size={16} />New quotation</button> : null}
        >
          <CompactList label="Quotations" columns={[{ label: "Customer / quotation" }, { label: "Valid until" }, { label: "Items" }, { label: "Total" }]}>
            {rows.map((q) => {
              const state = quotationState(q);
              const expanded = openNumber === q.number;
              return (
                <CompactRow
                  key={q.number}
                  openLabel={`${expanded ? "Hide" : "Show"} quotation ${q.number}`}
                  onOpen={() => setOpenNumber(expanded ? null : q.number)}
                  expanded={expanded}
                  title={q.customer}
                  subtitle={`${q.number} · ${formatDate(q.date)}`}
                  meta={[formatDate(q.valid_until), `${q.items.length} item${q.items.length === 1 ? "" : "s"}`]}
                  amount={formatMoney(q.total)}
                  badge={<Badge tone={state.tone}>{state.label}</Badge>}
                  actions={rowActions(q)}
                >
                  <ul className="divide-y text-sm" style={{ borderColor: "var(--nx-border)" }}>
                    {q.items.map((line, i) => (
                      <li key={i} className="flex justify-between gap-4 py-2">
                        <div className="min-w-0">
                          <strong className="block break-words">{line.name}</strong>
                          <span className="nx-muted text-xs">
                            {line.quantity} × {formatMoney(line.unit_price)} · GST {line.tax_rate}%{Number(line.discount) > 0 ? ` · Discount ${formatMoney(line.discount)}` : ""}
                          </span>
                        </div>
                        <span className="tabular-nums">{formatMoney(line.total)}</span>
                      </li>
                    ))}
                  </ul>
                  {q.notes ? <p className="nx-muted my-2 whitespace-pre-wrap text-sm">{q.notes}</p> : null}
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    {q.conversion?.id ? (
                      <Link className="nx-button nx-secondary nx-btn-sm" href={`/${q.conversion.kind === "order" ? "sales-orders" : "invoices"}?view=${q.conversion.id}`}>View {q.conversion.number}</Link>
                    ) : q.conversion ? (
                      <span className="nx-muted text-sm">Conversion in progress or awaiting review.</span>
                    ) : (
                      <>
                        {can("invoices.create") ? <button type="button" className="nx-button nx-btn-sm" onClick={() => setInvoice(q)}><FilePlus2 size={15} />Convert to invoice</button> : null}
                        {can("sales_orders.create") ? <button type="button" className="nx-button nx-secondary nx-btn-sm" onClick={() => setOrder(q)}><ClipboardList size={15} />Convert to order</button> : null}
                      </>
                    )}
                    {q.linked_invoice ? <Link className="nx-button nx-secondary nx-btn-sm" href={`/invoices?view=${q.linked_invoice.id}`}>View invoice {q.linked_invoice.number}</Link> : null}
                  </div>
                </CompactRow>
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>

      <InvoiceDialog quotation initialMode="direct" open={createOpen} onClose={() => { setCreateOpen(false); void query.refetch(); }} />
      {invoice ? <InvoiceDialog sourceQuote={invoice} initialMode="direct" open onClose={() => { setInvoice(undefined); void query.refetch(); }} /> : null}
      {order ? (
        <SalesOrderDialog sourceQuote={order} salesOrderId={null} open canCreateCustomer={can("customers.create")} canCreateProduct={can("products.create")} onClose={() => { setOrder(undefined); void query.refetch(); }} />
      ) : null}
    </>
  );
}
