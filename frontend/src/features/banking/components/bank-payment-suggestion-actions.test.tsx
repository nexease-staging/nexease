import type {
  BankPaymentSuggestionSummary,
} from "@/features/banking/types";
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

import BankPaymentSuggestionActions
  from "@/features/banking/components/bank-payment-suggestion-actions";

const mockGenerateMutate = vi.fn();
const mockConfirmMutate = vi.fn();
const mockRejectMutate = vi.fn();
const mockExecuteMutate = vi.fn();

vi.mock(
  "@/features/banking/hooks",
  () => ({
    useGenerateBankPaymentSuggestion: () => ({
      mutate: mockGenerateMutate,
      isPending: false,
      error: null,
    }),

    useConfirmBankPaymentSuggestion: () => ({
      mutate: mockConfirmMutate,
      isPending: false,
      error: null,
    }),

    useRejectBankPaymentSuggestion: () => ({
      mutate: mockRejectMutate,
      isPending: false,
      error: null,
    }),

    useExecuteBankPaymentSuggestion: () => ({
      mutate: mockExecuteMutate,
      isPending: false,
      error: null,
    }),
  }),
);

const pendingSuggestion:
  BankPaymentSuggestionSummary = {
    id: "suggestion-1",

    statement: {
      id: "statement-1",
      statement_number: "BST-001",

      bank_account: {
        id: "account-1",
        account_name: "Current",
        account_type: "BANK",
        bank_name: "Test Bank",
        account_number: "1234567890",
        ifsc_code: "TEST0001234",
        currency: "INR",
        opening_balance: "10000.00",
        current_balance: "10500.00",
        is_active: true,
      },

      statement_start_date:
        "2026-09-01",

      statement_end_date:
        "2026-09-01",

      opening_balance:
        "10000.00",

      closing_balance:
        "10500.00",

      source_filename:
        "test_statement.csv",

      source_type:
        "CSV",

      status:
        "PARTIALLY_RECONCILED",

      line_count: 1,
      matched_count: 0,
      ignored_count: 0,
      unmatched_count: 1,

      created_at:
        "2026-09-01T00:00:00Z",

      updated_at:
        "2026-09-01T00:00:00Z",
    },

    line_number:
      "1",

    suggestion_type:
      "CUSTOMER_RECEIPT",

    invoice: {
      id: "invoice-1",
      invoice_number: "INV-001",

      sales_order: null,

      customer: {
        id: "customer-1",
        code: "CUS-001",
        name: "Test Customer",
        email: "customer@example.com",
        phone: null,
        gstin: null,
        city: null,
        state: null,
        country: "India",
        is_active: true,
      },

      status: "ISSUED",

      invoice_date:
        "2026-09-01",

      due_date:
        "2026-09-30",

      subtotal:
        "500.00",

      tax_amount:
        "0.00",

      discount_amount:
        "0.00",

      total_amount:
        "500.00",

      amount_paid:
        "0.00",

      balance_due:
        "500.00",

      item_count: 1,

      created_at:
        "2026-09-01T00:00:00Z",

      updated_at:
        "2026-09-01T00:00:00Z",
    },

    vendor_bill:
      null,

    amount:
      "500.00",

    confidence:
      "1.00",

    match_reason:
      "Reference matched",

    status:
      "PENDING",

    is_executed:
      false,

    payment_reference:
      null,

    created_at:
      "2026-09-01T00:00:00Z",

    updated_at:
      "2026-09-01T00:00:00Z",
  };

function renderActions(
  suggestion:
    BankPaymentSuggestionSummary | null,
) {
  return render(
    <BankPaymentSuggestionActions
      statementId="statement-1"
      lineNumber={1}
      currency="INR"
      suggestion={suggestion}
    />,
  );
}

describe(
  "BankPaymentSuggestionActions",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it(
      "generates suggestion when none exists",
      () => {
        renderActions(null);

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: /suggest payment/i,
            },
          ),
        );

        expect(
          mockGenerateMutate,
        ).toHaveBeenCalledWith({
          statementId: "statement-1",
          lineNumber: 1,
        });
      },
    );

    it(
      "confirms pending suggestion",
      () => {
        renderActions(
          pendingSuggestion,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: /confirm/i,
            },
          ),
        );

        expect(
          mockConfirmMutate,
        ).toHaveBeenCalledWith(
          "suggestion-1",
        );
      },
    );

    it(
      "rejects pending suggestion",
      () => {
        renderActions(
          pendingSuggestion,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: /reject/i,
            },
          ),
        );

        expect(
          mockRejectMutate,
        ).toHaveBeenCalledWith(
          "suggestion-1",
        );
      },
    );

    it(
      "executes confirmed suggestion",
      () => {
        renderActions({
          ...pendingSuggestion,
          status: "CONFIRMED",
        });

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: /execute payment/i,
            },
          ),
        );

        expect(
          mockExecuteMutate,
        ).toHaveBeenCalledWith(
          "suggestion-1",
        );
      },
    );

    it(
      "does not allow regeneration after rejection",
      () => {
        renderActions({
          ...pendingSuggestion,
          status: "REJECTED",
        });

        expect(
          screen.queryByRole(
            "button",
            {
              name: /generate again/i,
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByText(
            /suggestion rejected/i,
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows executed suggestion without further actions",
      () => {
        renderActions({
          ...pendingSuggestion,
          status: "CONFIRMED",
          is_executed: true,
          payment_reference:
            "PAY-TEST-001",
        });

        expect(
          screen.queryByRole(
            "button",
            {
              name: /execute payment/i,
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name: /confirm/i,
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name: /reject/i,
            },
          ),
        ).not.toBeInTheDocument();
      },
    );
  },
);