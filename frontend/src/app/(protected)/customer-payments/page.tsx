"use client";

import RegisterScreen from "@/features/payments/components/register-screen";

export default function CustomerPaymentsPage() {
  return <RegisterScreen title="Customer payments" subtitle="Receipts from customers. One receipt can settle several invoices." initialDirection="in" lockDirection />;
}
