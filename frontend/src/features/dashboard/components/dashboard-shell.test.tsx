import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import DashboardShell from "@/features/dashboard/components/dashboard-shell";

import {
  useMainDashboard,
} from "@/features/dashboard/hooks";

import type {
  MainDashboard,
} from "@/features/dashboard/types";


vi.mock(
  "@/features/dashboard/hooks",
  () => ({
    useMainDashboard:
      vi.fn(),
  }),
);


vi.mock(
  "@/features/dashboard/components/dashboard-loading-skeleton",
  () => ({
    default: () => (
      <div>
        Dashboard loading skeleton
      </div>
    ),
  }),
);


vi.mock(
  "@/features/dashboard/components/dashboard-kpi-grid",
  () => ({
    default: () => (
      <div>
        Dashboard KPI grid
      </div>
    ),
  }),
);


vi.mock(
  "@/features/dashboard/components/dashboard-trend-charts",
  () => ({
    default: () => (
      <div>
        Dashboard trend charts
      </div>
    ),
  }),
);


vi.mock(
  "@/features/dashboard/components/dashboard-status-charts",
  () => ({
    default: () => (
      <div>
        Dashboard status charts
      </div>
    ),
  }),
);


vi.mock(
  "@/features/dashboard/components/dashboard-top-entities",
  () => ({
    default: () => (
      <div>
        Dashboard top entities
      </div>
    ),
  }),
);


vi.mock(
  "@/features/dashboard/components/dashboard-alerts-activity",
  () => ({
    default: () => (
      <div>
        Dashboard alerts activity
      </div>
    ),
  }),
);


const dashboard:
  MainDashboard = {
    period: {
      start_date:
        "2026-01-01",

      end_date:
        "2026-09-03",
    },

    kpis: {
      total_sales:
        "254944.00",

      total_purchases:
        "591250.00",

      receivables:
        "16000.00",

      payables:
        "0.00",

      bank_balance:
        "21844.00",

      inventory_value:
        "100000.00",

      out_of_stock_items:
        1,
    },

    sales_trend: [],

    purchase_trend: [],

    cash_flow: [],

    receivable_aging: {
      current:
        "16000.00",

      "1_30":
        "0.00",

      "31_60":
        "0.00",

      "61_90":
        "0.00",

      "90_plus":
        "0.00",
    },

    invoice_status: {
      issued:
        2,

      partially_paid:
        1,

      paid:
        4,

      overdue:
        0,
    },

    bill_status: {
      posted:
        0,

      partially_paid:
        0,

      paid:
        3,

      overdue:
        0,
    },

    inventory_status: {
      in_stock:
        10,

      out_of_stock:
        1,
    },

    top_customers: [],

    top_suppliers: [],

    alerts: {
      overdue_invoices:
        0,

      overdue_bills:
        0,

      out_of_stock_items:
        1,
    },

    recent_activity: [],
  };


const useMainDashboardMock =
  vi.mocked(
    useMainDashboard,
  );


function createQueryResult(
  overrides:
    Record<
      string,
      unknown
    > = {},
) {
  return {
    data:
      undefined,

    isLoading:
      false,

    isFetching:
      false,

    isError:
      false,

    error:
      null,

    refetch:
      vi.fn(),

    ...overrides,
  } as unknown as ReturnType<
    typeof useMainDashboard
  >;
}


describe(
  "DashboardShell",
  () => {
    beforeEach(
      () => {
        vi.clearAllMocks();
      },
    );


    it(
      "shows dashboard loading skeleton during initial load",
      () => {
        useMainDashboardMock
          .mockReturnValue(
            createQueryResult({
              isLoading:
                true,
            }),
          );

        render(
          <DashboardShell />,
        );

        expect(
          screen.getByText(
            "Dashboard loading skeleton",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "shows the dashboard API error state",
      () => {
        useMainDashboardMock
          .mockReturnValue(
            createQueryResult({
              isError:
                true,

              error:
                new Error(
                  "Dashboard request failed",
                ),
            }),
          );

        render(
          <DashboardShell />,
        );

        expect(
          screen.getByText(
            "Dashboard could not be loaded",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Dashboard request failed",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "renders dashboard sections when data is loaded",
      () => {
        useMainDashboardMock
          .mockReturnValue(
            createQueryResult({
              data:
                dashboard,
            }),
          );

        render(
          <DashboardShell />,
        );

        expect(
          screen.getByText(
            "API connected",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Dashboard KPI grid",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Dashboard trend charts",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Dashboard status charts",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Dashboard top entities",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Dashboard alerts activity",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "passes selected dates to the dashboard hook",
      () => {
        useMainDashboardMock
          .mockReturnValue(
            createQueryResult({
              data:
                dashboard,
            }),
          );

        render(
          <DashboardShell />,
        );



        const startDateInput =
          screen.getByLabelText(
            "Start date",
          );

        const endDateInput =
          screen.getByLabelText(
            "End date",
          );

        fireEvent.change(
          startDateInput,
          {
            target: {
              value:
                "2026-08-01",
            },
          },
        );

        fireEvent.change(
          endDateInput,
          {
            target: {
              value:
                "2026-08-31",
            },
          },
        );

        expect(
          useMainDashboardMock,
        ).toHaveBeenLastCalledWith(
          {
            start_date:
              "2026-08-01",

            end_date:
              "2026-08-31",
          },
        );
      },
    );


    it(
      "refetches dashboard when Refresh is clicked",
      async () => {
        const refetch =
          vi.fn();

        useMainDashboardMock
          .mockReturnValue(
            createQueryResult({
              data:
                dashboard,

              refetch,
            }),
          );

        render(
          <DashboardShell />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Refresh",
            },
          ),
        );

        expect(
          refetch,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );


    it(
      "disables Refresh while dashboard is fetching",
      () => {
        useMainDashboardMock
          .mockReturnValue(
            createQueryResult({
              data:
                dashboard,

              isFetching:
                true,
            }),
          );

        render(
          <DashboardShell />,
        );

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Refresh",
            },
          ),
        ).toBeDisabled();
      },
    );
  },
);