import {
  Building2,
  Users,
} from "lucide-react";

import type {
  DashboardTopCustomer,
  DashboardTopSupplier,
} from "@/features/dashboard/types";


interface DashboardTopEntitiesProps {
  customers:
    DashboardTopCustomer[];

  suppliers:
    DashboardTopSupplier[];
}


function formatCurrency(
  value: string,
): string {
  const amount =
    Number(
      value,
    );

  if (
    !Number.isFinite(
      amount,
    )
  ) {
    return "₹0.00";
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


interface EntityTableProps {
  title: string;
  description: string;
  entityLabel: string;
  icon:
    typeof Users;

  rows: Array<{
    id: string;
    name: string;
    amount: string;
  }>;
}


function EntityTable({
  title,
  description,
  entityLabel,
  icon: Icon,
  rows,
}: EntityTableProps) {
  return (
    <article
        className="
        flex
        h-[420px]
        flex-col
        overflow-hidden
        rounded-2xl
        border
        border-slate-200
        bg-white
        shadow-sm
        "
    >
      <div
        className="
          flex
          items-center
          gap-3
          border-b
          border-slate-100
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

        <div>
          <h2
            className="
              text-base
              font-semibold
              text-slate-950
            "
          >
            {title}
          </h2>

          <p
            className="
              mt-0.5
              text-sm
              text-slate-500
            "
          >
            {description}
          </p>
        </div>
      </div>

      {
        rows.length > 0
          ? (
            <div
              className="
                min-h-0
                flex-1
                overflow-x-auto
              "
            >
              <table
                className="
                  w-full
                  min-w-[480px]
                  text-left
                "
              >
                <thead
                  className="
                    bg-slate-50
                  "
                >
                  <tr>
                    <th
                      className="
                        w-16
                        px-5
                        py-3
                        text-xs
                        font-semibold
                        uppercase
                        tracking-wide
                        text-slate-500
                      "
                    >
                      Rank
                    </th>

                    <th
                      className="
                        px-5
                        py-3
                        text-xs
                        font-semibold
                        uppercase
                        tracking-wide
                        text-slate-500
                      "
                    >
                      {entityLabel}
                    </th>

                    <th
                      className="
                        px-5
                        py-3
                        text-right
                        text-xs
                        font-semibold
                        uppercase
                        tracking-wide
                        text-slate-500
                      "
                    >
                      Value
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {
                    rows.map(
                      (
                        row,
                        index,
                      ) => (
                        <tr
                          key={
                            row.id
                          }
                          className="
                            border-t
                            border-slate-100
                          "
                        >
                          <td
                            className="
                              px-5
                              py-4
                            "
                          >
                            <span
                              className="
                                inline-flex
                                h-7
                                w-7
                                items-center
                                justify-center
                                rounded-full
                                bg-slate-100
                                text-xs
                                font-bold
                                text-slate-700
                              "
                            >
                              {
                                index
                                + 1
                              }
                            </span>
                          </td>

                          <td
                            className="
                              px-5
                              py-4
                            "
                          >
                            <p
                              className="
                                max-w-[320px]
                                truncate
                                text-sm
                                font-semibold
                                text-slate-900
                              "
                              title={
                                row.name
                              }
                            >
                              {
                                row.name
                              }
                            </p>
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-5
                              py-4
                              text-right
                              text-sm
                              font-semibold
                              text-slate-900
                            "
                          >
                            {
                              formatCurrency(
                                row.amount,
                              )
                            }
                          </td>
                        </tr>
                      ),
                    )
                  }
                </tbody>
              </table>
            </div>
          )
          : (
            <div
              className="
                flex
                min-h-48
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
                No data available
              </p>
            </div>
          )
      }
    </article>
  );
}


export default function DashboardTopEntities({
  customers,
  suppliers,
}: DashboardTopEntitiesProps) {
  const customerRows =
    customers.map(
      (
        customer,
      ) => ({
        id:
          customer
            .customer_id,

        name:
          customer
            .customer_name,

        amount:
          customer
            .amount,
      }),
    );

  const supplierRows =
    suppliers.map(
      (
        supplier,
      ) => ({
        id:
          supplier
            .supplier_id,

        name:
          supplier
            .supplier_name,

        amount:
          supplier
            .amount,
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
      <EntityTable
        title="Top Customers"
        description="Highest invoice value in the selected period"
        entityLabel="Customer"
        icon={
          Users
        }
        rows={
          customerRows
        }
      />

      <EntityTable
        title="Top Suppliers"
        description="Highest vendor bill value in the selected period"
        entityLabel="Supplier"
        icon={
          Building2
        }
        rows={
          supplierRows
        }
      />
    </section>
  );
}