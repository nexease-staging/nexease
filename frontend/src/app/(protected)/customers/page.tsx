"use client";
import {confirmAction} from "@/components/nex-feedback";
import PageHeader from "@/components/ui/page-header";
import IconButton from "@/components/ui/icon-button";
import FilterSheet from "@/components/ui/filter-sheet";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  Pencil,
  Plus,
  Power,
  PowerOff,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Users,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import CustomerDialog from "@/features/customers/components/customer-dialog";

import {
  useActivateCustomer,
  useCustomerList,
  useDeactivateCustomer,
} from "@/features/customers/hooks";

import type {
  CustomerSummary,
} from "@/features/customers/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

export default function CustomersPage() {
  const {
    authentication,
  } = useAuth();

  const [filtersOpen,setFiltersOpen]=useState(false);
  const [
    search,
    setSearch,
  ] = useState("");

  const [
    activeFilter,
    setActiveFilter,
  ] = useState<
    "all" | "active" | "inactive"
  >("all");

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    dialogOpen,
    setDialogOpen,
  ] = useState(false);

  const [
    editingCustomerId,
    setEditingCustomerId,
  ] = useState<string | null>(
    null,
  );

  const [
    actionError,
    setActionError,
  ] = useState<string | null>(
    null,
  );

  const activateMutation =
    useActivateCustomer();

  const deactivateMutation =
    useDeactivateCustomer();

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead = hasPermission(
    permissions,
    "customers.read",
  );

  const canCreate = hasPermission(
    permissions,
    "customers.create",
  );

  const canUpdate = hasPermission(
    permissions,
    "customers.update",
  );

  const listParameters = useMemo(
    () => ({
      page,
      page_size: 25,
      search:
        search.trim()
        ||
        undefined,
      is_active:
        activeFilter === "all"
          ? undefined
          : activeFilter === "active",
      sort: "name",
    }),
    [
      activeFilter,
      page,
      search,
    ],
  );

  const customerQuery =
    useCustomerList(
      listParameters,
    );

  if (!authentication) {
    return null;
  }

  if (!canRead) {
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
          Customer access restricted
        </h1>

        <p className="mt-2 text-sm text-amber-800">
          Your role does not include the
          customers.read permission.
        </p>
      </section>
    );
  }

  const customers =
    customerQuery.data
      ?.customers
    ??
    [];

  const pagination =
    customerQuery.data
      ?.pagination;

  const actionPending =
    activateMutation.isPending
    ||
    deactivateMutation.isPending;

  function openCreateDialog(): void {
    setEditingCustomerId(
      null,
    );

    setDialogOpen(
      true,
    );
  }

  function openEditDialog(
    customerId: string,
  ): void {
    setEditingCustomerId(
      customerId,
    );

    setDialogOpen(
      true,
    );
  }

  async function activate(
    customer: CustomerSummary,
  ): Promise<void> {
    if (
      !await confirmAction(
        `Activate ${customer.name}?`,
      )
    ) {
      return;
    }

    setActionError(
      null,
    );

    try {
      await activateMutation.mutateAsync(
        customer.id,
      );
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to activate customer.",
      );
    }
  }

  async function deactivate(
    customer: CustomerSummary,
  ): Promise<void> {
    if (
      !await confirmAction(
        (
          `Deactivate ${customer.name}?`
          +
          "\n\nThe customer remains "
          +
          "available in historical records."
        ),
      )
    ) {
      return;
    }

    setActionError(
      null,
    );

    try {
      await deactivateMutation.mutateAsync(
        customer.id,
      );
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to deactivate customer.",
      );
    }
  }

  return (
    <section className="space-y-6">
      <PageHeader title="Customers" actions={<>
        <IconButton icon={SlidersHorizontal} label="Filter customers" onClick={()=>setFiltersOpen(true)}/>
        <IconButton icon={RefreshCw} label="Refresh customers" disabled={customerQuery.isFetching} onClick={()=>void customerQuery.refetch()}/>
        {canCreate && <IconButton icon={Plus} label="New customer" className="nx-primary-icon" onClick={openCreateDialog}/>}
      </>}/>
      <label className="nx-compact-search"><Search size={18} aria-hidden="true"/>
        <input type="search" aria-label="Search customers" placeholder="Search name or GSTIN" value={search} onChange={event=>{setSearch(event.target.value);setPage(1)}}/>
      </label>
      <FilterSheet open={filtersOpen} onClose={()=>setFiltersOpen(false)}>
        <label className="block space-y-2"><span>Status</span>
          <SearchSelect value={activeFilter} onChange={event=>{setActiveFilter(event.target.value as "all"|"active"|"inactive");setPage(1)}} className="nx-input w-full">
            <option value="all">All customers</option><option value="active">Active customers</option><option value="inactive">Inactive customers</option>
          </SearchSelect>
        </label>
      </FilterSheet>

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
          overflow-hidden rounded-2xl
          border border-slate-200
          bg-white shadow-sm
        "
      >
        {customerQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading customers…
          </div>
        ) : customerQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6
            "
          >
            <p className="text-sm text-red-700">
              {customerQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void customerQuery.refetch();
              }}
              className="
                rounded-lg bg-slate-900
                px-4 py-2 text-sm
                font-semibold text-white
              "
            >
              Try again
            </button>
          </div>
        ) : customers.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <Users
              size={36}
              className="text-slate-300"
            />

            <h2 className="mt-3 font-semibold text-slate-900">
              No customers found
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Change the filters or create
              your first customer.
            </p>

            {canCreate ? (
              <button title="Create customer"
                type="button"
                onClick={
                  openCreateDialog
                }
                className="
                  mt-4 inline-flex
                  items-center gap-2
                  rounded-lg bg-blue-600
                  px-4 py-2 text-sm
                  font-semibold text-white
                "
              >
                <Plus size={16} /><span className="sr-only">Create customer</span></button>
            ) : null}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table role="table"
              className="nx-mobile-records
                min-w-full divide-y
                divide-slate-200
              "
            >
              <thead className="bg-slate-50">
                <tr>
                  {[
                    "Code",
                    "Customer",
                    "Contact",
                    "GSTIN",
                    "Location",
                    "Status",
                    "Actions",
                  ].map(
                    (heading) => (
                      <th
                        key={heading}
                        className="
                          whitespace-nowrap
                          px-4 py-3 text-left
                          text-xs font-semibold
                          uppercase tracking-wide
                          text-slate-500
                        "
                      >
                        {heading}
                      </th>
                    ),
                  )}
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {customers.map(
                  (customer) => (
                    <tr
                      key={customer.id}
                      className="hover:bg-slate-50"
                    >
                      <td data-label="Code"
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-bold text-slate-900
                        "
                      >
                        {customer.code}
                      </td>

                      <td data-label="Customer"
                        className="
                          px-4 py-4 text-sm
                          font-semibold
                          text-slate-900
                        "
                      >
                        {customer.name}
                      </td>

                      <td data-label="Contact"
                        className="
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        <p>
                          {customer.email ?? "—"}
                        </p>

                        <p className="mt-0.5 text-xs">
                          {customer.phone ?? "—"}
                        </p>
                      </td>

                      <td data-label="GSTIN"
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {customer.gstin ?? "—"}
                      </td>

                      <td data-label="Location"
                        className="
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {
                          [
                            customer.city,
                            customer.state,
                          ]
                            .filter(Boolean)
                            .join(", ")
                          ||
                          customer.country
                          ||
                          "—"
                        }
                      </td>

                      <td data-label="Status"
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <span
                          className={`
                            inline-flex rounded-full
                            border px-2.5 py-1
                            text-xs font-semibold
                            ${
                              customer.is_active
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
                          {
                            customer.is_active
                              ? "Active"
                              : "Inactive"
                          }
                        </span>
                      </td>

                      <td data-label="Actions"
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        {canUpdate ? (
                          <div className="flex gap-2">
                            {customer.is_active ? (
                              <>
                                <button
                                  type="button"
                                  title="Edit customer"
                                  disabled={
                                    actionPending
                                  }
                                  onClick={() => {
                                    openEditDialog(
                                      customer.id,
                                    );
                                  }}
                                  className="
                                    rounded-lg border
                                    border-slate-300
                                    bg-white p-2
                                    text-slate-600
                                    hover:text-blue-700
                                    disabled:opacity-40
                                  "
                                >
                                  <Pencil size={16} />
                                </button>

                                <button
                                  type="button"
                                  title="Deactivate customer"
                                  disabled={
                                    actionPending
                                  }
                                  onClick={() => {
                                    void deactivate(
                                      customer,
                                    );
                                  }}
                                  className="
                                    rounded-lg border
                                    border-red-200
                                    bg-red-50 p-2
                                    text-red-700
                                    disabled:opacity-40
                                  "
                                >
                                  <PowerOff size={16} />
                                </button>
                              </>
                            ) : (
                              <button
                                type="button"
                                title="Activate customer"
                                disabled={
                                  actionPending
                                }
                                onClick={() => {
                                  void activate(
                                    customer,
                                  );
                                }}
                                className="
                                  rounded-lg border
                                  border-emerald-200
                                  bg-emerald-50 p-2
                                  text-emerald-700
                                  disabled:opacity-40
                                "
                              >
                                <Power size={16} />
                              </button>
                            )}
                          </div>
                        ) : null}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}

        {pagination ? (
          <div
            className="
              flex flex-col gap-3
              border-t border-slate-200
              px-4 py-3
              sm:flex-row sm:items-center
              sm:justify-between
            "
          >
            <p className="text-sm text-slate-600">
              Page {pagination.page} of{" "}
              {pagination.total_pages || 1}
              {" · "}
              {pagination.total_items} customers
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !pagination.has_previous
                  ||
                  customerQuery.isFetching
                }
                onClick={() => {
                  setPage(
                    (current) =>
                      Math.max(
                        1,
                        current - 1,
                      ),
                  );
                }}
                className="
                  rounded-lg border
                  border-slate-300 bg-white
                  px-3 py-1.5 text-sm
                  font-semibold text-slate-700
                  disabled:opacity-40
                "
              >
                Previous
              </button>

              <button
                type="button"
                disabled={
                  !pagination.has_next
                  ||
                  customerQuery.isFetching
                }
                onClick={() => {
                  setPage(
                    (current) =>
                      current + 1,
                  );
                }}
                className="
                  rounded-lg border
                  border-slate-300 bg-white
                  px-3 py-1.5 text-sm
                  font-semibold text-slate-700
                  disabled:opacity-40
                "
              >
                Next
              </button>
            </div>
          </div>
        ) : null}
      </div>

      <CustomerDialog
        open={dialogOpen}
        customerId={
          editingCustomerId
        }
        onClose={() => {
          setDialogOpen(
            false,
          );

          setEditingCustomerId(
            null,
          );
        }}
      />
    </section>
  );
}