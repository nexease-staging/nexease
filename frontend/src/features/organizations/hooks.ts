import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getOrganization,
  updateOrganization,
} from "@/features/organizations/api";

import {
  organizationQueryKeys,
} from "@/features/organizations/query-keys";

import type {
  UpdateOrganizationInput,
} from "@/features/organizations/types";


export function useOrganization(
  enabled = true,
) {
  return useQuery({
    queryKey:
      organizationQueryKeys.current(),

    queryFn:
      getOrganization,

    enabled,

    staleTime: 60_000,
  });
}


export function useUpdateOrganization() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: UpdateOrganizationInput,
    ) =>
      updateOrganization(
        input,
      ),

    onSuccess: (
      organization,
    ) => {
      queryClient.setQueryData(
        organizationQueryKeys.current(),
        organization,
      );
    },
  });
}