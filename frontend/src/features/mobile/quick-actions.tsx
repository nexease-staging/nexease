"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import InvoiceDialog from "@/features/invoices/components/invoice-dialog";
import QuickPurchase from "@/features/business/quick-purchase";
import SettleSheet from "@/features/payments/components/settle-sheet";
import CustomerDialog from "@/features/customers/components/customer-dialog";
import SupplierDialog from "@/features/suppliers/components/supplier-dialog";
import ProductDialog from "@/features/products/components/product-dialog";
import { stashRecordPrefill } from "@/features/ai/handoff";

export type QuickAction = "sale" | "payment_in" | "payment_out" | "purchase" | "expense" | "customer" | "supplier" | "item";
const EVENT = "nexease:quick";

/** Opens a create form from anywhere (home tiles, party rows, the Add sale button). */
export function runQuick(action: QuickAction, partyId?: string) {
  window.dispatchEvent(new CustomEvent(EVENT, { detail: { action, partyId } }));
}

/** Mounted once in the app shell; renders whichever form was asked for. */
export default function QuickActionHost() {
  const [open, setOpen] = useState<{ action: QuickAction; partyId?: string; key: number } | null>(null);
  const router = useRouter();
  const pathname = usePathname();
  const qc = useQueryClient();

  useEffect(() => {
    const onQuick = (e: Event) => {
      const { action, partyId } = (e as CustomEvent<{ action: QuickAction; partyId?: string }>).detail;
      if (action === "expense") {
        stashRecordPrefill({ kind: "expenses", data: {} });
        if (pathname !== "/expenses") router.push("/expenses");
        return;
      }
      setOpen({ action, partyId, key: Date.now() });
    };
    window.addEventListener(EVENT, onQuick);
    return () => window.removeEventListener(EVENT, onQuick);
  }, [pathname, router]);

  if (!open) return null;
  const close = () => {
    setOpen(null);
    void qc.invalidateQueries({ queryKey: ["mobile-home"] });
    void qc.invalidateQueries({ queryKey: ["mobile-parties"] });
  };
  switch (open.action) {
    case "sale": return <InvoiceDialog key={open.key} open initialMode="direct" onClose={close} />;
    case "purchase": return <QuickPurchase key={open.key} open kind="bill" onClose={close} />;
    case "payment_in": return <SettleSheet key={open.key} side="receivable" partyId={open.partyId} onClose={close} />;
    case "payment_out": return <SettleSheet key={open.key} side="payable" partyId={open.partyId} onClose={close} />;
    case "customer": return <CustomerDialog key={open.key} open customerId={null} onClose={close} />;
    case "supplier": return <SupplierDialog key={open.key} open supplierId={null} onClose={close} />;
    case "item": return <ProductDialog key={open.key} open productId={null} onClose={close} />;
    default: return null;
  }
}
