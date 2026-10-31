import type {
  LucideIcon,
} from "lucide-react";

import {
  Database,
  ListChecks,
  Activity,
  ChartSpline,
  BookOpen,
  Scale,
  ArrowDownUp,
  Banknote,
  Boxes,
  Building2,
  ChartNoAxesCombined,
  CircleDollarSign,
  ClipboardList,
  FileMinus2,
  FileText,
  LayoutDashboard,
  Package,
  PackageCheck,
  ReceiptText,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Tags,
  Truck,
  Undo2,
  UserRoundCog,
  Users,
  Warehouse,
} from "lucide-react";

export interface NavigationItem {
  label: string;
  href: string;
  icon: LucideIcon;
  permission?: string;
}

export interface NavigationSection {
  label: string;
  items: NavigationItem[];
}

export const navigationSections:
  NavigationSection[] = [
    {label:"Barcode",items:[{label:"Barcode inventory",href:"/barcode",icon:Boxes,permission:"inventory.read"}]},
    {label:"Expenses",items:[{label:"Daily expenses",href:"/expenses",icon:ReceiptText,permission:"expenses.read"}]},
    {label:"Workforce",items:[{label:"Workforce dashboard",href:"/workforce",icon:Users,permission:"payroll.read"},{label:"Sites & attendance",href:"/workforce/sites",icon:Building2,permission:"labour.read"}]},
    {label:"Taxation",items:[{label:"GST & tax workpapers",href:"/taxation",icon:ReceiptText,permission:"taxation.read"}]},
    {
      label: "Overview",
      items: [
        {
          label: "Dashboard",
          href: "/dashboard",
          icon: LayoutDashboard,
        },
      ],
    },

    {
      label: "Inventory",
      items: [
        {
          label: "Products",
          href: "/products",
          icon: Package,
          permission: "products.read",
        },
        {
          label: "Warehouses",
          href: "/warehouses",
          icon: Warehouse,
          permission: "warehouses.read",
        },
          {
            label: "Stock",
            href: "/inventory",
            icon: Boxes,
            permission: "inventory.read",
          },
          {
            label: "Stock Movements",
            href: "/stock-movements",
            icon: ArrowDownUp,
            permission: "inventory.read",
          },
          {
            label: "Stock Transfers",
            href: "/stock-transfers",
            icon: Truck,
            permission: "inventory.read",
          },
      ],
    },

    {
      label: "Sales",
      items: [
        {
          label: "Customers",
          href: "/customers",
          icon: Users,
          permission: "customers.read",
        },
        {
          label: "Sales Orders",
          href: "/sales-orders",
          icon: ShoppingCart,
          permission: "sales_orders.read",
        },
        {
          label: "Invoices",
          href: "/invoices",
          icon: ReceiptText,
          permission: "invoices.read",
        },
          {
            label: "Customer Payments",
            href: "/customer-payments",
            icon: Banknote,
            permission: "customer_payments.read",
          },
          {
            label: "Receivables",
            href: "/accounts-receivable",
            icon: ChartNoAxesCombined,
            permission: "invoices.read",
          },
        {
          label: "Sales Returns",
          href: "/sales-returns",
          icon: Undo2,
          permission: "sales_returns.read",
        },
        {
          label: "Credit Notes",
          href: "/credit-notes",
          icon: FileText,
          permission: "credit_notes.read",
        },
      ],
    },

    {
      label: "Purchasing",
      items: [
        {
          label: "Suppliers",
          href: "/suppliers",
          icon: Truck,
          permission: "suppliers.read",
        },
        {
          label: "Purchase Orders",
          href: "/purchase-orders",
          icon: ClipboardList,
          permission: "purchase_orders.read",
        },
        {
          label: "Goods Receipts",
          href: "/goods-receipts",
          icon: PackageCheck,
          permission:
            "goods_receipts.read",
        },
        {
          label: "Vendor Bills",
          href: "/vendor-bills",
          icon: FileText,
          permission: "bills.read",
        },
        {
          label: "Accounts Payable",
          href: "/accounts-payable",
          icon: CircleDollarSign,
          permission: "bills.read",
        },
        {
          label: "Purchase Returns",
          href: "/purchase-returns",
          icon: Undo2,
          permission: "purchase_returns.read",
        },
        {
          label: "Vendor Debit Notes",
          href: "/vendor-debit-notes",
          icon: FileMinus2,
          permission:
            "vendor_debit_notes.read",
        },
      ],
    },

      {
        label: "Finance",
        items: [
          {
            label: "Financial Dashboard",
            href: "/financial-dashboard",
            icon: ChartNoAxesCombined,
            permission:
              "accounting_reports.read",
          },
          {
            label: "Cash Flow",
            href: "/cash-flow",
            icon: ChartSpline,
            permission:
              "bank_transactions.read",
          },
          {
            label: "Finance Audit",
            href: "/finance-audit",
            icon: Activity,
            permission:
              "bank_transactions.read",
          },
          {
            label: "Document Activity",
            href: "/document-logs",
            icon: Activity,
            permission:
              "accounting_audit.read",
          },
          {
            label: "Chart of Accounts",
            href: "/chart-of-accounts",
            icon: ChartNoAxesCombined,
            permission:
              "chart_of_accounts.read",
          },
          {
            label: "Journal Entries",
            href: "/journal-entries",
            icon: ReceiptText,
            permission:
              "journal_entries.read",
          },
          {
            label: "General Ledger",
            href: "/general-ledger",
            icon: BookOpen,
            permission:
              "general_ledger.read",
          },
          {
            label: "Trial Balance",
            href: "/trial-balance",
            icon: Scale,
            permission:
              "trial_balance.read",
          },
          {
            label: "Banking",
            href: "/banking",
            icon: Banknote,
            permission:
              "bank_accounts.read",
          },
        ],
      },

    {
      label: "Administration",
      items: [
        {
          label: "Invoice formats & logo",
          href: "/settings/invoices",
          icon: FileText,
          permission: "organizations.update",
        },
        {
          label: "Organization",
          href: "/settings/organization",
          icon: Building2,
          permission: "organizations.update",
        },
        {
          label: "Categories",
          href: "/settings/categories",
          icon: Tags,
          permission: "products.read",
        },
        {
          label: "Users",
          href: "/settings/users",
          icon: UserRoundCog,
          permission: "users.read",
        },
        {
          label: "Roles",
          href: "/settings/roles",
          icon: ShieldCheck,
          permission: "roles.read",
        },
        {
          label: "Permissions",
          href: "/settings/permissions",
          icon: Tags,
          permission: "permissions.read",
        },
        {
          label: "Authentication Audit",
          href: "/settings/audit",
          icon: ShieldCheck,
          permission: "accounting_audit.read",
        },
        {
          label: "Data Migration",
          href: "/data-migration",
          icon: Database,
        },
        {
          label: "Background Jobs",
          href: "/background-jobs",
          icon: ListChecks,
        },
        {
          label: "Settings",
          href: "/settings",
          icon: Settings,
        },
      ],
    },
  ];
export const workforceSections: NavigationSection[] = [{label:'Workforce',items:[
 {label:'Dashboard',href:'/workforce',icon:LayoutDashboard},
 ...([
 ['Employees','employees','payroll.read'],['Client sites','sites','labour.read'],['Assignments','assignments','labour.read'],['Daily attendance','attendance','labour.read'],['Timesheets','timesheets','labour.read'],['Leave & approvals','leave','payroll.read'],['Monthly pay inputs','inputs','payroll.read'],['Pay runs','payruns','payroll.read'],['Payslips','payslips','payroll.read'],['Advances','advances','payroll.read'],['Client billing','billing','labour.read'],['Accounts','accounts','accounting_reports.read'],['Reports','reports','payroll.read'],['Settings','settings','payroll.read']
 ]).map(([label,path,permission])=>({label,href:'/workforce/'+path,permission,icon:path==='settings'?Settings:ClipboardList}))
]}];
