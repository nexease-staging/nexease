import type {
  VendorDebitNoteListParameters,
} from "@/features/vendor-debit-notes/types";

export const vendorDebitNoteQueryKeys = {
  all: [
    "vendor-debit-notes",
  ] as const,

  lists: () => [
    ...vendorDebitNoteQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      VendorDebitNoteListParameters,
  ) => [
    ...vendorDebitNoteQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...vendorDebitNoteQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    debitNoteId: string,
  ) => [
    ...vendorDebitNoteQueryKeys.details(),
    debitNoteId,
  ] as const,
};