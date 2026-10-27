"use client";

import {
  useState,
} from "react";

import {
  CircleDollarSign,
  Eye,
  ReceiptText,
  Users,
} from "lucide-react";

import VendorBillDetailDialog from "@/features/vendor-bills/components/vendor-bill-detail-dialog";

import {
  useAccountsPayable,
} from "@/features/vendor-bills/hooks";

import type {
  VendorBillStatus,
} from "@/features/vendor-bills/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const statusStyles:
  Partial<
    Record<
      VendorBillStatus,
      string
    >
  > = {
    POSTED:
      "bg-blue-100 text-blue-700",
    PARTIALLY_PAID:
      "bg-amber-100 text-amber-700",
  };

function formatAmount(
  value: string,
): string {
  const amount =
    Number(value);

  if (
    Number.isNaN(amount)
  ) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
    },
  ).format(
    amount,
  );
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const parsedDate =
    new Date(value);

  if (
    Number.isNaN(
      parsedDate.getTime(),
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
    },
  ).format(
    parsedDate,
  );
}

function getErrorMessage(
  error: unknown,
): string {
  if (
    error
    instanceof
    APIRequestError
  ) {
    return error.message;
  }

  if (
    error
    instanceof
    Error
  ) {
    return error.message;
  }

  return (
    "Unable to load accounts payable."
  );
}

export default function AccountsPayablePage() {
  const [
    selectedBillId,
    setSelectedBillId,
  ] = useState("");

  const [
    detailOpen,
    setDetailOpen,
  ] = useState(false);

  const payableQuery =
    useAccountsPayable();

  const payable =
    payableQuery.data;

  const vendorBills =
    payable?.vendor_bills
    ??
    [];

  function openDetail(
    billId: string,
  ): void {
    setSelectedBillId(
      billId,
    );
    setDetailOpen(true);
  }

  return (
    <>
      <div className="space-y-6">
        <header>
          <p
            className="
              text-sm font-semibold
              text-blue-600
            "
          >
            Purchasing
          </p>

          <h1
            className="
              mt-1 text-2xl
              font-bold tracking-tight
              text-slate-950 sm:text-3xl
            "
          >
            Accounts Payable
          </h1>

          <p
            className="
              mt-2 max-w-2xl
              text-sm text-slate-600
            "
          >
            Monitor posted supplier bills
            and outstanding payment
            obligations.
          </p>
        </header>

        {payableQuery.isLoading
          ? (
            <section
              className="
                rounded-xl border
                border-slate-200 bg-white
                px-5 py-14 text-center
                text-sm text-slate-600
              "
            >
              Loading accounts payable…
            </section>
          )
          : null}

        {payableQuery.isError
          ? (
            <section
              className="
                rounded-xl border
                border-red-200 bg-red-50
                px-5 py-4 text-sm
                text-red-700
              "
            >
              {getErrorMessage(
                payableQuery.error,
              )}
            </section>
          )
          : null}

        {payable
          ? (
            <>
              <section
                className="
                  grid gap-4 sm:grid-cols-3
                "
              >
                <SummaryCard
                  label="Total outstanding"
                  value={formatAmount(
                    payable
                      .total_outstanding,
                  )}
                  icon={
                    CircleDollarSign
                  }
                  iconClass="
                    bg-red-100 text-red-700
                  "
                />

                <SummaryCard
                  label="Outstanding bills"
                  value={String(
                    payable.bill_count,
                  )}
                  icon={ReceiptText}
                  iconClass="
                    bg-amber-100
                    text-amber-700
                  "
                />

                <SummaryCard
                  label="Suppliers"
                  value={String(
                    payable
                      .supplier_count,
                  )}
                  icon={Users}
                  iconClass="
                    bg-blue-100
                    text-blue-700
                  "
                />
              </section>

              {vendorBills.length === 0
                ? (
                  <section
                    className="
                      rounded-xl border
                      border-dashed
                      border-slate-300
                      bg-white px-5 py-14
                      text-center
                    "
                  >
                    <CircleDollarSign
                      size={40}
                      className="
                        mx-auto
                        text-slate-400
                      "
                    />

                    <h2
                      className="
                        mt-4 font-bold
                        text-slate-950
                      "
                    >
                      No outstanding payables
                    </h2>

                    <p
                      className="
                        mt-2 text-sm
                        text-slate-600
                      "
                    >
                      All posted supplier bills
                      have been paid.
                    </p>
                  </section>
                )
                : (
                  <>
                    <section
                      className="
                        space-y-3 lg:hidden
                      "
                    >
                      {vendorBills.map(
                        (bill) => (
                          <article
                            key={bill.id}
                            className="
                              rounded-xl border
                              border-slate-200
                              bg-white p-4
                            "
                          >
                            <div
                              className="
                                flex items-start
                                justify-between
                                gap-3
                              "
                            >
                              <div>
                                <button
                                  type="button"
                                  onClick={() => {
                                    openDetail(
                                      bill.id,
                                    );
                                  }}
                                  className="
                                    font-bold
                                    text-blue-700
                                    hover:underline
                                  "
                                >
                                  {
                                    bill
                                      .bill_number
                                  }
                                </button>

                                <p
                                  className="
                                    mt-1 text-sm
                                    font-medium
                                    text-slate-950
                                  "
                                >
                                  {
                                    bill
                                      .supplier
                                      .name
                                  }
                                </p>
                              </div>

                              <span
                                className={`
                                  rounded-full
                                  px-2.5 py-1
                                  text-xs
                                  font-semibold
                                  ${
                                    statusStyles[
                                      bill.status
                                    ]
                                    ??
                                    (
                                      "bg-slate-100 "
                                      +
                                      "text-slate-700"
                                    )
                                  }
                                `}
                              >
                                {bill.status
                                  .toLowerCase()
                                  .replaceAll(
                                    "_",
                                    " ",
                                  )}
                              </span>
                            </div>

                            <dl
                              className="
                                mt-4 grid
                                grid-cols-2
                                gap-3 text-sm
                              "
                            >
                              <div>
                                <dt
                                  className="
                                    text-xs
                                    text-slate-500
                                  "
                                >
                                  Due date
                                </dt>

                                <dd
                                  className="
                                    mt-1
                                    font-medium
                                    text-slate-900
                                  "
                                >
                                  {formatDate(
                                    bill.due_date,
                                  )}
                                </dd>
                              </div>

                              <div>
                                <dt
                                  className="
                                    text-xs
                                    text-slate-500
                                  "
                                >
                                  Balance
                                </dt>

                                <dd
                                  className="
                                    mt-1 font-bold
                                    text-red-700
                                  "
                                >
                                  {formatAmount(
                                    bill
                                      .balance_due,
                                  )}
                                </dd>
                              </div>
                            </dl>

                            <button
                              type="button"
                              onClick={() => {
                                openDetail(
                                  bill.id,
                                );
                              }}
                              className="
                                mt-4 inline-flex
                                w-full items-center
                                justify-center gap-2
                                rounded-lg border
                                border-slate-300
                                px-4 py-2 text-sm
                                font-semibold
                                text-slate-700
                              "
                            >
                              <Eye size={17} />
                              View bill
                            </button>
                          </article>
                        ),
                      )}
                    </section>

                    <section
                      className="
                        hidden overflow-hidden
                        rounded-xl border
                        border-slate-200
                        bg-white lg:block
                      "
                    >
                      <div
                        className="
                          overflow-x-auto
                        "
                      >
                        <table
                          className="
                            min-w-full divide-y
                            divide-slate-200
                          "
                        >
                          <thead
                            className="
                              bg-slate-50
                            "
                          >
                            <tr>
                              {[
                                "Bill",
                                "Supplier",
                                "Bill date",
                                "Due date",
                                "Total",
                                "Paid",
                                "Balance",
                                "Actions",
                              ].map(
                                (heading) => (
                                  <th
                                    key={heading}
                                    className="
                                      whitespace-nowrap
                                      px-4 py-3
                                      text-left
                                      text-xs
                                      font-semibold
                                      uppercase
                                      tracking-wide
                                      text-slate-600
                                    "
                                  >
                                    {heading}
                                  </th>
                                ),
                              )}
                            </tr>
                          </thead>

                          <tbody
                            className="
                              divide-y
                              divide-slate-200
                            "
                          >
                            {vendorBills.map(
                              (bill) => (
                                <tr
                                  key={bill.id}
                                  className="
                                    hover:bg-slate-50
                                  "
                                >
                                  <td
                                    className="
                                      px-4 py-4
                                    "
                                  >
                                    <button
                                      type="button"
                                      onClick={() => {
                                        openDetail(
                                          bill.id,
                                        );
                                      }}
                                      className="
                                        font-semibold
                                        text-blue-700
                                        hover:underline
                                      "
                                    >
                                      {
                                        bill
                                          .bill_number
                                      }
                                    </button>
                                  </td>

                                  <td
                                    className="
                                      min-w-48
                                      px-4 py-4
                                      text-sm
                                      font-medium
                                      text-slate-950
                                    "
                                  >
                                    {
                                      bill
                                        .supplier.name
                                    }
                                  </td>

                                  <td
                                    className="
                                      whitespace-nowrap
                                      px-4 py-4
                                      text-sm
                                      text-slate-700
                                    "
                                  >
                                    {formatDate(
                                      bill
                                        .bill_date,
                                    )}
                                  </td>

                                  <td
                                    className="
                                      whitespace-nowrap
                                      px-4 py-4
                                      text-sm
                                      text-slate-700
                                    "
                                  >
                                    {formatDate(
                                      bill
                                        .due_date,
                                    )}
                                  </td>

                                  <td
                                    className="
                                      whitespace-nowrap
                                      px-4 py-4
                                      text-sm
                                      text-slate-700
                                    "
                                  >
                                    {formatAmount(
                                      bill
                                        .total_amount,
                                    )}
                                  </td>

                                  <td
                                    className="
                                      whitespace-nowrap
                                      px-4 py-4
                                      text-sm
                                      text-slate-700
                                    "
                                  >
                                    {formatAmount(
                                      bill
                                        .amount_paid,
                                    )}
                                  </td>

                                  <td
                                    className="
                                      whitespace-nowrap
                                      px-4 py-4
                                      text-sm
                                      font-bold
                                      text-red-700
                                    "
                                  >
                                    {formatAmount(
                                      bill
                                        .balance_due,
                                    )}
                                  </td>

                                  <td
                                    className="
                                      px-4 py-4
                                    "
                                  >
                                    <button
                                      type="button"
                                      onClick={() => {
                                        openDetail(
                                          bill.id,
                                        );
                                      }}
                                      className="
                                        rounded-lg p-2
                                        text-slate-500
                                        hover:bg-blue-50
                                        hover:text-blue-700
                                      "
                                    >
                                      <Eye
                                        size={18}
                                      />
                                    </button>
                                  </td>
                                </tr>
                              ),
                            )}
                          </tbody>
                        </table>
                      </div>
                    </section>
                  </>
                )}
            </>
          )
          : null}
      </div>

      <VendorBillDetailDialog
        open={detailOpen}
        billId={selectedBillId}
        onClose={() => {
          setDetailOpen(false);
        }}
      />
    </>
  );
}

interface SummaryCardProps {
  label: string;
  value: string;
  icon: typeof CircleDollarSign;
  iconClass: string;
}

function SummaryCard({
  label,
  value,
  icon: Icon,
  iconClass,
}: SummaryCardProps) {
  return (
    <div
      className="
        rounded-xl border
        border-slate-200 bg-white
        p-4 shadow-sm
      "
    >
      <div
        className="
          flex items-center gap-3
        "
      >
        <div
          className={`
            flex size-10 items-center
            justify-center rounded-lg
            ${iconClass}
          `}
        >
          <Icon size={20} />
        </div>

        <div>
          <p
            className="
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            {label}
          </p>

          <p
            className="
              mt-1 text-xl font-bold
              text-slate-950
            "
          >
            {value}
          </p>
        </div>
      </div>
    </div>
  );
}