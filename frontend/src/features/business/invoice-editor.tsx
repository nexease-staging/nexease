"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";
import NexDialog from "@/components/nex-dialog";
import { confirmAction, notify } from "@/components/nex-feedback";
import { getConfig } from "./workspace";
type Row = {
  product_id: string;
  name: string;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  description: string;
  show_description: boolean;
};
type Draft = {
  version: string;
  invoice_date: string;
  due_date: string;
  billing_name: string;
  billing_address: string;
  notes: string;
  items: Row[];
};
export default function InvoiceEditor({ id }: { id: string }) {
  const qc = useQueryClient();
  const config = useQuery({
    queryKey: ["business-config"],
    queryFn: getConfig,
  });
  const [draft, setDraft] = useState<Draft | null>(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const products = useQuery({
    queryKey: ["invoice-amendment-products", search],
    queryFn: async () =>
      (
        await apiRequest<{
          products: {
            id: string;
            name: string;
            selling_price: string;
            item_type?: string;
          }[];
        }>(
          `/products/?page_size=100&is_active=true&search=${encodeURIComponent(search)}`,
        )
      ).data,
    enabled: open,
  });
  if (!config.data?.can_edit_issued_invoices) return null;
  async function load() {
    setOpen(true);
    setError("");
    setBusy(true);
    try {
      setDraft(
        (await apiRequest<Draft>(`/business/invoices/${id}/edit/`)).data,
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button
        className="nx-button nx-secondary my-3"
        onClick={() => void load()}
      >
        Edit invoice amounts & details
      </button>
      {open && (
        <NexDialog
          title="Admin invoice amendment"
          busy={busy}
          onClose={() => {
            setOpen(false);
            setDraft(null);
          }}
        >
          {error && (
            <p role="alert" className="mb-4 text-red-700">
              {error}
            </p>
          )}
          {draft && (
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (
                  !(await confirmAction(
                    "Save this invoice amendment? Amounts, outstanding balance and accounting adjustments will be recorded.",
                  ))
                )
                  return;
                setBusy(true);
                setError("");
                try {
                  await apiRequest(`/business/invoices/${id}/edit/`, {
                    method: "POST",
                    body: draft,
                  });
                  await qc.invalidateQueries();
                  setOpen(false);
                  notify(
                    "Invoice amended. Balances and accounting were updated.",
                  );
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              <p className="mb-4 text-sm text-slate-500">
                Submitted e-invoices and e-way bills remain locked. Sales-order
                quantities must follow fulfillment corrections. Payments already
                applied are preserved.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {(
                  [
                    "invoice_date",
                    "due_date",
                    "billing_name",
                    "billing_address",
                    "notes",
                  ] as const
                ).map((key) => (
                  <label key={key} className="text-sm capitalize">
                    {key.replaceAll("_", " ")}
                    <input
                      className="nx-input"
                      type={key.endsWith("date") ? "date" : "text"}
                      value={draft[key]}
                      onChange={(e) =>
                        setDraft({ ...draft, [key]: e.target.value })
                      }
                    />
                  </label>
                ))}
              </div>
              <div className="my-5 space-y-4">
                {draft.items.map((row, index) => (
                  <fieldset key={index} className="rounded-xl border p-3">
                    <legend>{row.name}</legend>
                    <div className="grid grid-cols-2 gap-3">
                      {(
                        [
                          "quantity",
                          "unit_price",
                          "tax_rate",
                          "discount",
                        ] as const
                      ).map((key) => (
                        <label key={key} className="text-sm capitalize">
                          {key.replaceAll("_", " ")}
                          <input
                            className="nx-input"
                            type="number"
                            step="0.01"
                            min={key === "quantity" ? "0.01" : "0"}
                            required
                            value={row[key]}
                            onChange={(e) =>
                              setDraft({
                                ...draft,
                                items: draft.items.map((r, i) =>
                                  i === index
                                    ? { ...r, [key]: e.target.value }
                                    : r,
                                ),
                              })
                            }
                          />
                        </label>
                      ))}
                    </div>
                    <div className="mt-3 flex gap-3">
                      <label className="flex gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={row.show_description}
                          onChange={(e) =>
                            setDraft({
                              ...draft,
                              items: draft.items.map((r, i) =>
                                i === index
                                  ? { ...r, show_description: e.target.checked }
                                  : r,
                              ),
                            })
                          }
                        />
                        Print description
                      </label>
                      <button
                        type="button"
                        className="text-sm text-red-700 underline"
                        disabled={draft.items.length === 1}
                        onClick={() =>
                          setDraft({
                            ...draft,
                            items: draft.items.filter((_, i) => i !== index),
                          })
                        }
                      >
                        Remove line
                      </button>
                    </div>
                    <label className="mt-3 block text-sm">
                      Description
                      <input
                        className="nx-input"
                        value={row.description}
                        onChange={(e) =>
                          setDraft({
                            ...draft,
                            items: draft.items.map((r, i) =>
                              i === index
                                ? { ...r, description: e.target.value }
                                : r,
                            ),
                          })
                        }
                      />
                    </label>
                  </fieldset>
                ))}
              </div>
              <div className="mb-4 rounded-xl border p-3">
                <label className="text-sm">
                  Add a product
                  <input
                    className="nx-input"
                    placeholder="Search active products"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </label>
                <select
                  className="nx-input"
                  aria-label="Product to add"
                  value=""
                  onChange={(e) => {
                    const p = products.data?.products.find(
                      (x) => x.id === e.target.value,
                    );
                    if (p)
                      setDraft({
                        ...draft,
                        items: [
                          ...draft.items,
                          {
                            product_id: p.id,
                            name: p.name,
                            quantity: "1",
                            unit_price: p.selling_price,
                            tax_rate: "0",
                            discount: "0",
                            description: "",
                            show_description: false,
                          },
                        ],
                      });
                  }}
                >
                  <option value="">Choose product to add a line</option>
                  {products.data?.products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
                <p className="mt-2 text-xs text-slate-500">
                  Review the tax rate on every added line.
                </p>
              </div>
              <button disabled={busy} className="nx-button">
                Save invoice amendment
              </button>
            </form>
          )}
          {busy && !draft && <p role="status">Loading invoice…</p>}
        </NexDialog>
      )}
    </>
  );
}
