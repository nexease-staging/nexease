import type {
  DocumentAccessLogParameters,
  DocumentDeliveryLogParameters,
} from "@/features/documents/types";

export const documentQueryKeys = {
  all: [
    "documents",
  ] as const,

  accessLogs: () => [
    ...documentQueryKeys.all,
    "access-logs",
  ] as const,

  accessLogList: (
    parameters:
      DocumentAccessLogParameters,
  ) => [
    ...documentQueryKeys
      .accessLogs(),
    parameters,
  ] as const,

  accessLogSummary: () => [
    ...documentQueryKeys
      .accessLogs(),
    "summary",
  ] as const,

  deliveryLogs: () => [
    ...documentQueryKeys.all,
    "delivery-logs",
  ] as const,

  deliveryLogList: (
    parameters:
      DocumentDeliveryLogParameters,
  ) => [
    ...documentQueryKeys
      .deliveryLogs(),
    parameters,
  ] as const,

  deliveryLogSummary: () => [
    ...documentQueryKeys
      .deliveryLogs(),
    "summary",
  ] as const,
};