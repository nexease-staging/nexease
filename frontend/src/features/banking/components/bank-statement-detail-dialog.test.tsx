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

import BankStatementDetailDialog
  from "@/features/banking/components/bank-statement-detail-dialog";

const mockUseBankStatement = vi.fn();
const mockUseBankPaymentSuggestionList = vi.fn();
const mockUseBankTransactionList = vi.fn();

const mockAutoMatchMutate = vi.fn();
const mockMatchMutate = vi.fn();
const mockIgnoreMutate = vi.fn();
const mockCancelMutate = vi.fn();

vi.mock(
  "@/features/banking/hooks",
  () => ({
    useBankStatement: (
      ...args: unknown[]
    ) =>
      mockUseBankStatement(...args),

    useBankPaymentSuggestionList: (
      ...args: unknown[]
    ) =>
      mockUseBankPaymentSuggestionList(
        ...args,
      ),

    useBankTransactionList: (
      ...args: unknown[]
    ) =>
      mockUseBankTransactionList(
        ...args,
      ),

    useAutoMatchStatementLine: () => ({
      mutate: mockAutoMatchMutate,
      isPending: false,
      error: null,
    }),

    useMatchStatementLine: () => ({
      mutate: mockMatchMutate,
      isPending: false,
      error: null,
    }),

    useIgnoreStatementLine: () => ({
      mutate: mockIgnoreMutate,
      isPending: false,
      error: null,
    }),

    useCancelBankStatement: () => ({
      mutate: mockCancelMutate,
      isPending: false,
      error: null,
    }),
  }),
);

vi.mock(
  "@/features/banking/components/bank-payment-suggestion-actions",
  () => ({
    default: () => (
      <div data-testid="payment-suggestion-actions">
        Payment suggestion actions
      </div>
    ),
  }),
);
const unmatchedLine = {
  line_number: 1,
  transaction_date: "2026-09-01",
  description: "Customer receipt",
  external_reference: "INV-TEST-001",
  debit_amount: "0.00",
  credit_amount: "500.00",
  match_status: "UNMATCHED",
  matched_transaction: null,
};

const availableTransaction = {
  id: "transaction-1",
  transaction_number: "BTX-TEST-001",
  transaction_date: "2026-09-01",
  transaction_type: "CUSTOMER_RECEIPT",
  amount: "500.00",
};
const statement = {
  id: "statement-1",
  statement_number: "BST-TEST-001",

  bank_account: {
    id: "account-1",
    account_name: "Current",
    currency: "INR",
  },

  statement_start_date:
    "2026-09-01",
  statement_end_date:
    "2026-09-01",

  opening_balance:
    "10000.00",
  closing_balance:
    "10500.00",

  status:
    "PARTIALLY_RECONCILED",

  source_type: "CSV",
  source_filename:
    "test_statement.csv",

  line_count: 5,
  matched_count: 1,
  unmatched_count: 3,
  ignored_count: 1,

  lines: [],
};

function renderDialog() {
  return render(
    <BankStatementDetailDialog
      open
      statementId="statement-1"
      canReconcile
      canCancel
      onClose={vi.fn()}
    />,
  );
}

describe(
  "BankStatementDetailDialog",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mockUseBankStatement
        .mockReturnValue({
          data: statement,
          isLoading: false,
          isError: false,
          error: null,
        });

      mockUseBankPaymentSuggestionList
        .mockReturnValue({
          data: {
            bank_payment_suggestions: [],
          },
          isLoading: false,
          isError: false,
          error: null,
        });

      mockUseBankTransactionList
        .mockReturnValue({
          data: {
            bank_transactions: [],
          },
          isLoading: false,
          isError: false,
          error: null,
        });
    });

    it(
    "shows transaction loading state",
    () => {
        mockUseBankStatement
        .mockReturnValue({
            data: {
            ...statement,
            lines: [
                unmatchedLine,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        mockUseBankTransactionList
        .mockReturnValue({
            data: undefined,
            isLoading: true,
            isError: false,
            error: null,
        });

        renderDialog();

        const select =
        screen.getByRole(
            "combobox",
        );

        expect(
        select,
        ).toBeDisabled();

        expect(
        screen.getByText(
            "Loading transactions...",
        ),
        ).toBeInTheDocument();
    },
    );

    it(
    "shows empty transaction state",
    () => {
        mockUseBankStatement
        .mockReturnValue({
            data: {
            ...statement,
            lines: [
                unmatchedLine,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        mockUseBankTransactionList
        .mockReturnValue({
            data: {
            bank_transactions: [],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        renderDialog();

        const select =
        screen.getByRole(
            "combobox",
        );

        expect(
        select,
        ).toBeDisabled();

        expect(
        screen.getByText(
            "No unreconciled transactions",
        ),
        ).toBeInTheDocument();
    },
    );

    it(
    "shows transaction query error",
    () => {
        mockUseBankStatement
        .mockReturnValue({
            data: {
            ...statement,
            lines: [
                unmatchedLine,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        mockUseBankTransactionList
        .mockReturnValue({
            data: undefined,
            isLoading: false,
            isError: true,
            error: new Error(
            "Unable to load transactions",
            ),
        });

        renderDialog();

        const select =
        screen.getByRole(
            "combobox",
        );

        expect(
        select,
        ).toBeDisabled();

        expect(
        screen.getByText(
            "Unable to load transactions",
            {
            selector: "option",
            },
        ),
        ).toBeInTheDocument();

        expect(
        screen.getByRole(
            "alert",
        ),
        ).toHaveTextContent(
        "Unable to load transactions",
        );
    },
    );

    it(
    "enables transaction selection when transactions exist",
    () => {
        mockUseBankStatement
        .mockReturnValue({
            data: {
            ...statement,
            lines: [
                unmatchedLine,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        mockUseBankTransactionList
        .mockReturnValue({
            data: {
            bank_transactions: [
                availableTransaction,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        renderDialog();

        const select =
        screen.getByRole(
            "combobox",
        );

        expect(
        select,
        ).toBeEnabled();

        expect(
        screen.getByText(
            "Select transaction",
        ),
        ).toBeInTheDocument();
    },
    );

    it(
      "renders statement summary",
      () => {
        renderDialog();

        expect(
          screen.getByText(
            "BST-TEST-001",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "PARTIALLY_RECONCILED",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Opening balance",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Closing balance",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Matched lines",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Unmatched lines",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Ignored lines",
          ),
        ).toBeInTheDocument();
      },
    );
    it(
    "calls auto-match mutation for an unmatched line",
    () => {
        mockUseBankStatement
        .mockReturnValue({
            data: {
            ...statement,
            lines: [
                unmatchedLine,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        renderDialog();

        fireEvent.click(
        screen.getByRole(
            "button",
            {
            name: /auto-match/i,
            },
        ),
        );

        expect(
        mockAutoMatchMutate,
        ).toHaveBeenCalledWith({
        statementId: "statement-1",
        lineNumber: 1,
        dateToleranceDays: 2,
        });
    },
    );

    it(
    "calls ignore mutation for an unmatched line",
    () => {
        mockUseBankStatement
        .mockReturnValue({
            data: {
            ...statement,
            lines: [
                unmatchedLine,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        renderDialog();

        fireEvent.click(
        screen.getByRole(
            "button",
            {
            name: /ignore/i,
            },
        ),
        );

        expect(
        mockIgnoreMutate,
        ).toHaveBeenCalledWith({
        statementId: "statement-1",
        lineNumber: 1,
        });
    },
    );

    it(
    "manually matches a selected transaction",
    () => {
        mockUseBankStatement
        .mockReturnValue({
            data: {
            ...statement,
            lines: [
                unmatchedLine,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        mockUseBankTransactionList
        .mockReturnValue({
            data: {
            bank_transactions: [
                availableTransaction,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        renderDialog();

        changeControl(
        screen.getByRole(
            "combobox",
        ),
        {
            target: {
            value: "transaction-1",
            },
        },
        );

        fireEvent.click(
        screen.getByRole(
            "button",
            {
            name: /^match$/i,
            },
        ),
        );

        expect(
        mockMatchMutate,
        ).toHaveBeenCalledWith(
        {
            statementId: "statement-1",
            lineNumber: 1,
            transactionId:
            "transaction-1",
        },
        expect.objectContaining({
            onSuccess:
            expect.any(Function),
        }),
        );
    },
    );

    it(
    "disables manual match until a transaction is selected",
    () => {
        mockUseBankStatement
        .mockReturnValue({
            data: {
            ...statement,
            lines: [
                unmatchedLine,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        mockUseBankTransactionList
        .mockReturnValue({
            data: {
            bank_transactions: [
                availableTransaction,
            ],
            },
            isLoading: false,
            isError: false,
            error: null,
        });

        renderDialog();

        expect(
        screen.getByRole(
            "button",
            {
            name: /^match$/i,
            },
        ),
        ).toBeDisabled();
    },
    );
    it(
      "calculates reconciliation progress",
      () => {
        renderDialog();

        expect(
          screen.getByText(
            "2 of 5 · 40%",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows statement loading state",
      () => {
        mockUseBankStatement
          .mockReturnValue({
            data: undefined,
            isLoading: true,
            isError: false,
            error: null,
          });

        renderDialog();

        expect(
          screen.getByText(
            "Loading statement...",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows statement error",
      () => {
        mockUseBankStatement
          .mockReturnValue({
            data: undefined,
            isLoading: false,
            isError: true,
            error: new Error(
              "Unable to load statement",
            ),
          });

        renderDialog();

        expect(
          screen.getByRole("alert"),
        ).toHaveTextContent(
          "Unable to load statement",
        );
      },
    );

    it(
      "shows empty statement message",
      () => {
        mockUseBankStatement
          .mockReturnValue({
            data: {
              ...statement,
              line_count: 0,
              matched_count: 0,
              unmatched_count: 0,
              ignored_count: 0,
              lines: [],
            },
            isLoading: false,
            isError: false,
            error: null,
          });

        renderDialog();

        expect(
          screen.getByText(
            "This statement contains no lines.",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "does not render when closed",
      () => {
        const { container } =
          render(
            <BankStatementDetailDialog
              open={false}
              statementId="statement-1"
              canReconcile
              canCancel
              onClose={vi.fn()}
            />,
          );

        expect(
          container,
        ).toBeEmptyDOMElement();
      },
    );

    it(
      "calls cancel mutation",
      () => {
        renderDialog();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: /cancel statement/i,
            },
          ),
        );

        expect(
          mockCancelMutate,
        ).toHaveBeenCalledWith(
          "statement-1",
        );
      },
    );
  },
);
function changeControl(element:HTMLElement, event:{target:{value:string}}){
 if(element.getAttribute('role')==='combobox' && element.tagName==='INPUT'){
  const select=element.parentElement?.querySelector('select');
  const option=Array.from(select?.options??[]).find(o=>o.value===event.target.value);
  fireEvent.focus(element);fireEvent.change(element,{target:{value:option?.text??event.target.value}});
  const button=Array.from(document.querySelectorAll('[role="option"]')??[]).find(b=>b.textContent===option?.text);
  if(!button)throw new Error('Matching option not rendered');fireEvent.click(button);
 }else fireEvent.change(element,event);
}
