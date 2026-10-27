import type {
  CreditNoteListParameters,
} from "@/features/credit-notes/types";

export const creditNoteQueryKeys = {
  all: [
    "credit-notes",
  ] as const,

  lists: () => [
    ...creditNoteQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      CreditNoteListParameters,
  ) => [
    ...creditNoteQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...creditNoteQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    creditNoteId: string,
  ) => [
    ...creditNoteQueryKeys.details(),
    creditNoteId,
  ] as const,
};