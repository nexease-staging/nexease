import type {
  ReactNode,
} from "react";

import {
  render,
  screen,
} from "@testing-library/react";

import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import DashboardAlertsActivity from "@/features/dashboard/components/dashboard-alerts-activity";
import DashboardKPIGrid from "@/features/dashboard/components/dashboard-kpi-grid";
import DashboardStatusCharts from "@/features/dashboard/components/dashboard-status-charts";
import DashboardTopEntities from "@/features/dashboard/components/dashboard-top-entities";

import type {
  DashboardAlerts,
  DashboardBillStatus,
  DashboardInventoryStatus,
  DashboardInvoiceStatus,
  DashboardKPIs,
  DashboardReceivableAging,
  DashboardRecentActivity,
  DashboardTopCustomer,
  DashboardTopSupplier,
} from "@/features/dashboard/types";


vi.mock(
  "recharts",
  () => ({
    ResponsiveContainer: ({
      children,
    }: {
      children:ReactNode;
    }) => (
      <div>
        {children}
      </div>
    ),

    PieChart: ({
      children,
    }: {
      children:ReactNode;
    }) => (
      <div>
        {children}
      </div>
    ),

    Pie: ({
      children,
    }: {
      children?:
        React.ReactNode;
    }) => (
      <div>
        {children}
      </div>
    ),

    Cell: () => (
      <span />
    ),

    Tooltip: () => (
      <span />
    ),
  }),
);


const kpis:
  DashboardKPIs = {
    total_sales:
      "254944.00",

    total_purchases:
      "591250.00",

    receivables:
      "16000.00",

    payables:
      "5000.00",

    bank_balance:
      "21844.00",

    inventory_value:
      "100000.00",

    out_of_stock_items:
      3,
  };


const customers:
  DashboardTopCustomer[] = [
    {
      customer_id:
        "customer-1",

      customer_name:
        "TechNova Solutions Pvt Ltd",

      amount:
        "237800.00",
    },
  ];


const suppliers:
  DashboardTopSupplier[] = [
    {
      supplier_id:
        "supplier-1",

      supplier_name:
        "ABC Components India Pvt Ltd",

      amount:
        "591250.00",
    },
  ];


const alerts:
  DashboardAlerts = {
    overdue_invoices:
      2,

    overdue_bills:
      1,

    out_of_stock_items:
      3,
  };


const recentActivity:
  DashboardRecentActivity[] = [
    {
      activity_type:
        "INVOICE",

      reference_id:
        "invoice-1",

      reference_number:
        "INV-001",

      description:
        "Invoice created for TechNova",

      activity_date:
        "2026-09-03T10:30:00",

      amount:
        "12500.00",
    },

    {
      activity_type:
        "STOCK_MOVEMENT",

      reference_id:
        "movement-1",

      reference_number:
        "MOV-001",

      description:
        "Stock received",

      activity_date:
        "2026-09-03T09:00:00",

      amount:
        null,

      quantity:
        "5",
    },
  ];


const receivableAging:
  DashboardReceivableAging = {
    current:
      "16000.00",

    "1_30":
      "5000.00",

    "31_60":
      "0.00",

    "61_90":
      "0.00",

    "90_plus":
      "0.00",
  };


const invoiceStatus:
  DashboardInvoiceStatus = {
    issued:
      2,

    partially_paid:
      1,

    paid:
      4,

    overdue:
      1,
  };


const billStatus:
  DashboardBillStatus = {
    posted:
      1,

    partially_paid:
      1,

    paid:
      3,

    overdue:
      1,
  };


const inventoryStatus:
  DashboardInventoryStatus = {
    in_stock:
      10,

    out_of_stock:
      3,
  };


describe(
  "DashboardKPIGrid",
  () => {
    it(
      "renders KPI labels",
      () => {
        render(
          <DashboardKPIGrid
            kpis={
              kpis
            }
          />,
        );

        expect(
          screen.getByText(
            "Total Sales",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Total Purchases",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Receivables",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Out of Stock Items",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "formats KPI monetary values in INR",
      () => {
        render(
          <DashboardKPIGrid
            kpis={
              kpis
            }
          />,
        );

        expect(
          screen.getByText(
            "₹2,54,944.00",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "₹5,91,250.00",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "₹16,000.00",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "renders out of stock count",
      () => {
        render(
          <DashboardKPIGrid
            kpis={
              kpis
            }
          />,
        );

        expect(
          screen.getByText(
            "3",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);


describe(
  "DashboardTopEntities",
  () => {
    it(
      "renders top customer and supplier data",
      () => {
        render(
          <DashboardTopEntities
            customers={
              customers
            }
            suppliers={
              suppliers
            }
          />,
        );

        expect(
          screen.getByText(
            "TechNova Solutions Pvt Ltd",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "ABC Components India Pvt Ltd",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "₹2,37,800.00",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "₹5,91,250.00",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "renders empty states when no entities exist",
      () => {
        render(
          <DashboardTopEntities
            customers={[]}
            suppliers={[]}
          />,
        );

        expect(
          screen.getAllByText(
            "No data available",
          ),
        ).toHaveLength(
          2,
        );
      },
    );
  },
);


describe(
  "DashboardAlertsActivity",
  () => {
    it(
      "renders alert counts",
      () => {
        render(
          <DashboardAlertsActivity
            alerts={
              alerts
            }
            recentActivity={[]}
          />,
        );

        expect(
          screen.getByText(
            "Overdue Invoices",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Overdue Bills",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Out of Stock Items",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "2",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "1",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "3",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "renders recent activity amount and quantity",
      () => {
        render(
          <DashboardAlertsActivity
            alerts={
              alerts
            }
            recentActivity={
              recentActivity
            }
          />,
        );

        expect(
          screen.getByText(
            "Invoice created for TechNova",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "INV-001",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "₹12,500.00",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Stock received",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Qty 5",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "renders empty recent activity state",
      () => {
        render(
          <DashboardAlertsActivity
            alerts={
              alerts
            }
            recentActivity={[]}
          />,
        );

        expect(
          screen.getByText(
            "No recent activity",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);


describe(
  "DashboardStatusCharts",
  () => {
    it(
      "renders status chart headings",
      () => {
        render(
          <DashboardStatusCharts
            receivableAging={
              receivableAging
            }
            invoiceStatus={
              invoiceStatus
            }
            billStatus={
              billStatus
            }
            inventoryStatus={
              inventoryStatus
            }
          />,
        );

        expect(
          screen.getByText(
            "Receivables Aging",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Invoice Status",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Bill Status",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Inventory Status",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "renders aging and status labels",
      () => {
        render(
          <DashboardStatusCharts
            receivableAging={
              receivableAging
            }
            invoiceStatus={
              invoiceStatus
            }
            billStatus={
              billStatus
            }
            inventoryStatus={
              inventoryStatus
            }
          />,
        );

        expect(
          screen.getByText(
            "Current",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "90+ Days",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "Paid",
          ).length,
        ).toBeGreaterThan(
          0,
        );

        expect(
          screen.getByText(
            "In Stock",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Out of Stock",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "renders no data states when all chart values are zero",
      () => {
        render(
          <DashboardStatusCharts
            receivableAging={{
              current:
                "0.00",

              "1_30":
                "0.00",

              "31_60":
                "0.00",

              "61_90":
                "0.00",

              "90_plus":
                "0.00",
            }}
            invoiceStatus={{
              issued:
                0,

              partially_paid:
                0,

              paid:
                0,

              overdue:
                0,
            }}
            billStatus={{
              posted:
                0,

              partially_paid:
                0,

              paid:
                0,

              overdue:
                0,
            }}
            inventoryStatus={{
              in_stock:
                0,

              out_of_stock:
                0,
            }}
          />,
        );

        expect(
          screen.getAllByText(
            "No data available",
          ),
        ).toHaveLength(
          4,
        );
      },
    );
  },
);