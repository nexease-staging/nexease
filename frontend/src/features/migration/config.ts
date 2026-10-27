import type {
  MigrationType,
} from "@/features/migration/types";


export interface MigrationTypeConfig {
  type: MigrationType;
  label: string;
  description: string;
  requiredColumns: string[];
}


export const migrationTypeConfigs:
  MigrationTypeConfig[] = [
    {
      type: "CATEGORIES",
      label: "Categories",
      description:
        "Import product categories.",
      requiredColumns: [
        "Category Name",
      ],
    },
    {
      type: "PRODUCTS",
      label: "Products",
      description:
        "Import products and item master data.",
      requiredColumns: [
        "SKU",
        "Product Name",
      ],
    },
    {
      type: "CUSTOMERS",
      label: "Customers",
      description:
        "Import customer master data.",
      requiredColumns: [
        "Customer Name",
      ],
    },
    {
      type: "SUPPLIERS",
      label: "Suppliers",
      description:
        "Import supplier master data.",
      requiredColumns: [
        "Supplier Name",
      ],
    },
    {
      type: "WAREHOUSES",
      label: "Warehouses",
      description:
        "Import warehouse master data.",
      requiredColumns: [
        "Warehouse Code",
        "Warehouse Name",
      ],
    },
    {
      type: "INVENTORY",
      label: "Opening Inventory",
      description:
        "Import opening stock by product and warehouse.",
      requiredColumns: [
        "Product SKU",
        "Warehouse Code",
        "Opening Quantity",
      ],
    },
    {
      type: "SALES_ORDERS",
      label: "Sales Orders",
      description:
        "Import historical sales orders.",
      requiredColumns: [],
    },
    {
      type: "SALES_INVOICES",
      label: "Sales Invoices",
      description:
        "Import sales invoices from fulfilled sales orders.",
      requiredColumns: [
        "Invoice Number",
        "Sales Order Number",
        "Invoice Date",
      ],
    },
    {
      type: "CUSTOMER_PAYMENTS",
      label: "Customer Payments",
      description:
        "Import historical customer payments.",
      requiredColumns: [],
    },
    {
      type: "PURCHASE_ORDERS",
      label: "Purchase Orders",
      description:
        "Import historical purchase orders.",
      requiredColumns: [],
    },
    {
      type: "GOODS_RECEIPTS",
      label: "Goods Receipts",
      description:
        "Import historical goods receipts.",
      requiredColumns: [],
    },
    {
      type: "EMPLOYEES",
      label: "Employees",
      description: "Import employees and pay details. Requires payroll management access.",
      requiredColumns: ["code","name","joining_date","basis","rate"],
    },
    {
      type: "VENDOR_BILLS",
      label: "Vendor Bills",
      description:
        "Import historical vendor bills.",
      requiredColumns: [],
    },
    {
      type: "SUPPLIER_PAYMENTS",
      label: "Supplier Payments",
      description:
        "Import historical supplier payments.",
      requiredColumns: [],
    },
  ];


export function getMigrationTypeConfig(
  migrationType: MigrationType,
): MigrationTypeConfig {
  const config =
    migrationTypeConfigs.find(
      (item) =>
        item.type === migrationType,
    );

  if (!config) {
    throw new Error(
      `Unknown migration type: ${migrationType}`,
    );
  }

  return config;
}

export const DEFAULT_MIGRATION_SOURCE_SYSTEM =
  "GENERIC";