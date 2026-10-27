import {
  useQuery,
} from "@tanstack/react-query";

import {
  getAccountsReceivable,
  getReceivableAging,
} from "@/features/receivables/api";

import {
  receivableQueryKeys,
} from "@/features/receivables/query-keys";

export function useAccountsReceivable() {
  return useQuery({
    queryKey:
      receivableQueryKeys.summary(),

    queryFn:
      getAccountsReceivable,

    staleTime: 30_000,
  });
}

export function useReceivableAging() {
  return useQuery({
    queryKey:
      receivableQueryKeys.aging(),

    queryFn:
      getReceivableAging,

    staleTime: 30_000,
  });
}