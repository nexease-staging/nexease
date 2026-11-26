import {
  AlarmClock, ArrowDownUp, BadgePercent, BookOpen, Boxes, ChartLine, ChartNoAxesCombined, ClipboardList, FileText, Landmark,
  Layers, PackageMinus, PiggyBank, ReceiptIndianRupee, ReceiptText, Scale, ShoppingCart, Tags, TrendingUp, Truck, Users, Wallet,
  type LucideIcon,
} from "lucide-react";

export interface ReportEntry {
  /** Engine id ("sales/item") or an app route ("/trial-balance"). */
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  /** Any one of these permissions shows the report; the server still checks. */
  permissions: string[];
}

export interface ReportGroup {
  name: string;
  reports: ReportEntry[];
}

const r = (id: string, title: string, description: string, icon: LucideIcon, ...permissions: string[]): ReportEntry => ({ id, title, description, icon, permissions });

export const reportGroups: ReportGroup[] = [
  {
    name: "Business overview",
    reports: [
      r("overview/monthly", "Monthly business overview", "Sales, purchases and expenses month by month", ChartNoAxesCombined, "invoices.read", "bills.read", "expenses.read"),
      r("sales/trend", "Sales trend", "Daily or monthly sales with change over the previous period", TrendingUp, "invoices.read"),
      r("purchases/trend", "Purchase trend", "Daily or monthly purchases", ChartLine, "bills.read"),
      r("profit/item", "Gross profit by item", "Sales, cost and margin for every item sold", PiggyBank, "products.read_cost"),
      r("profit/party", "Gross profit by customer", "Which customers bring the most margin", PiggyBank, "products.read_cost"),
    ],
  },
  {
    name: "Sales",
    reports: [
      r("sales/document", "Sales transactions", "Every issued invoice with GSTIN, GST and total", ReceiptText, "invoices.read"),
      r("sales/party", "Sales by customer", "Top customers and their share of sales", Users, "invoices.read"),
      r("sales/item", "Item sales", "Quantity, average rate and value per item", Boxes, "invoices.read"),
      r("sales/category", "Sales by item category", "Sales grouped by product category", Layers, "invoices.read"),
      r("sales/party-item", "Customer and item", "What each customer bought", ClipboardList, "invoices.read"),
      r("sales/discount", "Invoice discounts", "Invoices with discounts and the discount rate", BadgePercent, "invoices.read"),
      r("sales/item-discount", "Item-wise discounts", "Discount given per item", BadgePercent, "invoices.read"),
      r("/accounts-receivable", "Customer outstanding", "Who owes you, with aging", AlarmClock, "invoices.read"),
    ],
  },
  {
    name: "Purchases",
    reports: [
      r("purchases/document", "Purchase transactions", "Every posted vendor bill", FileText, "bills.read"),
      r("purchases/party", "Purchases by supplier", "Top suppliers and their share", Truck, "bills.read"),
      r("purchases/item", "Item purchases", "Quantity, average rate and value per item", Boxes, "bills.read"),
      r("purchases/category", "Purchases by item category", "Purchases grouped by product category", Layers, "bills.read"),
      r("purchases/party-item", "Supplier and item", "What you bought from each supplier", ClipboardList, "bills.read"),
      r("/accounts-payable", "Supplier outstanding", "What you owe, oldest first", Wallet, "bills.read"),
    ],
  },
  {
    name: "GST",
    reports: [
      r("/taxation/workpapers", "GSTR-1, GSTR-3B and GSTR-9 workpapers", "Return-ready summaries", Landmark, "taxation.read"),
      r("sales/hsn", "Sales summary by HSN", "Goods sold by HSN code, for GSTR-1", ReceiptIndianRupee, "taxation.read"),
      r("sales/sac", "Sales summary by SAC", "Services sold by SAC code", ReceiptIndianRupee, "taxation.read"),
      r("sales/rate", "Sales by GST rate", "Taxable value and GST at each rate", BadgePercent, "taxation.read"),
      r("purchases/hsn", "Purchases by HSN", "Goods bought by HSN code", ReceiptIndianRupee, "taxation.read"),
      r("purchases/rate", "Purchases by GST rate", "Input tax at each rate", BadgePercent, "taxation.read"),
    ],
  },
  {
    name: "Stock",
    reports: [
      r("inventory/low", "Low stock summary", "Items at or below their reorder level", PackageMinus, "inventory.read"),
      r("inventory/category", "Stock by category", "Quantity and value at cost per category", Layers, "inventory.read"),
      r("/inventory", "Stock summary", "Current stock by item and warehouse", Boxes, "inventory.read"),
      r("/stock-movements", "Stock movements", "Every stock in and out", ArrowDownUp, "inventory.read"),
    ],
  },
  {
    name: "Expenses",
    reports: [
      r("expenses/document", "Expense transactions", "Every expense with payee and mode", ReceiptText, "expenses.read"),
      r("expenses/category", "Expenses by category", "Where the money goes", Tags, "expenses.read"),
      r("expenses/item", "Expenses by description", "Repeated expenses grouped together", Tags, "expenses.read"),
    ],
  },
  {
    name: "Orders",
    reports: [
      r("sales-orders/document", "Sales order transactions", "Open and fulfilled sales orders", ShoppingCart, "sales_orders.read"),
      r("sales-orders/item", "Sales order items", "Ordered quantity per item", ShoppingCart, "sales_orders.read"),
      r("purchase-orders/document", "Purchase order transactions", "Purchase orders placed", Truck, "purchase_orders.read"),
      r("purchase-orders/item", "Purchase order items", "Ordered quantity per item", Truck, "purchase_orders.read"),
    ],
  },
  {
    name: "Accounts",
    reports: [
      r("/profit-and-loss", "Profit & loss", "Income and expenses from the ledger", Scale, "accounting_reports.read"),
      r("/balance-sheet", "Balance sheet", "Assets, liabilities and equity", Scale, "accounting_reports.read"),
      r("/cash-flow", "Cash flow", "Money in and out of bank and cash", Wallet, "bank_transactions.read"),
      r("/trial-balance", "Trial balance", "Debit and credit balance per ledger", BookOpen, "trial_balance.read"),
      r("/general-ledger", "General ledger", "Every posting for a ledger account", BookOpen, "general_ledger.read"),
      r("/journal-entries", "Day book", "All journal entries by date", BookOpen, "journal_entries.read"),
      r("/banking", "Bank statements", "Bank and cash account transactions", Landmark, "bank_accounts.read"),
      r("/workforce/advances", "Employee advances", "Advances given and recovered", Users, "payroll.read"),
    ],
  },
];

export const allReports = reportGroups.flatMap((g) => g.reports.map((report) => ({ ...report, group: g.name })));
export const findReport = (id: string) => allReports.find((report) => report.id === id);
export const isEngineReport = (id: string) => !id.startsWith("/");
export const reportHref = (id: string) => (isEngineReport(id) ? `/reports/view?id=${encodeURIComponent(id)}` : id);

const FAVOURITES = "nx-report-favourites";
const RECENT = "nx-report-recent";

function read(key: string): string[] {
  try {
    const value = JSON.parse(window.localStorage.getItem(key) ?? "[]");
    return Array.isArray(value) ? value.filter((v) => typeof v === "string") : [];
  } catch {
    return [];
  }
}

function write(key: string, value: string[]) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* Private mode or storage full: favourites simply are not kept. */
  }
}

export const favourites = {
  list: () => read(FAVOURITES),
  toggle: (id: string) => {
    const current = read(FAVOURITES);
    const next = current.includes(id) ? current.filter((x) => x !== id) : [id, ...current].slice(0, 12);
    write(FAVOURITES, next);
    return next;
  },
};

export const recent = {
  list: () => read(RECENT),
  add: (id: string) => write(RECENT, [id, ...read(RECENT).filter((x) => x !== id)].slice(0, 6)),
};
