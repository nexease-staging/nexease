import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';
import { useInvoiceOverview } from './overview-hook';
const api = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api/client', () => ({ apiRequest: api }));
beforeEach(() => api.mockReset());
function setup(enabled: boolean) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const result = renderHook(() => useInvoiceOverview(enabled), { wrapper: ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider> });
  return { ...result, client };
}
it('loads invoice KPIs without the dashboard and refreshes on invoice invalidation', async () => {
  api.mockResolvedValue({ data: { kpis: { receivables: '100.00', total_sales: '200.00' }, alerts: { overdue_invoices: 1 } } });
  const { result, client } = setup(true);
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(api).toHaveBeenCalledExactlyOnceWith('/invoices/overview/');
  await act(async () => { await client.invalidateQueries({ queryKey: ['invoices', 'list'] }); });
  expect(api).toHaveBeenCalledTimes(2);
  expect(result.current.data?.kpis.receivables).toBe('100.00');
});
it('does not request financial KPIs when report access is absent', () => {
  setup(false);
  expect(api).not.toHaveBeenCalled();
});
