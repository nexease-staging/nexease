"use client";

import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import type {
  DashboardBillStatus,
  DashboardInventoryStatus,
  DashboardInvoiceStatus,
  DashboardReceivableAging,
} from "@/features/dashboard/types";


interface DashboardStatusChartsProps {
  receivableAging:
    DashboardReceivableAging;

  invoiceStatus:
    DashboardInvoiceStatus;

  billStatus:
    DashboardBillStatus;

  inventoryStatus:
    DashboardInventoryStatus;
}


interface DonutDatum {
  name: string;
  value: number;
  color: string;
}


interface DonutCardProps {
  title: string;
  description: string;
  data: DonutDatum[];
  valueFormatter?: (
    value: number,
  ) => string;
}


function formatCurrency(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(
    value,
  );
}


function formatCount(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-IN",
  ).format(
    value,
  );
}


function DonutCard({
  title,
  description,
  data,
  valueFormatter = formatCount,
}: DonutCardProps) {
  const total =
    data.reduce(
      (
        sum,
        item,
      ) =>
        sum
        +
        item.value,
      0,
    );

  const hasData =
    total > 0;

  return (
    <article
      className="
        rounded-2xl
        border
        border-slate-200
        bg-white
        p-5
        shadow-sm
      "
    >
      <div>
        <h2
          className="
            text-base
            font-semibold
            text-slate-950
          "
        >
          {title}
        </h2>

        <p
          className="
            mt-1
            text-sm
            text-slate-500
          "
        >
          {description}
        </p>
      </div>

      {
        hasData
          ? (
            <>
              <div
                className="
                  relative
                  mt-5
                  h-56
                  w-full
                "
              >
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <PieChart>
                    <Pie
                      data={
                        data
                      }
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={58}
                      outerRadius={82}
                      paddingAngle={2}
                      stroke="none"
                    >
                      {
                        data.map(
                          (
                            item,
                          ) => (
                            <Cell
                              key={
                                item.name
                              }
                              fill={
                                item.color
                              }
                            />
                          ),
                        )
                      }
                    </Pie>

                    <Tooltip
                      formatter={(
                        value,
                      ) =>
                        valueFormatter(
                          Number(
                            value,
                          ),
                        )
                      }
                    />
                  </PieChart>
                </ResponsiveContainer>

                <div
                  className="
                    pointer-events-none
                    absolute
                    inset-0
                    flex
                    flex-col
                    items-center
                    justify-center
                  "
                >
                  <span
                    className="
                      text-xs
                      font-medium
                      uppercase
                      tracking-wide
                      text-slate-400
                    "
                  >
                    Total
                  </span>

                  <span
                    className="
                      mt-1
                      max-w-[130px]
                      truncate
                      text-center
                      text-lg
                      font-bold
                      text-slate-950
                    "
                    title={
                      valueFormatter(
                        total,
                      )
                    }
                  >
                    {
                      valueFormatter(
                        total,
                      )
                    }
                  </span>
                </div>
              </div>

              <div
                className="
                  mt-3
                  space-y-2
                "
              >
                {
                  data.map(
                    (
                      item,
                    ) => (
                      <div
                        key={
                          item.name
                        }
                        className="
                          flex
                          items-center
                          justify-between
                          gap-4
                          text-sm
                        "
                      >
                        <div
                          className="
                            flex
                            min-w-0
                            items-center
                            gap-2
                          "
                        >
                          <span
                            className="
                              h-2.5
                              w-2.5
                              shrink-0
                              rounded-full
                            "
                            style={{
                              backgroundColor:
                                item.color,
                            }}
                          />

                          <span
                            className="
                              truncate
                              text-slate-600
                            "
                          >
                            {
                              item.name
                            }
                          </span>
                        </div>

                        <span
                          className="
                            shrink-0
                            font-semibold
                            text-slate-900
                          "
                        >
                          {
                            valueFormatter(
                              item.value,
                            )
                          }
                        </span>
                      </div>
                    ),
                  )
                }
              </div>
            </>
          )
          : (
            <div
              className="
                mt-5
                flex
                h-56
                items-center
                justify-center
                rounded-xl
                border
                border-dashed
                border-slate-200
                bg-slate-50
              "
            >
              <p
                className="
                  text-sm
                  text-slate-500
                "
              >
                No data available
              </p>
            </div>
          )
      }
    </article>
  );
}


export default function DashboardStatusCharts({
  receivableAging,
  invoiceStatus,
  billStatus,
  inventoryStatus,
}: DashboardStatusChartsProps) {
  const receivableData:
    DonutDatum[] = [
      {
        name:
          "Current",
        value:
          Number(
            receivableAging
              .current,
          ),
        color:
          "#0f766e",
      },
      {
        name:
          "1–30 Days",
        value:
          Number(
            receivableAging[
              "1_30"
            ],
          ),
        color:
          "#2563eb",
      },
      {
        name:
          "31–60 Days",
        value:
          Number(
            receivableAging[
              "31_60"
            ],
          ),
        color:
          "#d97706",
      },
      {
        name:
          "61–90 Days",
        value:
          Number(
            receivableAging[
              "61_90"
            ],
          ),
        color:
          "#ea580c",
      },
      {
        name:
          "90+ Days",
        value:
          Number(
            receivableAging[
              "90_plus"
            ],
          ),
        color:
          "#dc2626",
      },
    ];

  const invoiceData:
    DonutDatum[] = [
      {
        name:
          "Issued",
        value:
          invoiceStatus
            .issued,
        color:
          "#2563eb",
      },
      {
        name:
          "Partially Paid",
        value:
          invoiceStatus
            .partially_paid,
        color:
          "#d97706",
      },
      {
        name:
          "Paid",
        value:
          invoiceStatus
            .paid,
        color:
          "#059669",
      },
      {
        name:
          "Overdue",
        value:
          invoiceStatus
            .overdue,
        color:
          "#dc2626",
      },
    ];

  const billData:
    DonutDatum[] = [
      {
        name:
          "Posted",
        value:
          billStatus
            .posted,
        color:
          "#2563eb",
      },
      {
        name:
          "Partially Paid",
        value:
          billStatus
            .partially_paid,
        color:
          "#d97706",
      },
      {
        name:
          "Paid",
        value:
          billStatus
            .paid,
        color:
          "#059669",
      },
      {
        name:
          "Overdue",
        value:
          billStatus
            .overdue,
        color:
          "#dc2626",
      },
    ];

  const inventoryData:
    DonutDatum[] = [
      {
        name:
          "In Stock",
        value:
          inventoryStatus
            .in_stock,
        color:
          "#059669",
      },
      {
        name:
          "Out of Stock",
        value:
          inventoryStatus
            .out_of_stock,
        color:
          "#dc2626",
      },
    ];

  return (
    <section
      className="
        grid
        gap-6
        md:grid-cols-2
        xl:grid-cols-4
      "
    >
      <DonutCard
        title="Receivables Aging"
        description="Outstanding receivables by age"
        data={
          receivableData
        }
        valueFormatter={
          formatCurrency
        }
      />

      <DonutCard
        title="Invoice Status"
        description="Current invoice distribution"
        data={
          invoiceData
        }
      />

      <DonutCard
        title="Bill Status"
        description="Current vendor bill distribution"
        data={
          billData
        }
      />

      <DonutCard
        title="Inventory Status"
        description="Available inventory position"
        data={
          inventoryData
        }
      />
    </section>
  );
}