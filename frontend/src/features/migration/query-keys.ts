export const migrationQueryKeys = {
  all: [
    "migrations",
  ] as const,

  lists: () => [
    ...migrationQueryKeys.all,
    "list",
  ] as const,

  list: (
    limit: number,
  ) => [
    ...migrationQueryKeys.lists(),
    {
      limit,
    },
  ] as const,

  details: () => [
    ...migrationQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    batchId: string,
  ) => [
    ...migrationQueryKeys.details(),
    batchId,
  ] as const,
};