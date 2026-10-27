import {
  AlertCircle,
  Boxes,
  Landmark,
  PackageSearch,
  ReceiptText,
  ShoppingCart,
} from "lucide-react";

import type {
  DashboardAlerts,
  DashboardRecentActivity,
} from "@/features/dashboard/types";


interface DashboardAlertsActivityProps {
  alerts:
    DashboardAlerts;

  recentActivity:
    DashboardRecentActivity[];
}


function formatCurrency(
  value: string | null,
): string {
  if (
    value === null
    ||
    value === ""
  ) {
    return "—";
  }

  const amount =
    Number(
      value,
    );

  if (
    !Number.isFinite(
      amount,
    )
  ) {
    return "—";
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


function formatDateTime(
  value: string,
): string {
  const date =
    new Date(
      value,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(
    date,
  );
}


function getActivityIcon(
  activityType:
    DashboardRecentActivity[
      "activity_type"
    ],
) {
  switch (
    activityType
  ) {
    case "INVOICE":
      return ReceiptText;

    case "VENDOR_BILL":
      return ShoppingCart;

    case "BANK_TRANSACTION":
      return Landmark;

    case "STOCK_MOVEMENT":
      return Boxes;

    default:
      return PackageSearch;
  }
}


function getActivityLabel(
  activityType:
    DashboardRecentActivity[
      "activity_type"
    ],
): string {
  switch (
    activityType
  ) {
    case "INVOICE":
      return "Invoice";

    case "VENDOR_BILL":
      return "Vendor Bill";

    case "BANK_TRANSACTION":
      return "Bank Transaction";

    case "STOCK_MOVEMENT":
      return "Stock Movement";

    default:
      return "Activity";
  }
}


export default function DashboardAlertsActivity({
  alerts,
  recentActivity,
}: DashboardAlertsActivityProps) {
  const alertItems = [
    {
      label:
        "Overdue Invoices",

      value:
        alerts.overdue_invoices,

      description:
        "Invoices currently past their due date",
    },

    {
      label:
        "Overdue Bills",

      value:
        alerts.overdue_bills,

      description:
        "Vendor bills currently past their due date",
    },

    {
      label:
        "Out of Stock Items",

      value:
        alerts.out_of_stock_items,

      description:
        "Items with no available inventory",
    },
  ];

  return (
    <section
      className="
        grid
        gap-6
        xl:grid-cols-[0.8fr_1.2fr]
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
            flex
            items-center
            gap-3
          "
        >
          <div
            className="
              flex
              h-10
              w-10
              items-center
              justify-center
              rounded-xl
              bg-amber-50
              text-amber-700
            "
          >
            <AlertCircle
              className="
                h-5
                w-5
              "
            />
          </div>

          <div>
            <h2
              className="
                text-base
                font-semibold
                text-slate-950
              "
            >
              Alerts
            </h2>

            <p
              className="
                mt-0.5
                text-sm
                text-slate-500
              "
            >
              Items requiring attention
            </p>
          </div>
        </div>

        <div
        className="
            mt-5
            min-h-0
            flex-1
            space-y-3
            overflow-y-auto
            pr-1
        "
        >
          {
            alertItems.map(
              (
                item,
              ) => {
                const hasAlert =
                  item.value
                  > 0;

                return (
                  <div
                    key={
                      item.label
                    }
                    className={`
                      rounded-xl
                      border
                      p-4
                      ${
                        hasAlert
                          ? `
                            border-amber-200
                            bg-amber-50/50
                          `
                          : `
                            border-slate-200
                            bg-slate-50
                          `
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
                      <div>
                        <p
                          className="
                            text-sm
                            font-semibold
                            text-slate-900
                          "
                        >
                          {
                            item.label
                          }
                        </p>

                        <p
                          className="
                            mt-1
                            text-xs
                            leading-5
                            text-slate-500
                          "
                        >
                          {
                            item.description
                          }
                        </p>
                      </div>

                      <span
                        className={`
                          inline-flex
                          min-w-8
                          items-center
                          justify-center
                          rounded-full
                          px-2.5
                          py-1
                          text-xs
                          font-bold
                          ${
                            hasAlert
                              ? `
                                bg-amber-100
                                text-amber-800
                              `
                              : `
                                bg-emerald-50
                                text-emerald-700
                              `
                          }
                        `}
                      >
                        {
                          item.value
                        }
                      </span>
                    </div>
                  </div>
                );
              },
            )
          }
        </div>
      </article>

      <article
        className="
        flex
        h-[520px]
        flex-col
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
            border-b
            border-slate-100
            p-5
          "
        >
          <h2
            className="
              text-base
              font-semibold
              text-slate-950
            "
          >
            Recent Activity
          </h2>

          <p
            className="
              mt-1
              text-sm
              text-slate-500
            "
          >
            Latest activity across the organization
          </p>
        </div>

        {
          recentActivity.length
          > 0
            ? (
                <div
                className="
                    min-h-0
                    flex-1
                    divide-y
                    divide-slate-100
                    overflow-y-auto
                "
                >
                {
                  recentActivity.map(
                    (
                      activity,
                    ) => {
                      const Icon =
                        getActivityIcon(
                          activity
                            .activity_type,
                        );

                      return (
                        <div
                          key={
                            [
                              activity
                                .activity_type,
                              activity
                                .reference_id,
                              activity
                                .activity_date,
                            ].join(
                              "-",
                            )
                          }
                          className="
                            flex
                            gap-4
                            p-5
                          "
                        >
                          <div
                            className="
                              flex
                              h-10
                              w-10
                              shrink-0
                              items-center
                              justify-center
                              rounded-xl
                              bg-slate-100
                              text-slate-700
                            "
                          >
                            <Icon
                              className="
                                h-5
                                w-5
                              "
                            />
                          </div>

                          <div
                            className="
                              min-w-0
                              flex-1
                            "
                          >
                            <div
                              className="
                                flex
                                flex-col
                                gap-1
                                sm:flex-row
                                sm:items-start
                                sm:justify-between
                              "
                            >
                              <div
                                className="
                                  min-w-0
                                "
                              >
                                <p
                                  className="
                                    truncate
                                    text-sm
                                    font-semibold
                                    text-slate-900
                                  "
                                  title={
                                    activity
                                      .description
                                  }
                                >
                                  {
                                    activity
                                      .description
                                  }
                                </p>

                                <div
                                  className="
                                    mt-1
                                    flex
                                    flex-wrap
                                    items-center
                                    gap-x-2
                                    gap-y-1
                                    text-xs
                                    text-slate-500
                                  "
                                >
                                  <span>
                                    {
                                      getActivityLabel(
                                        activity
                                          .activity_type,
                                      )
                                    }
                                  </span>

                                  <span>
                                    ·
                                  </span>

                                  <span
                                    className="
                                      font-medium
                                      text-slate-600
                                    "
                                  >
                                    {
                                      activity
                                        .reference_number
                                    }
                                  </span>
                                </div>
                              </div>

                              <span
                                className="
                                  shrink-0
                                  text-xs
                                  text-slate-400
                                "
                              >
                                {
                                  formatDateTime(
                                    activity
                                      .activity_date,
                                  )
                                }
                              </span>
                            </div>

                            {
                              (
                                activity.amount
                                !== null
                                ||
                                activity.quantity
                              )
                                ? (
                                  <div
                                    className="
                                      mt-3
                                      flex
                                      flex-wrap
                                      gap-2
                                    "
                                  >
                                    {
                                      activity.amount
                                      !== null
                                        ? (
                                          <span
                                            className="
                                              rounded-lg
                                              bg-slate-100
                                              px-2.5
                                              py-1
                                              text-xs
                                              font-semibold
                                              text-slate-700
                                            "
                                          >
                                            {
                                              formatCurrency(
                                                activity
                                                  .amount,
                                              )
                                            }
                                          </span>
                                        )
                                        : null
                                    }

                                    {
                                      activity.quantity
                                        ? (
                                          <span
                                            className="
                                              rounded-lg
                                              bg-slate-100
                                              px-2.5
                                              py-1
                                              text-xs
                                              font-semibold
                                              text-slate-700
                                            "
                                          >
                                            Qty{" "}
                                            {
                                              activity
                                                .quantity
                                            }
                                          </span>
                                        )
                                        : null
                                    }
                                  </div>
                                )
                                : null
                            }
                          </div>
                        </div>
                      );
                    },
                  )
                }
              </div>
            )
            : (
              <div
                className="
                  flex
                  min-h-64
                  items-center
                  justify-center
                  p-6
                "
              >
                <p
                  className="
                    text-sm
                    text-slate-500
                  "
                >
                  No recent activity
                </p>
              </div>
            )
        }
      </article>
    </section>
  );
}