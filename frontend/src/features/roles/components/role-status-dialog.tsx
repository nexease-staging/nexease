"use client";

import {
  useState,
} from "react";

import {
  Loader2,
  Power,
  PowerOff,
  X,
} from "lucide-react";

import {
  RoleSummary,
  useActivateRole,
  useDeactivateRole,
} from "@/features/roles";

interface RoleStatusDialogProps {
  open: boolean;
  role: RoleSummary | null;
  action: "activate" | "deactivate";
  onClose: () => void;
}

export function RoleStatusDialog({
  open,
  role,
  action,
  onClose,
}: RoleStatusDialogProps) {
  const activateMutation =
    useActivateRole();

  const deactivateMutation =
    useDeactivateRole();

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );

  if (
    !open
    ||
    !role
  ) {
    return null;
  }

  const isActivating =
    action === "activate";

  const isSubmitting =
    activateMutation.isPending
    ||
    deactivateMutation.isPending;

  const handleConfirm =
    async () => {
      setErrorMessage(null);

      try {
        if (isActivating) {
          await activateMutation.mutateAsync(
            role.id,
          );
        } else {
          await deactivateMutation.mutateAsync(
            role.id,
          );
        }

        onClose();
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : (
                isActivating
                  ? "Unable to activate role."
                  : "Unable to deactivate role."
              ),
        );
      }
    };

  return (
    <div
      role="presentation"
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-slate-950/40 p-4
      "
      onMouseDown={(event) => {
        if (
          event.target
          ===
          event.currentTarget
          &&
          !isSubmitting
        ) {
          onClose();
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="role-status-dialog-title"
        className="
          w-full max-w-md
          overflow-hidden rounded-2xl
          bg-white shadow-2xl
        "
      >
        <div
          className="
            flex items-start
            justify-between gap-4
            border-b border-slate-200
            px-6 py-5
          "
        >
          <div
            className="
              flex items-start gap-3
            "
          >
            <div
              className={`
                rounded-xl p-2.5
                ${
                  isActivating
                    ? (
                        "bg-emerald-50 "
                        +
                        "text-emerald-600"
                      )
                    : (
                        "bg-red-50 "
                        +
                        "text-red-600"
                      )
                }
              `}
            >
              {isActivating ? (
                <Power size={22} />
              ) : (
                <PowerOff size={22} />
              )}
            </div>

            <div>
              <h2
                id="role-status-dialog-title"
                className="
                  text-lg font-bold
                  text-slate-900
                "
              >
                {isActivating
                  ? "Activate role"
                  : "Deactivate role"}
              </h2>

              <p
                className="
                  mt-1 text-sm
                  text-slate-500
                "
              >
                {role.name}
              </p>
            </div>
          </div>

          <button
            type="button"
            disabled={isSubmitting}
            onClick={onClose}
            aria-label="Close role status dialog"
            className="
              rounded-lg p-2
              text-slate-500
              hover:bg-slate-100
              disabled:opacity-50
            "
          >
            <X size={19} />
          </button>
        </div>

        <div
          className="
            space-y-4 px-6 py-5
          "
        >
          <p
            className="
              text-sm leading-6
              text-slate-600
            "
          >
            {isActivating
              ? (
                  <>
                    Activate{" "}
                    <strong>
                      {role.name}
                    </strong>
                    ? The role will become
                    available for active use.
                  </>
                )
              : (
                  <>
                    Deactivate{" "}
                    <strong>
                      {role.name}
                    </strong>
                    ? The role will no longer
                    be active for normal use.
                  </>
                )}
          </p>

          {!isActivating ? (
            <div
              className="
                rounded-xl border
                border-amber-200
                bg-amber-50 px-4 py-3
                text-sm text-amber-800
              "
            >
              Deactivation may be rejected or
              require attention if active users
              are currently assigned to this role.
            </div>
          ) : null}

          {errorMessage ? (
            <div
              className="
                rounded-xl border
                border-red-200
                bg-red-50 px-4 py-3
                text-sm text-red-700
              "
            >
              {errorMessage}
            </div>
          ) : null}
        </div>

        <div
          className="
            flex justify-end gap-3
            border-t border-slate-200
            bg-slate-50 px-6 py-4
          "
        >
          <button
            type="button"
            disabled={isSubmitting}
            onClick={onClose}
            className="
              rounded-lg border
              border-slate-300 bg-white
              px-4 py-2
              text-sm font-semibold
              text-slate-700
              hover:bg-slate-50
              disabled:opacity-50
            "
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => {
              void handleConfirm();
            }}
            className={`
              inline-flex items-center
              gap-2 rounded-lg
              px-4 py-2
              text-sm font-semibold
              text-white
              disabled:cursor-not-allowed
              disabled:opacity-50
              ${
                isActivating
                  ? (
                      "bg-emerald-600 "
                      +
                      "hover:bg-emerald-700"
                    )
                  : (
                      "bg-red-600 "
                      +
                      "hover:bg-red-700"
                    )
              }
            `}
          >
            {isSubmitting ? (
              <Loader2
                size={16}
                className="animate-spin"
              />
            ) : isActivating ? (
              <Power size={16} />
            ) : (
              <PowerOff size={16} />
            )}

            {isActivating
              ? "Activate role"
              : "Deactivate role"}
          </button>
        </div>
      </div>
    </div>
  );
}