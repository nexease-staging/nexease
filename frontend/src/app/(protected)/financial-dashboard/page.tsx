"use client";

import {
  Activity,
  ArrowDown,
  ArrowUp,
  Banknote,
  Landmark,
  Scale,
  WalletCards,
} from "lucide-react";

import {
  useAccountingDashboard,
  useFinanceDashboard,
} from "@/features/accounting/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

function formatAmount(
  value: string | number | null | undefined,
): string {
  const amount = Number(value ?? 0);

  if (!Number.isFinite(amount)) {
    return "₹0.00";
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
    },
  ).format(amount);
}

function formatValue(
  value: unknown,
): string {
  if (
    value === null
    ||
    value === undefined
  ) {
    return "—";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (
    typeof value === "string"
    ||
    typeof value === "number"
  ) {
    return String(value);
  }

  return "—";
}

function formatLabel(
  value: string,
): string {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}

function getErrorMessage(
  error: unknown,
): string {
  if (error instanceof APIRequestError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to load financial dashboard.";
}

interface SummaryCardProps {
  title: string;
  value: string;
  description: string;
  icon: React.ReactNode;
}

function SummaryCard({
  title,
  value,
  description,
  icon,
}: SummaryCardProps) {
  return (
    <div
      className="
        rounded-2xl border
        border-slate-200 bg-white
        p-5 shadow-sm
      "
    >
      <div
        className="
          flex items-start
          justify-between gap-4
        "
      >
        <div>
          <p
            className="
              text-sm font-medium
              text-slate-500
            "
          >
            {title}
          </p>

          <p
            className="
              mt-2 text-2xl
              font-bold text-slate-900
            "
          >
            {value}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
          >
            {description}
          </p>
        </div>

        <div
          className="
            rounded-xl bg-slate-100
            p-3 text-slate-700
          "
        >
          {icon}
        </div>
      </div>
    </div>
  );
}

function DashboardSection({
  title,
  values,
}: {
  title: string;
  values:
    Record<string, unknown>;
}) {
  const entries =
    Object.entries(values);

  return (
    <section
      className="
        rounded-2xl border
        border-slate-200 bg-white
        p-6 shadow-sm
      "
    >
      <h2
        className="
          text-lg font-semibold
          text-slate-900
        "
      >
        {title}
      </h2>

      {entries.length === 0 ? (
        <p
          className="
            mt-4 text-sm
            text-slate-500
          "
        >
          No data available.
        </p>
      ) : (
        <dl
          className="
            mt-5 grid gap-4
            sm:grid-cols-2
          "
        >
          {entries.map(
            ([key, value]) => (
              <div
                key={key}
                className="
                  rounded-xl
                  bg-slate-50 p-4
                "
              >
                <dt
                  className="
                    text-xs font-semibold
                    uppercase
                    tracking-wide
                    text-slate-500
                  "
                >
                  {formatLabel(key)}
                </dt>

                <dd
                  className="
                    mt-1 break-words
                    text-sm font-medium
                    text-slate-900
                  "
                >
                  {formatValue(value)}
                </dd>
              </div>
            ),
          )}
        </dl>
      )}
    </section>
  );
}

export default function FinancialDashboardPage() {
  const financeDashboardQuery =
    useFinanceDashboard();

  const accountingDashboardQuery =
    useAccountingDashboard();

  const isLoading =
    financeDashboardQuery.isLoading
    ||
    accountingDashboardQuery.isLoading;

  const error =
    financeDashboardQuery.error
    ??
    accountingDashboardQuery.error;

  const finance =
    financeDashboardQuery.data;

  const accounting =
    accountingDashboardQuery.data;

  if (isLoading) {
    return (
      <div
        className="
          rounded-2xl border
          border-slate-200 bg-white
          p-8 shadow-sm
        "
      >
        <p className="text-slate-600">
          Loading financial dashboard...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="
          rounded-2xl border
          border-red-200 bg-red-50
          p-6
        "
      >
        <h1
          className="
            text-lg font-semibold
            text-red-900
          "
        >
          Unable to load financial dashboard
        </h1>

        <p
          className="
            mt-2 text-sm text-red-700
          "
        >
          {getErrorMessage(error)}
        </p>
      </div>
    );
  }

  if (!finance || !accounting) {
    return (
      <div
        className="
          rounded-2xl border
          border-slate-200 bg-white
          p-8 shadow-sm
        "
      >
        <p className="text-slate-600">
          Financial dashboard data is unavailable.
        </p>
      </div>
    );
  }

  return (
    <div
      className="
        mx-auto max-w-7xl
        space-y-6
      "
    >
      <header>
        <p
          className="
            text-sm font-semibold
            text-blue-600
          "
        >
          Finance
        </p>

        <h1
          className="
            mt-1 text-3xl font-bold
            text-slate-900
          "
        >
          Financial Dashboard
        </h1>

        <p
          className="
            mt-2 text-sm
            text-slate-600
          "
        >
          Monitor cash position,
          receivables, payables and
          accounting health.
        </p>
      </header>

      <section
        className="
          grid gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        <SummaryCard
          title="Bank Balance"
          value={formatAmount(
            finance
              .bank_accounts
              .total_balance,
          )}
          description={
            `${
              finance
                .bank_accounts
                .account_count
            } bank account(s)`
          }
          icon={<Landmark size={20} />}
        />

        <SummaryCard
          title="Receivables"
          value={formatAmount(
            finance
              .receivables
              .total_receivable,
          )}
          description="Outstanding customer balance"
          icon={<ArrowDown size={20} />}
        />

        <SummaryCard
          title="Payables"
          value={formatAmount(
            finance
              .payables
              .total_payable,
          )}
          description="Outstanding vendor balance"
          icon={<ArrowUp size={20} />}
        />

        <SummaryCard
          title="Net Cash Flow"
          value={formatAmount(
            finance
              .transactions
              .net_cash_flow,
          )}
          description="Recorded bank transaction flow"
          icon={<Banknote size={20} />}
        />
      </section>

      <section
        className="
          grid gap-4
          md:grid-cols-2
          xl:grid-cols-3
        "
      >
        <SummaryCard
          title="Money In"
          value={formatAmount(
            finance
              .transactions
              .total_in,
          )}
          description="Total recorded inflows"
          icon={<WalletCards size={20} />}
        />

        <SummaryCard
          title="Money Out"
          value={formatAmount(
            finance
              .transactions
              .total_out,
          )}
          description="Total recorded outflows"
          icon={<WalletCards size={20} />}
        />

        <SummaryCard
          title="Accounting As Of"
          value={
            accounting.as_of_date
              ? new Date(
                  accounting
                    .as_of_date,
                ).toLocaleDateString(
                  "en-IN",
                )
              : "Current"
          }
          description="Accounting report date"
          icon={<Scale size={20} />}
        />
      </section>

      <div
        className="
          grid gap-6
          xl:grid-cols-2
        "
      >
        <DashboardSection
          title="Liquidity"
          values={
            accounting.liquidity
          }
        />

        <DashboardSection
          title="Working Capital"
          values={
            accounting
              .working_capital
          }
        />

        <DashboardSection
          title="Profitability"
          values={
            accounting
              .profitability
          }
        />

        <DashboardSection
          title="Balance Sheet"
          values={
            accounting
              .balance_sheet
          }
        />

        <DashboardSection
          title="Trial Balance"
          values={
            accounting
              .trial_balance
          }
        />

        <section
          className="
            rounded-2xl border
            border-slate-200 bg-white
            p-6 shadow-sm
          "
        >
          <div
            className="
              flex items-center gap-3
            "
          >
            <Activity
              size={20}
              className="text-slate-700"
            />

            <h2
              className="
                text-lg font-semibold
                text-slate-900
              "
            >
              Accounting Health
            </h2>
          </div>

          <div className="mt-5">
            <DashboardSectionContent
              values={
                accounting
                  .accounting_health
              }
            />
          </div>
        </section>
      </div>
    </div>
  );
}

function DashboardSectionContent({
  values,
}: {
  values: Record<string, unknown>;
}) {
  const entries =
    Object.entries(values);

  if (entries.length === 0) {
    return (
      <p
        className="
          text-sm text-slate-500
        "
      >
        No accounting health data available.
      </p>
    );
  }

  return (
    <dl className="space-y-3">
      {entries.map(
        ([key, value]) => (
          <div
            key={key}
            className="
              flex items-start
              justify-between gap-4
              rounded-xl bg-slate-50
              p-4
            "
          >
            <dt
              className="
                text-sm text-slate-600
              "
            >
              {formatLabel(key)}
            </dt>

            <dd
              className="
                text-right text-sm
                font-semibold
                text-slate-900
              "
            >
              {formatValue(value)}
            </dd>
          </div>
        ),
      )}
    </dl>
  );
}