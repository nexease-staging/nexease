"use client";
import { FormSheet } from "@/components/form/form-sheet";
import { paymentRetryKey } from "@/lib/payments/retry-key";
import { useRef } from "react";
import SearchSelect from "@/components/search-select";


import {
  useState,
} from "react";

import {
  CreditCard,
} from "lucide-react";

import {
  useRecordVendorBillPayment,
  useVendorBillBankAccounts,
} from "@/features/vendor-bills/hooks";

import type {
  SupplierPaymentMethod,
  VendorBillDetail,
} from "@/features/vendor-bills/types";

import {
  APIRequestError,
} from "@/lib/api/client";

interface VendorBillPaymentDialogProps {
  open: boolean;
  vendorBill:
    VendorBillDetail | null;
  onClose: () => void;
  onRecorded?: () => void;
}

const paymentMethods:
  Array<{
    value: SupplierPaymentMethod;
    label: string;
  }> = [
    {
      value: "BANK_TRANSFER",
      label: "Bank transfer",
    },
    {
      value: "UPI",
      label: "UPI",
    },
    {
      value: "CHEQUE",
      label: "Cheque",
    },
    {
      value: "CASH",
      label: "Cash",
    },
    {
      value: "CARD",
      label: "Card",
    },
    {
      value: "OTHER",
      label: "Other",
    },
  ];

function todayValue(): string {
  const now = new Date();

  const offset =
    now.getTimezoneOffset()
    *
    60_000;

  return new Date(
    now.getTime() - offset,
  )
    .toISOString()
    .slice(
      0,
      10,
    );
}

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
    "Unable to record the payment."
  );
}

export default function VendorBillPaymentDialog({
  open,
  vendorBill,
  onClose,
  onRecorded,
}: VendorBillPaymentDialogProps) {
  const [
    amount,
    setAmount,
  ] = useState("");

  const [
    paymentMethod,
    setPaymentMethod,
  ] = useState<
    SupplierPaymentMethod
  >(
    "BANK_TRANSFER",
  );

  const [
    bankAccountId,
    setBankAccountId,
  ] = useState("");

  const [
    paymentDate,
    setPaymentDate,
  ] = useState(
    todayValue(),
  );

  const [
    referenceNumber,
    setReferenceNumber,
  ] = useState("");

  const [
    notes,
    setNotes,
  ] = useState("");

  const [
    formError,
    setFormError,
  ] = useState<string | null>(
    null,
  );

  const submitting = useRef(false);
  const bankAccountQuery =
    useVendorBillBankAccounts(
      open,
    );

  const paymentMutation =
    useRecordVendorBillPayment();

  if (
    !open
    ||
    !vendorBill
  ) {
    return null;
  }
  const activeVendorBill =
    vendorBill;

  function resetDialog():
    void {
    setAmount("");
    setPaymentMethod(
      "BANK_TRANSFER",
    );
    setBankAccountId("");
    setPaymentDate(
      todayValue(),
    );
    setReferenceNumber("");
    setNotes("");
    setFormError(null);
  }

  function closeDialog():
    void {
    if (
      paymentMutation.isPending
    ) {
      return;
    }

    resetDialog();
    onClose();
  }

  async function submit():
    Promise<void> {
    setFormError(null);

    const paymentAmount =
      Number(amount);

    const balanceDue =
      Number(
        activeVendorBill.balance_due,
      );

    if (
      !Number.isFinite(
        paymentAmount,
      )
      ||
      paymentAmount <= 0
    ) {
      setFormError(
        (
          "Payment amount must be "
          +
          "greater than zero."
        ),
      );
      return;
    }

    if (
      Number.isFinite(balanceDue)
      &&
      paymentAmount > balanceDue
    ) {
      setFormError(
        (
          "Payment cannot exceed "
          +
          "the outstanding balance."
        ),
      );
      return;
    }

    if (!bankAccountId) {
      setFormError(
        "Select a bank account.",
      );
      return;
    }

    if (submitting.current) return;
    submitting.current = true;
    try {
      const input = {
            amount,
            payment_method:
              paymentMethod,
            bank_account_id:
              bankAccountId,
            payment_date:
              paymentDate
              ||
              undefined,
            reference_number:
              referenceNumber
                .trim()
              ||
              undefined,
            notes:
              notes.trim()
              ||
              undefined,
      };
      const retry = await paymentRetryKey(activeVendorBill.id, input);
      await paymentMutation
        .mutateAsync({
          billId:
            activeVendorBill.id,
          input: { ...input, request_key: retry.requestKey },
        });
      retry.complete();

      resetDialog();

      if (onRecorded) {
        onRecorded();
      } else {
        onClose();
      }
    } catch (error) {
      setFormError(
        getErrorMessage(error),
      );
    } finally {
      submitting.current = false;
    }
  }

  return (
    <FormSheet title={"Record payment"} subtitle={`${vendorBill.bill_number} · Balance ${formatAmount(vendorBill.balance_due)}`} onClose={closeDialog} busy={paymentMutation.isPending} size="md" closeLabel="Close dialog">
      

        <div className="flex flex-col gap-4">
          <div
            className="
              space-y-4 rounded-xl
              border border-slate-200
              bg-white p-4 shadow-sm
              sm:p-5
            "
          >
            <label
              className="
                block text-sm
                font-semibold
                text-slate-800
              "
            >
              Payment amount

              <input
                type="number"
                min="0.01"
                step="0.01"
                max={
                  vendorBill.balance_due
                }
                value={amount}
                disabled={
                  paymentMutation.isPending
                }
                onChange={(event) => {
                  setAmount(
                    event.currentTarget
                      .value,
                  );

                  setFormError(null);
                }}
                className="
                  mt-2 h-11 w-full
                  rounded-lg border
                  border-slate-300
                  bg-white px-3
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:bg-slate-100
                "
              />

              <button
                type="button"
                disabled={
                  paymentMutation.isPending
                }
                onClick={() => {
                  setAmount(
                    vendorBill.balance_due,
                  );
                }}
                className="
                  mt-2 text-xs
                  font-semibold text-blue-700
                  hover:underline
                "
              >
                Pay full balance
              </button>
            </label>

            <div
              className="
                grid gap-4 sm:grid-cols-2
              "
            >
              <label
                className="
                  block text-sm
                  font-semibold
                  text-slate-800
                "
              >
                Payment method

                <SearchSelect
                  value={paymentMethod}
                  disabled={
                    paymentMutation
                      .isPending
                  }
                    onChange={(event) => {
                    const selectedMethod = event.currentTarget.value as SupplierPaymentMethod;

                    setPaymentMethod(
                        selectedMethod,
                    );
                    }}
                  className="
                    mt-2 h-11 w-full
                    rounded-lg border
                    border-slate-300
                    bg-white px-3
                    text-sm text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                >
                  {paymentMethods.map(
                    (method) => (
                      <option
                        key={method.value}
                        value={method.value}
                      >
                        {method.label}
                      </option>
                    ),
                  )}
                </SearchSelect>
              </label>

              <label
                className="
                  block text-sm
                  font-semibold
                  text-slate-800
                "
              >
                Payment date

                <input
                  type="date"
                  value={paymentDate}
                  disabled={
                    paymentMutation
                      .isPending
                  }
                  onChange={(event) => {
                    setPaymentDate(
                      event.currentTarget
                        .value,
                    );
                  }}
                  className="
                    mt-2 h-11 w-full
                    rounded-lg border
                    border-slate-300
                    bg-white px-3
                    text-sm text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                />
              </label>
            </div>

            <label
              className="
                block text-sm
                font-semibold
                text-slate-800
              "
            >
              Bank account

              <SearchSelect
                value={bankAccountId}
                disabled={
                  bankAccountQuery
                    .isLoading
                  ||
                  paymentMutation
                    .isPending
                }
                onChange={(event) => {
                  setBankAccountId(
                    event.currentTarget
                      .value,
                  );

                  setFormError(null);
                }}
                className="
                  mt-2 h-11 w-full
                  rounded-lg border
                  border-slate-300
                  bg-white px-3
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:bg-slate-100
                "
              >
                <option value="">
                  Select bank account
                </option>

                {bankAccountQuery
                  .data
                  ?.map(
                    (bankAccount) => (
                      <option
                        key={
                          bankAccount.id
                        }
                        value={
                          bankAccount.id
                        }
                      >
                        {
                          bankAccount
                            .account_name
                        }
                        {" — "}
                        {
                          bankAccount
                            .masked_account_number
                          ??
                          bankAccount
                            .account_type
                        }
                      </option>
                    ),
                  )}
              </SearchSelect>
            </label>

            {bankAccountQuery.isError
              ? (
                <p
                  className="
                    text-sm text-red-700
                  "
                >
                  {getErrorMessage(
                    bankAccountQuery.error,
                  )}
                </p>
              )
              : null}

            <label
              className="
                block text-sm
                font-semibold
                text-slate-800
              "
            >
              Reference number

              <input
                type="text"
                maxLength={100}
                value={referenceNumber}
                disabled={
                  paymentMutation.isPending
                }
                onChange={(event) => {
                  setReferenceNumber(
                    event.currentTarget
                      .value,
                  );
                }}
                className="
                  mt-2 h-11 w-full
                  rounded-lg border
                  border-slate-300
                  bg-white px-3
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>

            <label
              className="
                block text-sm
                font-semibold
                text-slate-800
              "
            >
              Notes

              <textarea
                rows={3}
                maxLength={1000}
                value={notes}
                disabled={
                  paymentMutation.isPending
                }
                onChange={(event) => {
                  setNotes(
                    event.currentTarget
                      .value,
                  );
                }}
                className="
                  mt-2 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 py-2
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>

            {formError
              ? (
                <div
                  className="
                    rounded-lg border
                    border-red-200 bg-red-50
                    px-4 py-3 text-sm
                    text-red-700
                  "
                >
                  {formError}
                </div>
              )
              : null}
          </div>
        </div>

        <footer className="nxf-actions"><span /><div className="nxf-buttons">
          <button
            type="button"
            disabled={
              paymentMutation.isPending
            }
            onClick={closeDialog}
            className="nx-button nx-secondary nxf-secondary-sm"
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={
              paymentMutation.isPending
            }
            onClick={() => {
              void submit();
            }}
            className="nx-button"
          >
            <CreditCard size={17} />

            {paymentMutation.isPending
              ? "Recording…"
              : "Record payment"}
          </button>
        </div></footer>
      </FormSheet>
  );
}
