export const categoryQueryKeys = {
  all: ["categories"] as const,

  list: () => [...categoryQueryKeys.all, "list"] as const,

  detail: (categoryId: string) =>
    [...categoryQueryKeys.all, "detail", categoryId] as const,
};