import type {
  VendorBillListParameters,
} from "@/features/vendor-bills/types";

export const vendorBillQueryKeys = {
  all: [
    "vendor-bills",
  ] as const,

  lists: () => [
    ...vendorBillQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      VendorBillListParameters,
  ) => [
    ...vendorBillQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...vendorBillQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    billId: string,
  ) => [
    ...vendorBillQueryKeys.details(),
    billId,
  ] as const,

  bankAccounts: () => [
    ...vendorBillQueryKeys.all,
    "bank-accounts",
  ] as const,

  accountsPayable: () => [
    ...vendorBillQueryKeys.all,
    "accounts-payable",
  ] as const,
};