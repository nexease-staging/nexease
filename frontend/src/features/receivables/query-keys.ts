export const receivableQueryKeys = {
  all: [
    "accounts-receivable",
  ] as const,

  summary: () => [
    ...receivableQueryKeys.all,
    "summary",
  ] as const,

  aging: () => [
    ...receivableQueryKeys.all,
    "aging",
  ] as const,
};