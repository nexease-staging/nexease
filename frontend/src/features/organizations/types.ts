export interface OrganizationDetail {
  id: string;
  name: string;
  country: string;
  currency: string;
  timezone: string;
  is_active: boolean;
  email: string;
  phone: string | null;
  address: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface OrganizationData {
  organization: OrganizationDetail;
}

export interface UpdateOrganizationInput {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  country?: string;
  currency?: string;
  timezone?: string;
}