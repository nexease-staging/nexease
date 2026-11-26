"use client";

import { useMemo, useState, type FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ShoppingCart, Trash2 } from "lucide-react";
import { FieldHint, FormActions, FormSection, FormSheet } from "@/components/form/form-sheet";
import { notify } from "@/components/nex-feedback";
import SearchSelect from "@/components/search-select";
import { useSupplierList } from "@/features/suppliers/hooks";
import { apiRequest } from "@/lib/api/client";
import { formatMoney } from "@/lib/format";
import { groupBySupplier, type LowStockItem } from "../insights";

type Line = { item: LowStockItem; quantity: string; rate: string; gst: string };
const TWO_DECIMALS = /^\d+(\.\d{1,2})?$/;
const today = () => new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });

export function reorderProblem(lines: readonly Line[], supplierId: string): string {
  if (!supplierId) return "Choose the supplier for this purchase order.";
  if (!lines.length) return "Keep at least one item.";
  for (const l of lines) {
    if (!TWO_DECIMALS.test(l.quantity.trim()) || Number(l.quantity) <= 0) return `${l.item.name}: enter a quantity above 0 with up to 2 decimals.`;
    if (!TWO_DECIMALS.test(l.rate.trim())) return `${l.item.name}: enter a rate with up to 2 decimals.`;
    if (!TWO_DECIMALS.test(l.gst.trim()) || Number(l.gst) > 100) return `${l.item.name}: GST must be between 0 and 100.`;
  }
  return "";
}

export default function ReorderSheet({ items, onClose, onCreated }: { items: LowStockItem[]; onClose: () => void; onCreated?: (poNumber: string) => void }) {
  const qc = useQueryClient();
  const suppliers = useSupplierList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.suppliers ?? [];
  const firstGroup = useMemo(() => groupBySupplier(items)[0], [items]);
  const [supplierId, setSupplierId] = useState(firstGroup?.supplier?.id ?? "");
  const [lines, setLines] = useState<Line[]>(() =>
    items.map((item) => ({
      item,
      quantity: Number(item.suggested_quantity) > 0 ? item.suggested_quantity : item.reorder_level,
      rate: item.supplier && Number(item.supplier.last_rate) > 0 ? item.supplier.last_rate : item.cost_price,
      gst: "0",
    })),
  );
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const supplier = suppliers.find((s) => s.id === supplierId);
  const total = lines.reduce((sum, l) => sum + Number(l.quantity || 0) * Number(l.rate || 0) * (1 + Number(l.gst || 0) / 100), 0);
  const otherSuppliers = new Set(items.filter((i) => i.supplier && i.supplier.id !== supplierId).map((i) => i.supplier!.name));

  async function submit(e: FormEvent) {
    e.preventDefault();
    const problem = reorderProblem(lines, supplierId);
    if (problem) { setMessage(problem); return; }
    if (!supplier) { setMessage("Choose the supplier for this purchase order."); return; }
    setBusy(true);
    setMessage("");
    try {
      const r = await apiRequest<{ number: string }>("/business/quick-purchases/", {
        method: "POST",
        body: {
          kind: "purchase_order",
          number: "",
          date: today(),
          supplier: { code: supplier.code, name: supplier.name },
          items: lines.map((l) => ({ sku: l.item.sku, name: l.item.name, unit: l.item.unit, quantity: l.quantity.trim(), unit_price: l.rate.trim(), tax_rate: l.gst.trim(), discount: "0" })),
        },
      });
      await qc.invalidateQueries();
      notify(`Draft purchase order ${r.data.number} created for ${supplier.name}.`);
      onCreated?.(r.data.number);
      onClose();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create the purchase order.");
    } finally {
      setBusy(false);
    }
  }

  const patch = (i: number, p: Partial<Line>) => setLines((prev) => prev.map((l, j) => (j === i ? { ...l, ...p } : l)));

  return (
    <FormSheet title="Reorder stock" subtitle="Creates a draft purchase order you can review before sending." onClose={onClose} busy={busy} size="lg">
      <form onSubmit={submit}>
        <FormSection title="Supplier" icon={ShoppingCart}>
          <label>Supplier *
            <SearchSelect value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
              <option value="">Choose supplier</option>
              {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name} · {s.code}</option>)}
            </SearchSelect>
          </label>
          {firstGroup?.supplier ? <FieldHint>Pre-selected from the last purchase order for these items ({firstGroup.supplier.last_po}).</FieldHint> : <FieldHint>No earlier purchase order found for these items.</FieldHint>}
          {otherSuppliers.size ? <FieldHint>Some items were last bought from {[...otherSuppliers].join(", ")}. Remove them to order separately.</FieldHint> : null}
        </FormSection>

        <FormSection title={`Items (${lines.length})`}>
          <div className="nxf-lines">
            {lines.map((l, i) => (
              <div key={l.item.product_id} className="nxf-reorder-line">
                <div className="min-w-0">
                  <strong className="block truncate text-sm">{l.item.name}</strong>
                  <span className="nxf-field-hint">{l.item.sku} · available {l.item.available} {l.item.unit} · reorder at {l.item.reorder_level}</span>
                </div>
                <label>Qty<input aria-label={`quantity ${l.item.sku}`} inputMode="decimal" value={l.quantity} onChange={(e) => patch(i, { quantity: e.target.value })} /></label>
                <label>Rate ₹<input aria-label={`rate ${l.item.sku}`} inputMode="decimal" value={l.rate} onChange={(e) => patch(i, { rate: e.target.value })} /></label>
                <label>GST %<input aria-label={`gst ${l.item.sku}`} inputMode="decimal" value={l.gst} onChange={(e) => patch(i, { gst: e.target.value })} /></label>
                <button type="button" className="nxf-close" aria-label={`Remove ${l.item.name}`} disabled={lines.length === 1} onClick={() => setLines((prev) => prev.filter((_, j) => j !== i))}><Trash2 size={17} /></button>
              </div>
            ))}
          </div>
        </FormSection>

        {message ? <p role="alert" className="nxf-error">{message}</p> : null}
        <FormActions total={formatMoney(total)}>
          <button type="button" className="nx-button nx-secondary nxf-secondary-sm" disabled={busy} onClick={onClose}>Cancel</button>
          <button className="nx-button" disabled={busy}>{busy ? "Creating…" : "Create draft PO"}</button>
        </FormActions>
      </form>
    </FormSheet>
  );
}
