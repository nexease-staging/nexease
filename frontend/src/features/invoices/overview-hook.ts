import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '@/lib/api/client';

export interface InvoiceOverview {
  kpis: { receivables: string; total_sales: string };
  alerts: { overdue_invoices: number };
}

export function useInvoiceOverview(enabled: boolean) {
  return useQuery({
    // Existing invoice mutation hooks invalidate this prefix after saves/payments.
    queryKey: ['invoices', 'list', 'overview'],
    queryFn: async () => (await apiRequest<InvoiceOverview>('/invoices/overview/')).data,
    enabled,
    staleTime: 30_000,
  });
}
