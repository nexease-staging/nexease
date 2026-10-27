import type {
  InvoiceListParameters,
} from "@/features/invoices/types";

export const invoiceQueryKeys = {
  all: [
    "invoices",
  ] as const,

  lists: () => [
    ...invoiceQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      InvoiceListParameters,
  ) => [
    ...invoiceQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...invoiceQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    invoiceId: string,
  ) => [
    ...invoiceQueryKeys.details(),
    invoiceId,
  ] as const,

  bankAccounts: () => [
    ...invoiceQueryKeys.all,
    "bank-accounts",
  ] as const,
};