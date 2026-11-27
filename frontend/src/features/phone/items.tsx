"use client";

import { useState } from "react";
import { Package, ScanLine, Search, X } from "lucide-react";
import BarcodeScan from "@/features/business/barcode-scan";
import { runQuick } from "@/features/mobile/quick-actions";
import { useAuth } from "@/features/auth/auth-context";
import { hasPermission } from "@/lib/authorization/permissions";
import { useDebounced } from "@/components/list/list-kit";
import { inr, useItems, type Item } from "./api";
import { Empty, ErrorState, Loading, Sheet } from "./bits";

type Found = { name: string; code?: string; barcode?: string; hsn_code?: string; selling_price?: string; unit?: string; stock?: { warehouse: string; available: string }[] };

export default function PhoneItems() {
  const { authentication } = useAuth();
  const canAdd = hasPermission(authentication?.role.permissions ?? [], "products.create");
  const [term, setTerm] = useState("");
  const [type, setType] = useState("");
  const [open, setOpen] = useState<Item | null>(null);
  const [found, setFound] = useState<Found | null>(null);
  const [scanning, setScanning] = useState(false);
  const search = useDebounced(term.trim(), 300);
  const q = useItems(search, type);
  const rows = q.data?.pages.flatMap((p) => p.rows) ?? [];

  return (
    <div className="nxp-page">
      <div className="nxp-toolrow nxp-gap">
        <label className="nxp-search"><Search size={18} /><input aria-label="Search items" placeholder="Search items" value={term} onChange={(e) => setTerm(e.target.value)} /></label>
        <button type="button" className="nxp-btn ghost nxp-scan" onClick={() => setScanning(true)}><ScanLine size={18} />Scan</button>
      </div>
      <div className="nxp-chips">{[["", "All"], ["goods", "Goods"], ["service", "Services"]].map(([k, l]) => <button key={k} type="button" className={type === k ? "on" : ""} onClick={() => setType(k)}>{l}</button>)}</div>
      {found ? (
        <div className="nxp-card">
          <div className="nxp-cardhead"><b>{found.name}</b><button type="button" className="nxp-ic" aria-label="Close" onClick={() => setFound(null)}><X size={18} /></button></div>
          <small className="nxp-mute">{[found.code, found.barcode, found.hsn_code && `HSN ${found.hsn_code}`].filter(Boolean).join(" · ")}</small>
          <div className="nxp-big">{inr(found.selling_price)} <small className="nxp-mute">/ {found.unit}</small></div>
          {(found.stock ?? []).map((s, i) => <div className="nxp-row" key={i}><div className="nxp-g">{s.warehouse}</div><div className="nxp-amt">{s.available}<small>available</small></div></div>)}
          {!(found.stock ?? []).length ? <small className="nxp-mute">No stock recorded.</small> : null}
        </div>
      ) : null}
      {q.isPending ? <Loading /> : q.error ? <ErrorState error={q.error} retry={() => void q.refetch()} /> : !rows.length && !search && !type ? (
        <Empty icon={Package} text="Add the products and services you sell. They fill in automatically on invoices." cta={canAdd ? "Add item" : undefined} onCta={() => runQuick("item")} />
      ) : (
        <div className="nxp-card nxp-list">
          {rows.map((i) => (
            <div className="nxp-row" key={i.id} role="button" tabIndex={0} onClick={() => setOpen(i)} onKeyDown={(e) => e.key === "Enter" && setOpen(i)}>
              <div className="nxp-g"><b>{i.name}</b><small>{[i.unit, i.hsn && `HSN ${i.hsn}`].filter(Boolean).join(" · ")}</small></div>
              <div className="nxp-amt">{inr(i.price)}{i.stock !== null ? <small className={Number(i.stock) <= 0 ? "give" : ""}>Stock {Number(i.stock)}</small> : <small>Service</small>}</div>
            </div>
          ))}
          {!rows.length ? <div className="nxp-empty nxp-empty-sm">No item matches.</div> : null}
          {q.hasNextPage ? <button type="button" className="nxp-more" disabled={q.isFetchingNextPage} onClick={() => void q.fetchNextPage()}>{q.isFetchingNextPage ? "Loading…" : "Show more"}</button> : null}
        </div>
      )}
      {canAdd ? <button type="button" className="nxp-btn" onClick={() => runQuick("item")}>Add item</button> : null}
      {open ? (
        <Sheet title={open.name} sub={[open.sku, open.hsn && `HSN ${open.hsn}`].filter(Boolean).join(" · ")} onClose={() => setOpen(null)}>
          <div className="nxp-tot">
            <div><span>Selling price</span><b>{inr(open.price)} / {open.unit}</b></div>
            {open.stock !== null ? <div><span>In stock</span><b className={Number(open.stock) <= 0 ? "give" : ""}>{Number(open.stock)} {open.unit}</b></div> : null}
          </div>
          <div className="nxp-grid3 nxp-actions">
            <button type="button" onClick={() => { setOpen(null); runQuick("sale"); }}><span className="nxp-qi"><Package size={19} /></span>Sell</button>
            <a href={`/products?view=${open.id}`}><span className="nxp-qi"><Search size={19} /></span>Open full</a>
            <a href="/stock-movements"><span className="nxp-qi"><ScanLine size={19} /></span>Movements</a>
          </div>
        </Sheet>
      ) : null}
      {scanning ? (
        <Sheet title="Scan a barcode" sub="Point the camera at the barcode, or type the code" onClose={() => setScanning(false)}>
          <BarcodeScan onSelect={(r) => { setFound(r as unknown as Found); setScanning(false); }} />
        </Sheet>
      ) : null}
    </div>
  );
}
