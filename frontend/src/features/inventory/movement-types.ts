import type { Tone } from "@/components/ui/badge";
import type { StockMovementType } from "./types";

/** Plain-language label, colour and stock direction (+1 in, -1 out, 0 reservation only) per movement type. */
export const movementTypes: Record<StockMovementType, { label: string; tone: Tone; direction: 1 | -1 | 0 }> = {
  OPENING_STOCK: { label: "Opening stock", tone: "info", direction: 1 },
  STOCK_IN: { label: "Stock in", tone: "success", direction: 1 },
  STOCK_OUT: { label: "Stock out", tone: "danger", direction: -1 },
  ADJUSTMENT_IN: { label: "Adjusted up", tone: "success", direction: 1 },
  ADJUSTMENT_OUT: { label: "Adjusted down", tone: "danger", direction: -1 },
  RESERVATION: { label: "Reserved", tone: "warning", direction: 0 },
  RESERVATION_RELEASE: { label: "Released", tone: "neutral", direction: 0 },
  TRANSFER_OUT: { label: "Transferred out", tone: "violet", direction: -1 },
  TRANSFER_IN: { label: "Transferred in", tone: "violet", direction: 1 },
  SALES_RETURN: { label: "Sales return", tone: "success", direction: 1 },
  PURCHASE_RETURN: { label: "Purchase return", tone: "danger", direction: -1 },
};
