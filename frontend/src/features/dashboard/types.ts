export interface DashboardParameters {
  start_date?: string;
  end_date?: string;
}

export interface DashboardPeriod {
  start_date: string;
  end_date: string;
}

export interface DashboardKPIs {
  total_sales: string;
  total_purchases: string;
  receivables: string;
  payables: string;
  bank_balance: string;
  inventory_value: string;
  out_of_stock_items: number;
}

export interface DashboardTrendPoint {
  period: string;
  amount: string;
}

export interface DashboardCashFlowPoint {
  period: string;
  inflow: string;
  outflow: string;
  net: string;
}

export interface DashboardReceivableAging {
  current: string;
  "1_30": string;
  "31_60": string;
  "61_90": string;
  "90_plus": string;
}

export interface DashboardInvoiceStatus {
  issued: number;
  partially_paid: number;
  paid: number;
  overdue: number;
}

export interface DashboardBillStatus {
  posted: number;
  partially_paid: number;
  paid: number;
  overdue: number;
}

export interface DashboardInventoryStatus {
  in_stock: number;
  out_of_stock: number;
}

export interface DashboardTopCustomer {
  customer_id: string;
  customer_name: string;
  amount: string;
}

export interface DashboardTopSupplier {
  supplier_id: string;
  supplier_name: string;
  amount: string;
}

export interface DashboardAlerts {
  overdue_invoices: number;
  overdue_bills: number;
  out_of_stock_items: number;
}

export type DashboardActivityType =
  | "INVOICE"
  | "VENDOR_BILL"
  | "BANK_TRANSACTION"
  | "STOCK_MOVEMENT";

export interface DashboardRecentActivity {
  activity_type: DashboardActivityType;
  reference_id: string;
  reference_number: string;
  description: string;
  activity_date: string;
  amount: string | null;
  quantity?: string;
}

export interface MainDashboard {
  period: DashboardPeriod;
  kpis: DashboardKPIs;
  sales_trend: DashboardTrendPoint[];
  purchase_trend: DashboardTrendPoint[];
  cash_flow: DashboardCashFlowPoint[];
  receivable_aging: DashboardReceivableAging;
  invoice_status: DashboardInvoiceStatus;
  bill_status: DashboardBillStatus;
  inventory_status: DashboardInventoryStatus;
  top_customers: DashboardTopCustomer[];
  top_suppliers: DashboardTopSupplier[];
  alerts: DashboardAlerts;
  recent_activity: DashboardRecentActivity[];
}

export interface MainDashboardData {
  dashboard: MainDashboard;
}