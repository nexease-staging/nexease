"use client";
import ScopeSettings from "@/features/business/scope-settings";

import {
  useState,
} from "react";

import {
  Building2,
  RefreshCw,
  Save,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  useOrganization,
  useUpdateOrganization,
} from "@/features/organizations/hooks";

import type {
  OrganizationDetail,
  UpdateOrganizationInput,
} from "@/features/organizations/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";


interface OrganizationFormState {
  name: string;
  email: string;
  phone: string;
  address: string;
  country: string;
  currency: string;
  timezone: string;
}


const EMPTY_FORM: OrganizationFormState = {
  name: "",
  email: "",
  phone: "",
  address: "",
  country: "",
  currency: "",
  timezone: "",
};

function buildOrganizationForm(
  organization: OrganizationDetail,
): OrganizationFormState {
  return {
    name:
      organization.name,
    email:
      organization.email,
    phone:
      organization.phone ?? "",
    address:
      organization.address ?? "",
    country:
      organization.country,
    currency:
      organization.currency,
    timezone:
      organization.timezone,
  };
}

export default function OrganizationSettingsPage() {
  const {
    authentication,
    refreshAuthentication,
  } = useAuth();

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canUpdate = hasPermission(
    permissions,
    "organizations.update",
  );

  const organizationQuery =
    useOrganization(
      Boolean(authentication),
    );

  const updateMutation =
    useUpdateOrganization();

const [
  formOverride,
  setFormOverride,
] = useState<OrganizationFormState | null>(
  null,
);

  const [
    successMessage,
    setSuccessMessage,
  ] = useState<string | null>(
    null,
  );

  const [
    actionError,
    setActionError,
  ] = useState<string | null>(
    null,
  );

  const organization =
    organizationQuery.data;

  const form =
    formOverride
    ??
    (
      organization
        ? buildOrganizationForm(
            organization,
          )
        : EMPTY_FORM
    );

  if (!authentication) {
    return null;
  }


  if (!canUpdate) {
    return (
      <section
        className="
          rounded-2xl border
          border-amber-200 bg-amber-50
          p-6
        "
      >

        <h1
          className="
            text-lg font-semibold
            text-amber-900
          "
        >
          Organization access restricted
        </h1>

        <p
          className="
            mt-2 text-sm text-amber-800
          "
        >
          Your role does not include the
          organizations.update permission.
        </p>
      </section>
    );
  }

  function updateField(
    field: keyof OrganizationFormState,
    value: string,
  ): void {
    setFormOverride(
      (current) => ({
        ...(
          current
          ??
          (
            organization
              ? buildOrganizationForm(
                  organization,
                )
              : EMPTY_FORM
          )
        ),
        [field]: value,
      }),
    );

    setSuccessMessage(
      null,
    );

    setActionError(
      null,
    );
  }

  function resetForm(): void {
    setFormOverride(
      null,
    );

    setSuccessMessage(
      null,
    );

    setActionError(
      null,
    );
  }

  async function saveOrganization():
  Promise<void> {
    if (!organization) {
      return;
    }

    setSuccessMessage(
      null,
    );

    setActionError(
      null,
    );

    const input: UpdateOrganizationInput = {
      name:
        form.name.trim(),
      email:
        form.email.trim(),
      phone:
        form.phone.trim(),
      address:
        form.address.trim(),
      country:
        form.country.trim(),
      currency:
        form.currency
          .trim()
          .toUpperCase(),
      timezone:
        form.timezone.trim(),
    };

    try {
      const updatedOrganization =
        await updateMutation.mutateAsync(
          input,
        );

      setFormOverride(
        buildOrganizationForm(
          updatedOrganization,
        ),
      );

      await refreshAuthentication();

      setSuccessMessage(
        "Organization settings saved successfully.",
      );

    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to update organization.",
      );
    }
  }


  if (organizationQuery.isPending) {
    return (
      <section
        className="
          flex min-h-72 items-center
          justify-center
        "
      >
        <div
          className="
            flex items-center gap-2
            text-sm text-slate-500
          "
        >
          <RefreshCw
            size={17}
            className="animate-spin"
          />

          Loading organization...
        </div>
      </section>
    );
  }


  if (organizationQuery.isError) {
    return (
      <section
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
          Unable to load organization
        </h1>

        <p
          className="
            mt-2 text-sm text-red-700
          "
        >
          {organizationQuery.error.message}
        </p>

        <button
          type="button"
          onClick={() => {
            void organizationQuery.refetch();
          }}
          className="
            mt-4 inline-flex items-center
            gap-2 rounded-lg bg-slate-900
            px-4 py-2 text-sm
            font-semibold text-white
          "
        >
          <RefreshCw size={16} />

          Try again
        </button>
      </section>
    );
  }


  if (!organization) {
    return (
      <section
        className="
          rounded-2xl border
          border-slate-200 bg-white
          p-6 shadow-sm
        "
      >
        <h1
          className="
            text-lg font-semibold
            text-slate-900
          "
        >
          Organization unavailable
        </h1>

        <p
          className="
            mt-2 text-sm text-slate-600
          "
        >
          No organization information was returned.
        </p>
      </section>
    );
  }


  const normalizedForm = {
    name:
      form.name.trim(),
    email:
      form.email.trim(),
    phone:
      form.phone.trim(),
    address:
      form.address.trim(),
    country:
      form.country.trim(),
    currency:
      form.currency
        .trim()
        .toUpperCase(),
    timezone:
      form.timezone.trim(),
  };

  const hasChanges =
    normalizedForm.name
      !== organization.name
    ||
    normalizedForm.email
      !== organization.email
    ||
    normalizedForm.phone
      !== (organization.phone ?? "")
    ||
    normalizedForm.address
      !== (organization.address ?? "")
    ||
    normalizedForm.country
      !== organization.country
    ||
    normalizedForm.currency
      !== organization.currency
    ||
    normalizedForm.timezone
      !== organization.timezone;


  return (
    <section className="space-y-6">
<ScopeSettings />
      <div
        className="
          flex flex-col gap-4
          sm:flex-row sm:items-center
          sm:justify-between
        "
      >
        <div>
          <div
            className="
              flex items-center gap-2
            "
          >
            <Building2
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Organization
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm text-slate-600
            "
          >
            Manage your company profile and
            organization defaults.
          </p>
        </div>

        <div
          className="
            flex flex-col gap-2
            sm:flex-row
          "
        >
          <button
            type="button"
            disabled={
              !hasChanges
              ||
              updateMutation.isPending
            }
            onClick={
              resetForm
            }
            className="
              inline-flex items-center
              justify-center rounded-lg
              border border-slate-300
              bg-white px-4 py-2
              text-sm font-semibold
              text-slate-700
              hover:bg-slate-50
              disabled:cursor-not-allowed
              disabled:opacity-40
            "
          >
            Reset
          </button>

          <button
            type="button"
            disabled={
              !hasChanges
              ||
              updateMutation.isPending
            }
            onClick={() => {
              void saveOrganization();
            }}
            className="
              inline-flex items-center
              justify-center gap-2
              rounded-lg bg-blue-600
              px-4 py-2 text-sm
              font-semibold text-white
              hover:bg-blue-700
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            {updateMutation.isPending ? (
              <RefreshCw
                size={16}
                className="animate-spin"
              />
            ) : (
              <Save size={16} />
            )}

            {updateMutation.isPending
              ? "Saving..."
              : "Save changes"}
          </button>
        </div>
      </div>

      {successMessage ? (
        <div
          className="
            rounded-xl border
            border-emerald-200 bg-emerald-50
            px-4 py-3 text-sm
            text-emerald-700
          "
        >
          {successMessage}
        </div>
      ) : null}

      {actionError ? (
        <div
          className="
            rounded-xl border
            border-red-200 bg-red-50
            px-4 py-3 text-sm
            text-red-700
          "
        >
          {actionError}
        </div>
      ) : null}

      <div
        className="
          rounded-2xl border
          border-slate-200 bg-white
          shadow-sm
        "
      >
        <div
          className="
            border-b border-slate-200
            px-6 py-5
          "
        >
          <h2
            className="
              text-lg font-semibold
              text-slate-900
            "
          >
            Company information
          </h2>

          <p
            className="
              mt-1 text-sm text-slate-500
            "
          >
            Basic information used across
            your IMS organization.
          </p>
        </div>

        <div
          className="
            grid gap-5 p-6
            md:grid-cols-2
          "
        >
          <label className="space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Organization name
            </span>

            <input
              type="text"
              value={form.name}
              onChange={(event) => {
                updateField(
                  "name",
                  event.target.value,
                );
              }}
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white px-3 text-sm
                text-slate-900 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>

          <label className="space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Email
            </span>

            <input
              type="email"
              value={form.email}
              onChange={(event) => {
                updateField(
                  "email",
                  event.target.value,
                );
              }}
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white px-3 text-sm
                text-slate-900 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>

          <label className="space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Phone
            </span>

            <input
              type="tel"
              value={form.phone}
              onChange={(event) => {
                updateField(
                  "phone",
                  event.target.value,
                );
              }}
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white px-3 text-sm
                text-slate-900 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>

          <label className="space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Country
            </span>

            <input
              type="text"
              value={form.country}
              onChange={(event) => {
                updateField(
                  "country",
                  event.target.value,
                );
              }}
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white px-3 text-sm
                text-slate-900 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>

          <label className="space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Currency
            </span>

            <input
              type="text"
              value={form.currency}
              maxLength={10}
              placeholder="INR"
              onChange={(event) => {
                updateField(
                  "currency",
                  event.target.value
                    .toUpperCase(),
                );
              }}
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white px-3 text-sm
                uppercase text-slate-900
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>

          <label className="space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Timezone
            </span>

            <input
              type="text"
              value={form.timezone}
              placeholder="Asia/Kolkata"
              onChange={(event) => {
                updateField(
                  "timezone",
                  event.target.value,
                );
              }}
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white px-3 text-sm
                text-slate-900 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>

          <label
            className="
              space-y-1.5 md:col-span-2
            "
          >
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Address
            </span>

            <textarea
              value={form.address}
              rows={4}
              onChange={(event) => {
                updateField(
                  "address",
                  event.target.value,
                );
              }}
              className="
                w-full resize-y rounded-lg
                border border-slate-300
                bg-white px-3 py-2
                text-sm text-slate-900
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>
        </div>
      </div>

      <div
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
          Organization status
        </h2>

        <div
          className="
            mt-4 flex flex-wrap
            items-center gap-3
          "
        >
          <span
            className={`
              inline-flex rounded-full
              border px-2.5 py-1
              text-xs font-semibold
              ${
                organization.is_active
                  ? (
                      "border-emerald-200 "
                      +
                      "bg-emerald-50 "
                      +
                      "text-emerald-700"
                    )
                  : (
                      "border-slate-200 "
                      +
                      "bg-slate-100 "
                      +
                      "text-slate-600"
                    )
              }
            `}
          >
            {organization.is_active
              ? "Active"
              : "Inactive"}
          </span>

          <span
            className="
              text-sm text-slate-500
            "
          >
            Organization ID: {organization.id}
          </span>
        </div>

        {organization.updated_at ? (
          <p
            className="
              mt-3 text-xs text-slate-500
            "
          >
            Last updated:{" "}
            {new Date(
              organization.updated_at,
            ).toLocaleString()}
          </p>
        ) : null}
      </div>
    </section>
  );
}