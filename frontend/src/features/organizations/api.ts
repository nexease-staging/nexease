import {
  apiRequest,
} from "@/lib/api/client";

import type {
  OrganizationData,
  OrganizationDetail,
  UpdateOrganizationInput,
} from "@/features/organizations/types";


export async function getOrganization():
Promise<OrganizationDetail> {
  const response =
    await apiRequest<OrganizationData>(
      "/organization/",
    );

  return response.data.organization;
}


export async function updateOrganization(
  input: UpdateOrganizationInput,
): Promise<OrganizationDetail> {
  const response =
    await apiRequest<OrganizationData>(
      "/organization/",
      {
        method: "PATCH",
        body: input,
      },
    );

  return response.data.organization;
}