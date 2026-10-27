import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import ReportExportActions
  from "@/features/documents/components/report-export-actions";

const mockExportMutateAsync =
  vi.fn();

let mockIsPending = false;

vi.mock(
  "@/lib/api/client",
  () => ({
    APIRequestError:
      class APIRequestError
        extends Error {},
  }),
);

vi.mock(
  "@/features/documents/hooks",
  () => ({
    useExportResource: () => ({
      mutateAsync:
        mockExportMutateAsync,

      isPending:
        mockIsPending,
    }),
  }),
);

describe(
  "ReportExportActions",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mockIsPending = false;

      mockExportMutateAsync
        .mockResolvedValue(
          undefined,
        );
    });

    it(
      "renders CSV and XLSX export actions",
      () => {
        render(
          <ReportExportActions
            resourceType={
              "GENERAL_LEDGER"
            }
          />,
        );

        expect(
          screen.getByRole(
            "button",
            {
              name: "CSV",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name: "XLSX",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "exports CSV with report parameters",
      async () => {
        render(
          <ReportExportActions
            resourceType={
              "GENERAL_LEDGER"
            }
            parameters={{
              account_id:
                "account-1",
              start_date:
                "2026-09-01",
              end_date:
                "2026-09-30",
            }}
          />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "CSV",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockExportMutateAsync,
          ).toHaveBeenCalledTimes(
            1,
          );
        });

        expect(
          mockExportMutateAsync,
        ).toHaveBeenCalledWith({
          resourceType:
            "GENERAL_LEDGER",

          format:
            "csv",

          parameters: {
            account_id:
              "account-1",

            start_date:
              "2026-09-01",

            end_date:
              "2026-09-30",
          },
        });
      },
    );

    it(
      "exports XLSX with report parameters",
      async () => {
        render(
          <ReportExportActions
            resourceType={
              "TRIAL_BALANCE"
            }
            parameters={{
              as_of_date:
                "2026-09-01",
              include_zero_balances:
                true,
            }}
          />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "XLSX",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockExportMutateAsync,
          ).toHaveBeenCalledTimes(
            1,
          );
        });

        expect(
          mockExportMutateAsync,
        ).toHaveBeenCalledWith({
          resourceType:
            "TRIAL_BALANCE",

          format:
            "xlsx",

          parameters: {
            as_of_date:
              "2026-09-01",

            include_zero_balances:
              true,
          },
        });
      },
    );

    it(
      "uses empty parameters by default",
      async () => {
        render(
          <ReportExportActions
            resourceType={
              "FINANCE_AUDIT"
            }
          />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "CSV",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockExportMutateAsync,
          ).toHaveBeenCalledWith({
            resourceType:
              "FINANCE_AUDIT",

            format:
              "csv",

            parameters: {},
          });
        });
      },
    );

    it(
      "shows an export error",
      async () => {
        mockExportMutateAsync
          .mockRejectedValue(
            new Error(
              "Report export failed",
            ),
          );

        render(
          <ReportExportActions
            resourceType={
              "CASH_FLOW"
            }
          />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "CSV",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Report export failed",
        );
      },
    );

    it(
      "disables both actions when disabled",
      () => {
        render(
          <ReportExportActions
            resourceType={
              "GENERAL_LEDGER"
            }
            disabled
          />,
        );

        expect(
          screen.getByRole(
            "button",
            {
              name: "CSV",
            },
          ),
        ).toBeDisabled();

        expect(
          screen.getByRole(
            "button",
            {
              name: "XLSX",
            },
          ),
        ).toBeDisabled();
      },
    );

    it(
      "disables both actions while export is pending",
      () => {
        mockIsPending = true;

        render(
          <ReportExportActions
            resourceType={
              "GENERAL_LEDGER"
            }
          />,
        );

        expect(
          screen.getByRole(
            "button",
            {
              name: "Exporting...",
            },
          ),
        ).toBeDisabled();

        expect(
          screen.getByRole(
            "button",
            {
              name: "XLSX",
            },
          ),
        ).toBeDisabled();
      },
    );
  },
);