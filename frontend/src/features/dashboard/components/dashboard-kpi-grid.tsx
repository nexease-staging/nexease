import {
  AlertTriangle,
  Banknote,
  Boxes,
  CreditCard,
  IndianRupee,
  ReceiptIndianRupee,
  ShoppingCart,
} from "lucide-react";

import type {
  DashboardKPIs,
} from "@/features/dashboard/types";


interface DashboardKPIGridProps {
  kpis: DashboardKPIs;
}


function formatCurrency(
  value: string,
): string {
  const amount =
    Number(
      value,
    );

  if (
    !Number.isFinite(
      amount,
    )
  ) {
    return "₹0.00";
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(
    amount,
  );
}


export default function DashboardKPIGrid({
  kpis,
}: DashboardKPIGridProps) {
  const cards = [
    {
      label:
        "Total Sales",
      value:
        formatCurrency(
          kpis.total_sales,
        ),
      description:
        "Invoice value in period",
      icon:
        IndianRupee,
    },

    {
      label:
        "Total Purchases",
      value:
        formatCurrency(
          kpis.total_purchases,
        ),
      description:
        "Vendor bill value in period",
      icon:
        ShoppingCart,
    },

    {
      label:
        "Receivables",
      value:
        formatCurrency(
          kpis.receivables,
        ),
      description:
        "Outstanding customer balance",
      icon:
        ReceiptIndianRupee,
    },

    {
      label:
        "Payables",
      value:
        formatCurrency(
          kpis.payables,
        ),
      description:
        "Outstanding supplier balance",
      icon:
        CreditCard,
    },

    {
      label:
        "Cash / Bank Balance",
      value:
        formatCurrency(
          kpis.bank_balance,
        ),
      description:
        "Current active account balance",
      icon:
        Banknote,
    },

    {
      label:
        "Inventory Value",
      value:
        formatCurrency(
          kpis.inventory_value,
        ),
      description:
        "Inventory valued at cost",
      icon:
        Boxes,
    },

    {
      label:
        "Out of Stock Items",
      value:
        new Intl.NumberFormat(
          "en-IN",
        ).format(
          kpis.out_of_stock_items,
        ),
      description:
        "Items with no available stock",
      icon:
        AlertTriangle,
    },
  ];

  return (
    <section
      aria-label="Dashboard KPIs"
      className="
        grid
        gap-4
        sm:grid-cols-2
        xl:grid-cols-4
      "
    >
      {
        cards.map(
          (
            card,
            index,
          ) => {
            const Icon =
              card.icon;

            const isAlert =
              card.label
              ===
              "Out of Stock Items"
              &&
              kpis.out_of_stock_items
              > 0;

            return (
              <article
                key={
                  card.label
                }
                className={`
                  rounded-2xl
                  border
                  bg-white
                  p-5
                  shadow-sm
                  ${
                    index === 6
                      ? "xl:col-span-2"
                      : ""
                  }
                  ${
                    isAlert
                      ? "border-amber-200"
                      : "border-slate-200"
                  }
                `}
              >
                <div
                  className="
                    flex
                    items-start
                    justify-between
                    gap-4
                  "
                >
                  <div
                    className="
                      min-w-0
                    "
                  >
                    <p
                      className="
                        text-sm
                        font-medium
                        text-slate-500
                      "
                    >
                      {
                        card.label
                      }
                    </p>

                    <p
                      className="
                        mt-3
                        truncate
                        text-2xl
                        font-bold
                        tracking-tight
                        text-slate-950
                      "
                      title={
                        card.value
                      }
                    >
                      {
                        card.value
                      }
                    </p>

                    <p
                      className="
                        mt-2
                        text-xs
                        leading-5
                        text-slate-500
                      "
                    >
                      {
                        card.description
                      }
                    </p>
                  </div>

                  <div
                    className={`
                      flex
                      h-11
                      w-11
                      shrink-0
                      items-center
                      justify-center
                      rounded-xl
                      ${
                        isAlert
                          ? `
                            bg-amber-50
                            text-amber-700
                          `
                          : `
                            bg-slate-100
                            text-slate-700
                          `
                      }
                    `}
                  >
                    <Icon
                      className="
                        h-5
                        w-5
                      "
                    />
                  </div>
                </div>
              </article>
            );
          },
        )
      }
    </section>
  );
}