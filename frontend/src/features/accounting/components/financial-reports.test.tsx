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

vi.mock(
  "@/lib/api/client",
  () => {
    class MockAPIRequestError
      extends Error {
      constructor(
        message =
          "API request failed",
      ) {
        super(message);

        this.name =
          "APIRequestError";
      }
    }

    return {
      APIRequestError:
        MockAPIRequestError,
    };
  },
);

import FinancialDashboardPage
  from "@/app/(protected)/financial-dashboard/page";

import CashFlowPage
  from "@/app/(protected)/cash-flow/page";

import FinanceAuditPage
  from "@/app/(protected)/finance-audit/page";


const mockUseFinanceDashboard =
  vi.fn();

const mockUseAccountingDashboard =
  vi.fn();

const mockUseCashFlowReport =
  vi.fn();

const mockUseFinanceAudit =
  vi.fn();

const mockExportMutateAsync =
  vi.fn();

vi.mock(
  "@/features/accounting/hooks",
  () => ({
    useFinanceDashboard:
      (...args: unknown[]) =>
        mockUseFinanceDashboard(
          ...args,
        ),

    useAccountingDashboard:
      (...args: unknown[]) =>
        mockUseAccountingDashboard(
          ...args,
        ),

    useCashFlowReport:
      (...args: unknown[]) =>
        mockUseCashFlowReport(
          ...args,
        ),

    useFinanceAudit:
      (...args: unknown[]) =>
        mockUseFinanceAudit(
          ...args,
        ),
  }),
);

vi.mock(
  "@/features/documents/hooks",
  () => ({
    useExportResource: () => ({
      mutateAsync:
        mockExportMutateAsync,

      isPending: false,
    }),
  }),
);

const financeDashboardData = {
  bank_accounts: {
    account_count: 2,
    total_balance: "15000.00",

    accounts: [
      {
        id: "bank-1",
        current_balance: "10000.00",
      },
      {
        id: "bank-2",
        current_balance: "5000.00",
      },
    ],
  },

  transactions: {
    count: 4,
    total_in: "5000.00",
    total_out: "2000.00",
    net_cash_flow: "3000.00",
  },

  statements: {},

  payment_suggestions: {},

  receivables: {
    total_receivable: "8000.00",
  },

  payables: {
    total_payable: "3500.00",
  },
};


const accountingDashboardData = {
  as_of_date:
    "2026-09-01T00:00:00",

  liquidity: {
    cash_and_bank: "15000.00",
  },

  working_capital: {
    net_working_capital:
      "4500.00",
  },

  profitability: {
    net_profit: "2500.00",
  },

  balance_sheet: {
    total_assets: "25000.00",
  },

  trial_balance: {
    balanced: true,
  },

  accounting_health: {
    healthy: true,
  },
};


const cashFlowData = {
  start_date: "2026-09-01",
  end_date: "2026-09-30",

  bank_account: null,

  opening_balance:
    "10000.00",

  total_in:
    "5000.00",

  total_out:
    "2000.00",

  net_cash_flow:
    "3000.00",

  closing_balance:
    "13000.00",

  transaction_count: 2,

  reconciled_count: 1,

  unreconciled_count: 1,

  daily_summary: [
    {
      date: "2026-09-01",

      money_in:
        "5000.00",

      money_out:
        "2000.00",

      net_cash_flow:
        "3000.00",
    },
  ],

  transactions: [
    {
      transaction_date:
        "2026-09-01T00:00:00",

      amount:
        "5000.00",

      signed_amount:
        "5000.00",
    },
    {
      transaction_date:
        "2026-09-01T00:00:00",

      amount:
        "2000.00",

      signed_amount:
        "-2000.00",
    },
  ],
};


const financeAuditData = {
  healthy: true,

  critical_exception_count:
    0,

  attention_count:
    3,

  statement_exceptions: {
    unmatched_lines: [
      {
        statement_number:
          "BST-001",

        line_number:
          "1",

        description:
          "Customer receipt",

        credit_amount:
          "500.00",
      },
    ],

    invalid_matched_lines: [],

    stale_unresolved_links: [],
  },

  transaction_exceptions: {
    unreconciled_transactions: [
      {
        transaction_number:
          "BTX-001",

        bank_account:
          "Current",

        amount:
          "250.00",
      },
    ],

    duplicate_matches: [],
  },

  suggestion_exceptions: {
    pending: [
      {
        id: "suggestion-1",

        type:
          "CUSTOMER_RECEIPT",

        amount:
          "500.00",

        status:
          "PENDING",
      },
    ],

    confirmed_unexecuted: [],

    rejected: [],

    invalid_execution_state: [],
  },

  invoice_exceptions: [],

  vendor_bill_exceptions: [],
};


function queryResult<T>(
  data: T,
) {
  return {
    data,
    isLoading: false,
    isError: false,
    error: null,
    isFetching: false,
    refetch: vi.fn(),
  };
}


describe(
  "Financial reports pages",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

        mockExportMutateAsync
            .mockResolvedValue(
            undefined,
            );

      mockUseFinanceDashboard
        .mockReturnValue(
          queryResult(
            financeDashboardData,
          ),
        );

      mockUseAccountingDashboard
        .mockReturnValue(
          queryResult(
            accountingDashboardData,
          ),
        );

      mockUseCashFlowReport
        .mockReturnValue(
          queryResult(
            cashFlowData,
          ),
        );

      mockUseFinanceAudit
        .mockReturnValue(
          queryResult(
            financeAuditData,
          ),
        );
    });


    describe(
      "Financial Dashboard",
      () => {
        it(
          "renders financial summary data",
          () => {
            render(
              <FinancialDashboardPage />,
            );

            expect(
              screen.getByRole(
                "heading",
                {
                  name:
                    /financial dashboard/i,
                },
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Bank Balance",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Receivables",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Payables",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Net Cash Flow",
              ),
            ).toBeInTheDocument();
          },
        );


        it(
          "renders accounting dashboard sections",
          () => {
            render(
              <FinancialDashboardPage />,
            );

            expect(
              screen.getByText(
                "Liquidity",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Working Capital",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Profitability",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Balance Sheet",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Trial Balance",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Accounting Health",
              ),
            ).toBeInTheDocument();
          },
        );
      },
    );


    describe(
      "Cash Flow",
      () => {
        it(
          "renders cash flow summary",
          () => {
            render(
              <CashFlowPage />,
            );

            expect(
              screen.getByRole(
                "heading",
                {
                  name:
                    /cash flow/i,
                },
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Opening Balance",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Closing Balance",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Reconciled",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Unreconciled",
              ),
            ).toBeInTheDocument();
          },
        );


        it(
        "renders daily summary and transactions",
        () => {
            render(
            <CashFlowPage />,
            );

            expect(
            screen.getByText(
                "Daily Summary",
            ),
            ).toBeInTheDocument();

            expect(
            screen.getByText(
                "Transactions",
            ),
            ).toBeInTheDocument();

            expect(
            screen.getAllByText(
                "₹5,000.00",
            ).length,
            ).toBeGreaterThan(0);
        },
        );

        it(
          "applies changed date range",
          () => {
            render(
              <CashFlowPage />,
            );

            const inputs =
              screen.getAllByDisplayValue(
                /2026-/,
              );

            expect(
              inputs.length,
            ).toBeGreaterThanOrEqual(2);

            fireEvent.change(
              inputs[0],
              {
                target: {
                  value:
                    "2026-08-01",
                },
              },
            );

            fireEvent.change(
              inputs[1],
              {
                target: {
                  value:
                    "2026-08-31",
                },
              },
            );

            fireEvent.click(
              screen.getByRole(
                "button",
                {
                  name:
                    /apply/i,
                },
              ),
            );

            expect(
              mockUseCashFlowReport,
            ).toHaveBeenCalled();
          },
        );
      },
    );


    describe(
      "Finance Audit",
      () => {
        it(
          "renders audit health summary",
          () => {
            render(
              <FinanceAuditPage />,
            );

            expect(
              screen.getByRole(
                "heading",
                {
                  name:
                    /finance audit/i,
                },
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Overall Status",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Healthy",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Critical Issues",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Needs Attention",
              ),
            ).toBeInTheDocument();
          },
        );


        it(
          "renders statement exceptions",
          () => {
            render(
              <FinanceAuditPage />,
            );

            expect(
              screen.getByText(
                "Unmatched Statement Lines",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "BST-001",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Customer receipt",
              ),
            ).toBeInTheDocument();
          },
        );


        it(
          "renders transaction exceptions",
          () => {
            render(
              <FinanceAuditPage />,
            );

            expect(
              screen.getByText(
                "Unreconciled Transactions",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "BTX-001",
              ),
            ).toBeInTheDocument();
          },
        );


        it(
          "renders payment suggestion exceptions",
          () => {
            render(
              <FinanceAuditPage />,
            );

            expect(
              screen.getByText(
                "Pending Payment Suggestions",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "CUSTOMER_RECEIPT",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "PENDING",
              ),
            ).toBeInTheDocument();
          },
        );


        it(
          "renders empty exception categories",
          () => {
            render(
              <FinanceAuditPage />,
            );

            expect(
              screen.getByText(
                "Invalid Statement Matches",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Duplicate Matches",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getByText(
                "Customer Invoice Exceptions",
              ),
            ).toBeInTheDocument();

            expect(
              screen.getAllByText(
                "No exceptions found",
              ).length,
            ).toBeGreaterThan(0);
          },
        );
      },
    );
  },
);