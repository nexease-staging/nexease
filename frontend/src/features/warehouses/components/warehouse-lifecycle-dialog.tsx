"use client";

import {
  AlertTriangle,
  LoaderCircle,
} from "lucide-react";

import {
  useActivateWarehouse,
  useDeactivateWarehouse,
} from "@/features/warehouses/hooks";

import type {
  WarehouseSummary,
} from "@/features/warehouses/types";

interface WarehouseLifecycleDialogProps {
  open: boolean;
  warehouse: WarehouseSummary | null;
  onClose: () => void;
}

export default function WarehouseLifecycleDialog({
  open,
  warehouse,
  onClose,
}: WarehouseLifecycleDialogProps) {
  const activateMutation =
    useActivateWarehouse();

  const deactivateMutation =
    useDeactivateWarehouse();

  if (
    !open
    ||
    !warehouse
  ) {
    return null;
  }

  const activating =
    !warehouse.is_active;

  const mutation = activating
    ? activateMutation
    : deactivateMutation;

  async function confirm():
    Promise<void> {
    if (!warehouse) {
      return;
    }

    if (activating) {
      await activateMutation.mutateAsync(
        warehouse.id,
      );
    } else {
      await deactivateMutation.mutateAsync(
        warehouse.id,
      );
    }

    onClose();
  }

  return (
    <div
      className="
        fixed inset-0 z-50
        flex items-center
        justify-center bg-slate-950/50
        p-4
      "
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target
          ===
          event.currentTarget
          &&
          !mutation.isPending
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          "warehouse-lifecycle-title"
        }
        className="
          w-full max-w-md
          rounded-2xl bg-white p-6
          shadow-2xl
        "
      >
        <div
          className="
            flex size-11 items-center
            justify-center rounded-full
            bg-amber-100 text-amber-700
          "
        >
          <AlertTriangle size={22} />
        </div>

        <h2
          id="warehouse-lifecycle-title"
          className="
            mt-4 text-lg font-bold
            text-slate-900
          "
        >
          {activating
            ? "Activate warehouse?"
            : "Deactivate warehouse?"}
        </h2>

        <p
          className="
            mt-2 text-sm leading-6
            text-slate-600
          "
        >
          {activating
            ? (
              <>
                <strong>
                  {warehouse.name}
                </strong>
                {" "}will become available
                for inventory operations.
              </>
            )
            : (
              <>
                <strong>
                  {warehouse.name}
                </strong>
                {" "}will no longer be
                available for new inventory
                operations or transfers.
              </>
            )}
        </p>

        {mutation.error ? (
          <div
            role="alert"
            className="
              mt-4 rounded-lg border
              border-red-200 bg-red-50
              px-4 py-3 text-sm
              text-red-700
            "
          >
            {mutation.error.message}
          </div>
        ) : null}

        <div
          className="
            mt-6 flex justify-end gap-3
          "
        >
          <button
            type="button"
            disabled={mutation.isPending}
            onClick={onClose}
            className="
              rounded-lg border
              border-slate-300 bg-white
              px-4 py-2 text-sm
              font-semibold text-slate-700
              hover:bg-slate-50
              disabled:opacity-50
            "
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={mutation.isPending}
            onClick={() => {
              void confirm();
            }}
            className={
              activating
                ? (
                  "inline-flex items-center gap-2 "
                  +
                  "rounded-lg bg-emerald-600 "
                  +
                  "px-4 py-2 text-sm font-semibold "
                  +
                  "text-white hover:bg-emerald-700 "
                  +
                  "disabled:opacity-50"
                )
                : (
                  "inline-flex items-center gap-2 "
                  +
                  "rounded-lg bg-red-600 "
                  +
                  "px-4 py-2 text-sm font-semibold "
                  +
                  "text-white hover:bg-red-700 "
                  +
                  "disabled:opacity-50"
                )
            }
          >
            {mutation.isPending ? (
              <LoaderCircle
                size={16}
                className="animate-spin"
              />
            ) : null}

            {activating
              ? "Activate"
              : "Deactivate"}
          </button>
        </div>
      </section>
    </div>
  );
}