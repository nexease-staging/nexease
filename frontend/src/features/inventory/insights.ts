import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";

export interface InsightItem {
  product_id: string;
  sku: string;
  name: string;
  unit: string;
  cost_price: string;
  on_hand: string;
  reserved: string;
  available: string;
}

export interface LowStockItem extends InsightItem {
  reorder_level: string;
  suggested_quantity: string;
  supplier: { id: string; code: string; name: string; last_rate: string; last_po: string } | null;
}

export interface DeadStockItem extends InsightItem {
  value: string;
  last_movement: string | null;
}

export interface InventoryInsights {
  as_of: string;
  warehouse_id: string | null;
  dead_days: number;
  summary: {
    stock_value: string;
    products: number;
    in_stock: number;
    out_of_stock: number;
    low_stock: number;
    dead_stock: number;
    dead_stock_value: string;
    unvalued_products: number;
  };
  by_warehouse: Array<{ id: string; name: string; code: string; value: string; units: string }>;
  low_stock: LowStockItem[];
  dead_stock: DeadStockItem[];
}

export const insightsKey = (warehouseId: string, deadDays: number) => ["inventory-insights", warehouseId || "all", deadDays] as const;

export function useInventoryInsights(warehouseId: string, deadDays = 90, enabled = true) {
  return useQuery({
    queryKey: insightsKey(warehouseId, deadDays),
    enabled,
    staleTime: 60_000,
    queryFn: async () => {
      const params = new URLSearchParams({ dead_days: String(deadDays) });
      if (warehouseId) params.set("warehouse_id", warehouseId);
      return (await apiRequest<InventoryInsights>(`/business/inventory-insights/?${params}`)).data;
    },
  });
}

/** Group selected low-stock items by their last supplier so one draft PO can be raised per supplier. */
export function groupBySupplier(items: readonly LowStockItem[]) {
  const groups = new Map<string, { supplier: LowStockItem["supplier"]; items: LowStockItem[] }>();
  for (const item of items) {
    const key = item.supplier?.code ?? "";
    const group = groups.get(key) ?? { supplier: item.supplier, items: [] };
    group.items.push(item);
    groups.set(key, group);
  }
  return [...groups.values()].sort((a, b) => (a.supplier ? 0 : 1) - (b.supplier ? 0 : 1) || b.items.length - a.items.length);
}
