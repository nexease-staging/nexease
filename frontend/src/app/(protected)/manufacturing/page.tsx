"use client";
import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { exportWorkbook } from "@/features/business/workspace";
import Link from "next/link";
import SearchSelect from "@/components/search-select";
import { apiRequest } from "@/lib/api/client";
import { useAuth } from "@/features/auth/auth-context";
import { hasPermission } from "@/lib/authorization/permissions";

const root = "/business/manufacturing/";
type Material = {
  product: string;
  per_unit: string;
  name?: string;
  required?: string;
  issued?: string;
  unit?: string;
  value?: string;
  available?: string;
};
type Batch = {
  name: string;
  posted: boolean;
  accepted?: string;
  rejected?: string;
  cost?: string;
};
type Line = {
  batches?: Batch[];
  work_in_progress?: string;
  on_hand?: string;
  product: string;
  quantity: string;
  specification: string;
  estimated_expenses: string;
  materials: Material[];
  name?: string;
  accepted?: string;
  rejected?: string;
  estimate?: string;
  actual?: string;
  variance?: string;
  unit_cost?: string;
  pending?: string;
  unit?: string;
};
type Plan = {
  warehouse: string;
  sales_order: string;
  due: string;
  outputs: Line[];
};
type Order = Plan & {
  id: string;
  number: string;
  status: string;
  revision: number;
  sales_number: string;
};
type Entry = {
  revision: number;
  action: string;
  at: string;
  actor: string;
  entry: {
    batch?: string;
    quantity?: string;
    accepted?: string;
    rejected?: string;
  };
};
type Option = { id: string; name?: string; sku?: string; so_number?: string };
const material = (): Material => ({ product: "", per_unit: "1" });
const line = (): Line => ({
  product: "",
  quantity: "1",
  specification: "",
  estimated_expenses: "0",
  materials: [material()],
});
const empty = (): Plan => ({
  warehouse: "",
  sales_order: "",
  due: "",
  outputs: [line()],
});
const sum = (rows: Line[], field: "estimate" | "actual") =>
  rows.reduce((n, x) => n + Number(x[field] || 0), 0);
const rupees = (v: number | string | undefined) =>
  Number(v ?? 0).toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
  });
function Pick({
  label,
  value,
  options,
  set,
  products = false,
}: {
  label: string;
  value: string;
  options: Option[];
  set: (s: string) => void;
  products?: boolean;
}) {
  return (
    <label>
      {label}
      <SearchSelect
        aria-label={label}
        name={products ? "product_id" : undefined}
        value={value}
        onChange={(e) => set(e.target.value)}
      >
        <option value="">Select…</option>
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {[o.sku, o.name || o.so_number].filter(Boolean).join(" · ")}
          </option>
        ))}
      </SearchSelect>
    </label>
  );
}
function Input({
  label,
  value,
  set,
  type = "text",
}: {
  label: string;
  value: string;
  set: (s: string) => void;
  type?: string;
}) {
  return (
    <label>
      {label}
      <input
        className="nx-input"
        type={type}
        min={type === "number" ? 0 : undefined}
        step={type === "number" ? ".01" : undefined}
        value={value}
        onChange={(e) => set(e.target.value)}
      />
    </label>
  );
}
function useOptions(path: string, key: string, enabled: boolean) {
  return useQuery({
    queryKey: ["production-options", path],
    enabled,
    queryFn: async () =>
      (await apiRequest<Record<string, Option[]>>(path + "?page_size=100"))
        .data[key],
  });
}
export default function Manufacturing() {
  const cache = useQueryClient(),
    { authentication } = useAuth();
  const can = (p: string) =>
    hasPermission(authentication?.role.permissions ?? [], p);
  const write = can("manufacturing.manage") && can("inventory.adjust");
  const [page, setPage] = useState(1),
    [filter, setFilter] = useState({
      sales_order:
        typeof window === "undefined"
          ? ""
          : new URLSearchParams(window.location.search).get("sales_order") ||
            "",
      search: "",
      status: "",
      from: "",
      to: "",
      sort: "newest",
      product: "",
    });
  const [id, select] = useState(""),
    [draft, edit] = useState<Plan | null>(null),
    [msg, notify] = useState(""),
    [busy, setBusy] = useState(false);
  const [action, setAction] = useState("issue"),
    [idx, setIdx] = useState(0),
    [fields, setFields] = useState<Record<string, string>>({});
  const last = useRef({ body: "", key: "" }),
    guard = useRef(false);
  const [report, setReport] = useState("costs");
  const read = can("manufacturing.read");
  const list = useQuery({
    queryKey: ["production-list", page, filter],
    enabled: read,
    queryFn: async () =>
      (
        await apiRequest<{
          rows: Order[];
          count: number;
          completed: number;
          pending: number;
        }>(root + "?" + new URLSearchParams({ ...filter, page: String(page) }))
      ).data,
  });
  const detail = useQuery({
    queryKey: ["production", id],
    enabled: read && !!id,
    queryFn: async () =>
      (
        await apiRequest<{
          order: Order;
          history: Entry[];
          net_revenue?: string;
          revenue_less_job_cost?: string;
          sales?: {
            number: string;
            total: string;
            paid: string;
            due: string;
          }[];
        }>(root + id + "/")
      ).data,
  });
  const warehouses = useOptions("/warehouses/", "warehouses", !!draft),
    orders = useOptions(
      "/sales-orders/",
      "sales_orders",
      !!draft && can("sales_orders.read"),
    );
  const order = detail.data?.order,
    output = order?.outputs[idx];
  const field = (key: string, label: string, type = "text") => (
    <Input
      key={key}
      label={label}
      type={type}
      value={fields[key] ?? ""}
      set={(v) => setFields({ ...fields, [key]: v })}
    />
  );
  const change = (i: number, p: Partial<Line>) =>
    edit(
      draft && {
        ...draft,
        outputs: draft.outputs.map((x, j) => (i === j ? { ...x, ...p } : x)),
      },
    );
  function open(key: string) {
    select(key);
    edit(null);
    setFields({});
    setIdx(0);
    notify("");
  }
  async function save(data: Record<string, unknown>, target: string) {
    if (guard.current || !window.confirm("Save this manufacturing entry?"))
      return;
    guard.current = true;
    setBusy(true);
    notify("");
    const body = JSON.stringify([target, data]);
    if (last.current.body !== body)
      last.current = { body, key: crypto.randomUUID() };
    try {
      const r = await apiRequest<{ id: string }>(
        root + (target ? target + "/" : ""),
        { method: "POST", body: { ...data, request_key: last.current.key } },
      );
      open(r.data.id);
      await Promise.all([
        cache.invalidateQueries({ queryKey: ["production-list"] }),
        cache.invalidateQueries({ queryKey: ["production", r.data.id] }),
      ]);
      last.current.body = "";
      notify("Saved.");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Unable to save.");
    } finally {
      guard.current = false;
      setBusy(false);
    }
  }
  if (!read) return <p>Manufacturing access required.</p>;
  return (
    <section className="space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Manufacturing</h1>
        {write && !draft && (
          <button
            className="nx-button"
            onClick={() => {
              open("");
              edit(empty());
            }}
          >
            New order
          </button>
        )}
      </header>
      {msg && <p role="status">{msg}</p>}
      {draft ? (
        <div className="nx-card space-y-4 p-4">
          <h2>{id ? "Edit plan" : "Plan production"}</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            <Pick
              label="Warehouse"
              options={warehouses.data ?? []}
              value={draft.warehouse}
              set={(warehouse) => edit({ ...draft, warehouse })}
            />
            <Pick
              label="Sales order (optional)"
              options={orders.data ?? []}
              value={draft.sales_order}
              set={(sales_order) => edit({ ...draft, sales_order })}
            />
            <Input
              label="Due date"
              type="date"
              value={draft.due}
              set={(due) => edit({ ...draft, due })}
            />
          </div>
          {draft.outputs.map((l, i) => (
            <fieldset key={i} className="space-y-3 border-t py-3">
              <legend>Finished product {i + 1}</legend>
              <div className="grid gap-3 sm:grid-cols-2">
                <Pick
                  products
                  label="Finished item"
                  options={
                    l.product
                      ? [{ id: l.product, name: l.name || l.product }]
                      : []
                  }
                  value={l.product}
                  set={(product) => change(i, { product, name: undefined })}
                />
                <Input
                  label="Planned quantity"
                  type="number"
                  value={l.quantity}
                  set={(quantity) => change(i, { quantity })}
                />
                <Input
                  label="Specifications and dimensions"
                  value={l.specification}
                  set={(specification) => change(i, { specification })}
                />
                <Input
                  label="Estimated non-material cost (₹)"
                  type="number"
                  value={l.estimated_expenses}
                  set={(estimated_expenses) =>
                    change(i, { estimated_expenses })
                  }
                />
              </div>
              {l.materials.map((m, j) => (
                <div key={j} className="grid gap-2 sm:grid-cols-3">
                  <Pick
                    products
                    label="Raw material"
                    options={
                      m.product
                        ? [{ id: m.product, name: m.name || m.product }]
                        : []
                    }
                    value={m.product}
                    set={(product) =>
                      change(i, {
                        materials: l.materials.map((x, k) =>
                          k === j ? { ...x, product, name: undefined } : x,
                        ),
                      })
                    }
                  />
                  <Input
                    label="Material units per finished unit"
                    type="number"
                    value={m.per_unit}
                    set={(per_unit) =>
                      change(i, {
                        materials: l.materials.map((x, k) =>
                          k === j ? { ...x, per_unit } : x,
                        ),
                      })
                    }
                  />
                  <button
                    disabled={l.materials.length === 1}
                    onClick={() =>
                      change(i, {
                        materials: l.materials.filter((_, k) => k !== j),
                      })
                    }
                  >
                    Remove material
                  </button>
                </div>
              ))}
              <button
                className="nx-button nx-secondary"
                onClick={() =>
                  change(i, { materials: [...l.materials, material()] })
                }
              >
                Add material
              </button>{" "}
              {draft.outputs.length > 1 && (
                <button
                  onClick={() =>
                    edit({
                      ...draft,
                      outputs: draft.outputs.filter((_, j) => j !== i),
                    })
                  }
                >
                  Remove output
                </button>
              )}
            </fieldset>
          ))}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() =>
                edit({ ...draft, outputs: [...draft.outputs, line()] })
              }
            >
              Add finished product
            </button>
            <button
              className="nx-button"
              disabled={busy}
              onClick={() =>
                save(
                  {
                    ...draft,
                    action: id ? "edit" : "create",
                    revision: order?.revision,
                  },
                  id,
                )
              }
            >
              Save plan
            </button>
            <button onClick={() => edit(null)}>Cancel</button>
          </div>
        </div>
      ) : id ? (
        <>
          <button onClick={() => open("")}>← All manufacturing orders</button>
          {detail.error && <p role="alert">{detail.error.message}</p>}
          {!order && !detail.error && <p>Loading order…</p>}
          {order && (
            <>
              <article className="nx-card space-y-3 p-4">
                <h2>
                  {order.number} · {order.status}
                </h2>
                <p>
                  {order.due} · {order.sales_number || "Make to stock"}
                </p>
                {order.outputs.map((l, i) => (
                  <section key={i} className="border-t py-3">
                    <strong>
                      {l.name} · {l.quantity} {l.unit}
                    </strong>
                    <p>{l.specification}</p>
                    <p>
                      Accepted {l.accepted} · Rejected {l.rejected} · Pending{" "}
                      {l.pending}
                    </p>
                    <p>
                      Estimated {rupees(l.estimate)} · Actual {rupees(l.actual)}{" "}
                      · Variance {rupees(l.variance)} · Cost per accepted unit{" "}
                      {l.unit_cost ? rupees(l.unit_cost) : "—"}
                    </p>
                    <p>
                      Warehouse stock {l.on_hand} {l.unit} · Work in progress{" "}
                      {rupees(l.work_in_progress)}
                    </p>
                    {l.batches?.map((b) => (
                      <p key={b.name}>
                        Batch {b.name} ·{" "}
                        {b.posted
                          ? `Accepted ${b.accepted} · Rejected ${b.rejected} · ${rupees(b.cost)}`
                          : "In production"}
                      </p>
                    ))}
                    {l.materials.map((m) => (
                      <p key={m.product}>
                        {m.name} · Required {m.required} {m.unit} · Available{" "}
                        {m.available} · Net issued {m.issued} ·{" "}
                        {rupees(m.value)}
                      </p>
                    ))}
                  </section>
                ))}
                {order.sales_order && (
                  <Link href="/sales-orders">
                    Open sales orders for delivery and billing
                  </Link>
                )}
                {detail.data?.net_revenue !== undefined && (
                  <p>
                    Linked invoiced revenue after credits{" "}
                    {rupees(detail.data.net_revenue)} · Revenue less actual job
                    cost {rupees(detail.data.revenue_less_job_cost)}
                  </p>
                )}
                {detail.data?.sales?.map((s) => (
                  <p key={s.number}>
                    {s.number} · Billed {rupees(s.total)} · Paid{" "}
                    {rupees(s.paid)} · Outstanding {rupees(s.due)}
                  </p>
                ))}
                {write && (
                  <button
                    className="nx-button nx-secondary"
                    onClick={() => {
                      select("");
                      edit({
                        warehouse: order.warehouse,
                        sales_order: "",
                        due: "",
                        outputs: order.outputs.map((l) => ({
                          ...line(),
                          name: l.name,
                          product: l.product,
                          specification: l.specification,
                          quantity: l.quantity,
                          estimated_expenses: l.estimated_expenses,
                          materials: l.materials.map((m) => ({
                            name: m.name,
                            product: m.product,
                            per_unit: m.per_unit,
                          })),
                        })),
                      });
                      notify("");
                    }}
                  >
                    Use plan for a new order
                  </button>
                )}
                {write && order.status === "planned" && (
                  <button onClick={() => edit(order)}>Edit plan</button>
                )}
              </article>
              {write && order.status !== "completed" && output && (
                <div className="nx-card space-y-3 p-4">
                  <h2>Record production activity</h2>
                  <select
                    className="nx-input"
                    aria-label="Activity"
                    value={action}
                    onChange={(e) => {
                      setAction(e.target.value);
                      setFields({});
                    }}
                  >
                    {[
                      "allocate",
                      "release",
                      "issue",
                      "return",
                      "produce",
                      "close",
                    ].map((a) => (
                      <option key={a}>{a}</option>
                    ))}
                  </select>
                  {action !== "close" && (
                    <>
                      <select
                        aria-label="Output"
                        className="nx-input"
                        value={idx}
                        onChange={(e) => {
                          setIdx(Number(e.target.value));
                          setFields({});
                        }}
                      >
                        {order.outputs.map((l, i) => (
                          <option key={i} value={i}>
                            {l.name} · {l.specification}
                          </option>
                        ))}
                      </select>
                      {field("batch", "Batch reference")}
                    </>
                  )}
                  {["allocate", "release", "issue", "return"].includes(
                    action,
                  ) && (
                    <>
                      <select
                        aria-label="Raw material"
                        className="nx-input"
                        value={fields.material || ""}
                        onChange={(e) =>
                          setFields({ ...fields, material: e.target.value })
                        }
                      >
                        <option value="">Select material</option>
                        {output.materials.map((m) => (
                          <option key={m.product} value={m.product}>
                            {m.name} ({m.unit})
                          </option>
                        ))}
                      </select>
                      {field("quantity", "Material quantity", "number")}
                    </>
                  )}
                  {action === "produce" && (
                    <div className="grid gap-3 sm:grid-cols-2">
                      {[
                        "accepted",
                        "rejected",
                        "labour",
                        "machine",
                        "consumables",
                        "other",
                      ].map((k) =>
                        field(
                          k,
                          k[0].toUpperCase() +
                            k.slice(1) +
                            (["accepted", "rejected"].includes(k)
                              ? " quantity"
                              : " cost (₹)"),
                          "number",
                        ),
                      )}
                    </div>
                  )}
                  <button
                    className="nx-button"
                    disabled={busy}
                    onClick={() =>
                      save(
                        {
                          ...Object.fromEntries(
                            Object.entries(fields).filter(([, v]) => v !== ""),
                          ),
                          action,
                          line: idx,
                          revision: order.revision,
                        },
                        id,
                      )
                    }
                  >
                    Save {action}
                  </button>
                </div>
              )}
              <div className="nx-card p-4">
                <h2>Production history</h2>
                {detail.data?.history.map((e, i) => (
                  <details key={i}>
                    <summary>
                      {new Date(e.at).toLocaleString()} · {e.action}{" "}
                      {e.entry.batch}
                    </summary>
                    <pre className="overflow-auto">
                      {JSON.stringify(e.entry, null, 2)}
                    </pre>
                  </details>
                ))}
              </div>
            </>
          )}
        </>
      ) : (
        <>
          <div className="nx-card p-4">
            Orders {list.data?.count ?? "…"} · Pending{" "}
            {list.data?.pending ?? "…"} · Completed{" "}
            {list.data?.completed ?? "…"}
          </div>
          <div className="grid gap-2 sm:grid-cols-3">
            {(["search", "from", "to"] as const).map((k) => (
              <Input
                key={k}
                label={
                  {
                    search: "Order number",
                    from: "Due from",
                    to: "Due through",
                  }[k]
                }
                type={k === "search" ? "search" : "date"}
                value={filter[k]}
                set={(v) => {
                  setFilter({ ...filter, [k]: v });
                  setPage(1);
                }}
              />
            ))}
            <Pick
              products
              label="Finished product filter"
              options={[]}
              value={filter.product}
              set={(product) => {
                setFilter({ ...filter, product });
                setPage(1);
              }}
            />
            <select
              aria-label="Status"
              className="nx-input"
              value={filter.status}
              onChange={(e) => {
                setPage(1);
                setFilter({ ...filter, status: e.target.value });
              }}
            >
              {["", "planned", "in progress", "completed"].map((s) => (
                <option key={s} value={s}>
                  {s || "All statuses"}
                </option>
              ))}
            </select>
            <select
              aria-label="Order sorting"
              className="nx-input"
              value={filter.sort}
              onChange={(e) => {
                setPage(1);
                setFilter({ ...filter, sort: e.target.value });
              }}
            >
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
            </select>
          </div>
          <label>
            Report
            <select
              className="nx-input"
              value={report}
              onChange={(e) => setReport(e.target.value)}
            >
              <option value="costs">Manufacturing costs and quantities</option>
              <option value="materials">Raw material consumption</option>
              <option value="batches">Finished batches and yield</option>
            </select>
          </label>{" "}
          <button
            className="nx-button nx-secondary"
            onClick={() =>
              exportWorkbook(
                root +
                  "?" +
                  new URLSearchParams({ ...filter, report, export: "csv" }),
                "Manufacturing.csv",
              ).catch((e) => notify(e.message))
            }
          >
            Export filtered production report
          </button>
          {list.isPending && <p>Loading orders…</p>}
          {list.error && <p role="alert">{list.error.message}</p>}
          {list.data?.count === 0 && <p>No matching manufacturing orders.</p>}
          {list.data?.rows.map((o) => (
            <button
              key={o.id}
              className="nx-card block w-full p-4 text-left"
              onClick={() => open(o.id)}
            >
              <strong>{o.number}</strong>
              <p>
                {o.outputs.map((l) => l.name).join(", ")} · {o.status} · Due{" "}
                {o.due}
              </p>
              <p>
                Estimated {rupees(sum(o.outputs, "estimate"))} · Actual{" "}
                {rupees(sum(o.outputs, "actual"))}
              </p>
            </button>
          ))}
          <div className="flex gap-4">
            <button disabled={page === 1} onClick={() => setPage(page - 1)}>
              Previous
            </button>
            Page {page}
            <button
              disabled={page * 25 >= (list.data?.count ?? 0)}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </section>
  );
}
