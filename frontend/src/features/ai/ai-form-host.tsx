"use client";

import { useState } from "react";
import InvoiceDialog from "@/features/invoices/components/invoice-dialog";
import QuickPurchase from "@/features/business/quick-purchase";
import SettleSheet from "@/features/payments/components/settle-sheet";
import CustomerDialog from "@/features/customers/components/customer-dialog";
import SupplierDialog from "@/features/suppliers/components/supplier-dialog";
import ProductDialog from "@/features/products/components/product-dialog";
import { customerPrefill, invoicePrefill, paymentPrefill, productPrefill, purchasePrefill, supplierPrefill, type Proposal } from "./forms";

/**
 * Opens the app's own form for an AI proposal, already filled in. Saving goes through the
 * form's normal validation and permissions; the assistant never saves these itself.
 */
export default function AiFormHost({ proposal, onClose, onSaved }: { proposal: Proposal; onClose: () => void; onSaved: (what: string) => void }) {
  const type = proposal.assist?.form?.type;
  const entry = proposal.data;
  // Computed once per proposal so the forms never reset while the user is typing.
  const [values] = useState(() => ({
    invoice: invoicePrefill(entry),
    purchase: purchasePrefill(entry),
    payment: paymentPrefill(entry),
    customer: customerPrefill(entry),
    supplier: supplierPrefill(entry),
    product: productPrefill(entry),
  }));

  if (type === "invoice") return <InvoiceDialog open initialMode="direct" prefill={values.invoice} onClose={onClose} onCreated={() => onSaved("Invoice saved.")} />;
  if (type === "purchase") return <QuickPurchase open kind={proposal.kind === "purchase_order" ? "purchase_order" : "bill"} prefill={values.purchase} onClose={onClose} />;
  if (type === "payment") return <SettleSheet side={proposal.kind === "payment_out" ? "payable" : "receivable"} partyId={proposal.assist?.refs.party_id} prefill={values.payment} onClose={onClose} />;
  if (type === "customer") return <CustomerDialog open customerId={null} prefill={values.customer} onClose={onClose} onCreated={() => onSaved("Customer saved.")} />;
  if (type === "supplier") return <SupplierDialog open supplierId={null} prefill={values.supplier} onClose={onClose} />;
  if (type === "product") return <ProductDialog open productId={null} prefill={values.product} onClose={onClose} onCreated={() => onSaved("Item saved.")} />;
  return null;
}
