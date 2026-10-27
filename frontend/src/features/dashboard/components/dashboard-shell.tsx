"use client";

import {
  useMemo,
  useState,
} from "react";

import {
  RefreshCw,
} from "lucide-react";

import {
  useMainDashboard,
} from "@/features/dashboard/hooks";

import DashboardKPIGrid from "@/features/dashboard/components/dashboard-kpi-grid";

import DashboardTrendCharts from "@/features/dashboard/components/dashboard-trend-charts";

import DashboardStatusCharts from "@/features/dashboard/components/dashboard-status-charts";

import DashboardTopEntities from "@/features/dashboard/components/dashboard-top-entities";

import DashboardAlertsActivity from "@/features/dashboard/components/dashboard-alerts-activity";

import DashboardLoadingSkeleton from "@/features/dashboard/components/dashboard-loading-skeleton";

function formatDateInput(
  date: Date,
): string {
  return date
    .toISOString()
    .slice(
      0,
      10,
    );
}


function getDefaultStartDate():
  string {
  const now =
    new Date();

  return formatDateInput(
    new Date(
      now.getFullYear(),
      0,
      1,
    ),
  );
}


function getDefaultEndDate():
  string {
  return formatDateInput(
    new Date(),
  );
}


export default function DashboardShell() {
  const [
    startDate,
    setStartDate,
  ] = useState(
    getDefaultStartDate,
  );

  const [
    endDate,
    setEndDate,
  ] = useState(
    getDefaultEndDate,
  );

  const parameters =
    useMemo(
      () => ({
        start_date:
          startDate,
        end_date:
          endDate,
      }),
      [
        startDate,
        endDate,
      ],
    );

  const {
    data: dashboard,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useMainDashboard(
    parameters,
  );

  return (
    <div
      className="
        min-h-screen
        bg-slate-50
      "
    >
      <div
        className="
          mx-auto
          max-w-[1600px]
          space-y-6
          p-6
          lg:p-8
        "
      >
        <header
          className="
            flex
            flex-col
            gap-4
            xl:flex-row
            xl:items-center
            xl:justify-between
          "
        >
          <div>
            <p
              className="
                text-sm
                font-medium
                text-slate-500
              "
            >
              Executive overview
            </p>

            <h1
              className="
                mt-1
                text-3xl
                font-bold
                tracking-tight
                text-slate-950
              "
            >
              Dashboard
            </h1>

            <p
              className="
                mt-2
                text-sm
                text-slate-600
              "
            >
              Monitor sales,
              purchases,
              cash flow,
              receivables,
              payables,
              and inventory.
            </p>
          </div>

          <div
            className="
              flex
              flex-wrap
              items-end
              gap-3
            "
          >
            <label
              className="
                grid
                gap-1.5
                text-sm
                font-medium
                text-slate-700
              "
            >
              Start date

              <input
                type="date"
                value={
                  startDate
                }
                max={
                  endDate
                }
                onChange={(
                  event,
                ) => {
                  setStartDate(
                    event
                      .target
                      .value,
                  );
                }}
                className="
                  rounded-lg
                  border
                  border-slate-300
                  bg-white
                  px-3
                  py-2
                  text-sm
                  text-slate-900
                  outline-none
                  transition
                  focus:border-slate-500
                "
              />
            </label>

            <label
              className="
                grid
                gap-1.5
                text-sm
                font-medium
                text-slate-700
              "
            >
              End date

              <input
                type="date"
                value={
                  endDate
                }
                min={
                  startDate
                }
                onChange={(
                  event,
                ) => {
                  setEndDate(
                    event
                      .target
                      .value,
                  );
                }}
                className="
                  rounded-lg
                  border
                  border-slate-300
                  bg-white
                  px-3
                  py-2
                  text-sm
                  text-slate-900
                  outline-none
                  transition
                  focus:border-slate-500
                "
              />
            </label>

            <button
              type="button"
              disabled={
                isFetching
              }
              onClick={() => {
                void refetch();
              }}
              className="
                inline-flex
                h-10
                items-center
                gap-2
                rounded-lg
                border
                border-slate-300
                bg-white
                px-4
                text-sm
                font-semibold
                text-slate-700
                shadow-sm
                transition
                hover:bg-slate-100
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            >
              <RefreshCw
                className={
                  `
                    h-4
                    w-4
                    ${
                      isFetching
                        ? "animate-spin"
                        : ""
                    }
                  `
                }
              />

              Refresh
            </button>
          </div>
        </header>

        {
          isLoading
            ? (
              <DashboardLoadingSkeleton />
            )
            : null
        }

        {
          isError
            ? (
              <section
                className="
                  rounded-2xl
                  border
                  border-red-200
                  bg-red-50
                  p-6
                "
              >
                <h2
                  className="
                    text-sm
                    font-semibold
                    text-red-900
                  "
                >
                  Dashboard could not be loaded
                </h2>

                <p
                  className="
                    mt-2
                    text-sm
                    text-red-700
                  "
                >
                  {
                    error instanceof Error
                      ? error.message
                      : "An unexpected error occurred."
                  }
                </p>
              </section>
            )
            : null
        }

        {
          dashboard
            ? (
              <>
                <section
                  className="
                    rounded-2xl
                    border
                    border-slate-200
                    bg-white
                    p-6
                    shadow-sm
                  "
                >
                  <div
                    className="
                      flex
                      flex-wrap
                      items-center
                      justify-between
                      gap-3
                    "
                  >
                    <div>
                      <h2
                        className="
                          text-lg
                          font-semibold
                          text-slate-950
                        "
                      >
                        Dashboard data loaded
                      </h2>

                      <p
                        className="
                          mt-1
                          text-sm
                          text-slate-500
                        "
                      >
                        {
                          dashboard
                            .period
                            .start_date
                        }
                        {" → "}
                        {
                          dashboard
                            .period
                            .end_date
                        }
                      </p>
                    </div>

                    <span
                      className="
                        rounded-full
                        bg-emerald-50
                        px-3
                        py-1
                        text-xs
                        font-semibold
                        text-emerald-700
                      "
                    >
                      API connected
                    </span>
                  </div>
                </section>

                <DashboardKPIGrid
                  kpis={
                    dashboard.kpis
                  }
                />
                  <DashboardTrendCharts
                    salesTrend={
                      dashboard.sales_trend
                    }
                    purchaseTrend={
                      dashboard.purchase_trend
                    }
                    cashFlow={
                      dashboard.cash_flow
                    }
                  />
                <DashboardStatusCharts
                  receivableAging={
                    dashboard.receivable_aging
                  }
                  invoiceStatus={
                    dashboard.invoice_status
                  }
                  billStatus={
                    dashboard.bill_status
                  }
                  inventoryStatus={
                    dashboard.inventory_status
                  }
                />
                <DashboardTopEntities
                  customers={
                    dashboard.top_customers
                  }
                  suppliers={
                    dashboard.top_suppliers
                  }
                />
                  <DashboardAlertsActivity
                    alerts={
                      dashboard.alerts
                    }
                    recentActivity={
                      dashboard.recent_activity
                    }
                  />
              </>
            )
            : null
        }
      </div>
    </div>
  );
}