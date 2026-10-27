"use client";

import {
  Bar,
  BarChart,
  ComposedChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  DashboardCashFlowPoint,
  DashboardTrendPoint,
} from "@/features/dashboard/types";


interface DashboardTrendChartsProps {
  salesTrend:
    DashboardTrendPoint[];

  purchaseTrend:
    DashboardTrendPoint[];

  cashFlow:
    DashboardCashFlowPoint[];
}


function formatCurrency(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    },
  ).format(
    value,
  );
}


function formatPeriod(
  value: string,
): string {
  const [
    year,
    month,
  ] = value.split(
    "-",
  );

  const date =
    new Date(
      Number(
        year,
      ),
      Number(
        month,
      ) - 1,
      1,
    );

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      month: "short",
      year: "2-digit",
    },
  ).format(
    date,
  );
}


export default function DashboardTrendCharts({
  salesTrend,
  purchaseTrend,
  cashFlow,
}: DashboardTrendChartsProps) {
  const salesData =
    salesTrend.map(
      (
        item,
      ) => ({
        period:
          item.period,

        amount:
          Number(
            item.amount,
          ),
      }),
    );

  const purchaseData =
    purchaseTrend.map(
      (
        item,
      ) => ({
        period:
          item.period,

        amount:
          Number(
            item.amount,
          ),
      }),
    );

  const cashFlowData =
    cashFlow.map(
      (
        item,
      ) => ({
        period:
          item.period,

        inflow:
          Number(
            item.inflow,
          ),

        outflow:
          Number(
            item.outflow,
          ),

        net:
          Number(
            item.net,
          ),
      }),
    );

  return (
    <section
      className="
        grid
        gap-6
        xl:grid-cols-2
      "
    >
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
        <div
          className="
            mb-5
          "
        >
          <h2
            className="
              text-base
              font-semibold
              text-slate-950
            "
          >
            Sales Trend
          </h2>

          <p
            className="
              mt-1
              text-sm
              text-slate-500
            "
          >
            Monthly invoice value
          </p>
        </div>

        <div
          className="
            h-80
            w-full
          "
        >
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <LineChart
              data={
                salesData
              }
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="period"
                tickFormatter={
                  formatPeriod
                }
              />

              <YAxis
                tickFormatter={(
                  value,
                ) =>
                  formatCurrency(
                    Number(
                      value,
                    ),
                  )
                }
              />

              <Tooltip
                formatter={(
                  value,
                ) => [
                  formatCurrency(
                    Number(
                      value,
                    ),
                  ),
                  "Sales",
                ]}
                labelFormatter={(
                label,
                ) =>
                formatPeriod(
                    String(
                    label ?? "",
                    ),
                )
                }
              />

              <Line
                type="monotone"
                dataKey="amount"
                name="Sales"
                stroke="currentColor"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </article>

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
        <div
          className="
            mb-5
          "
        >
          <h2
            className="
              text-base
              font-semibold
              text-slate-950
            "
          >
            Purchase Trend
          </h2>

          <p
            className="
              mt-1
              text-sm
              text-slate-500
            "
          >
            Monthly vendor bill value
          </p>
        </div>

        <div
          className="
            h-80
            w-full
          "
        >
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <BarChart
              data={
                purchaseData
              }
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="period"
                tickFormatter={
                  formatPeriod
                }
              />

              <YAxis
                tickFormatter={(
                  value,
                ) =>
                  formatCurrency(
                    Number(
                      value,
                    ),
                  )
                }
              />

              <Tooltip
                formatter={(
                  value,
                ) => [
                  formatCurrency(
                    Number(
                      value,
                    ),
                  ),
                  "Purchases",
                ]}
                labelFormatter={(
                label,
                ) =>
                formatPeriod(
                    String(
                    label ?? "",
                    ),
                )
                }
              />

              <Bar
                dataKey="amount"
                name="Purchases"
                fill="currentColor"
                radius={[
                  6,
                  6,
                  0,
                  0,
                ]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article
        className="
          rounded-2xl
          border
          border-slate-200
          bg-white
          p-5
          shadow-sm
          xl:col-span-2
        "
      >
        <div
          className="
            mb-5
          "
        >
          <h2
            className="
              text-base
              font-semibold
              text-slate-950
            "
          >
            Cash Inflow vs Outflow
          </h2>

          <p
            className="
              mt-1
              text-sm
              text-slate-500
            "
          >
            Monthly bank movement
          </p>
        </div>

        <div
          className="
            h-80
            w-full
          "
        >
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <ComposedChart
              data={
                cashFlowData
              }
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="period"
                tickFormatter={
                  formatPeriod
                }
              />

              <YAxis
                tickFormatter={(
                  value,
                ) =>
                  formatCurrency(
                    Number(
                      value,
                    ),
                  )
                }
              />

              <Tooltip
                formatter={(
                  value,
                  name,
                ) => [
                  formatCurrency(
                    Number(
                      value,
                    ),
                  ),
                  String(
                    name,
                  ),
                ]}
                labelFormatter={(
                label,
                ) =>
                formatPeriod(
                    String(
                    label ?? "",
                    ),
                )
                }
              />

              <Legend />

              <Bar
                dataKey="inflow"
                name="Inflow"
                fill="currentColor"
                radius={[
                  6,
                  6,
                  0,
                  0,
                ]}
              />

              <Bar
                dataKey="outflow"
                name="Outflow"
                fill="currentColor"
                radius={[
                  6,
                  6,
                  0,
                  0,
                ]}
              />

              <Line
                type="monotone"
                dataKey="net"
                name="Net"
                stroke="currentColor"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </article>
    </section>
  );
}