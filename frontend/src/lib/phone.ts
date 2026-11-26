/** wa.me needs digits with country code; bare 10-digit Indian numbers get 91. */
export function whatsappNumber(phone: string | null | undefined): string | null {
  const digits = (phone ?? "").replace(/\D/g, "").replace(/^0+/, "");
  if (digits.length === 10) return "91" + digits;
  return digits.length >= 11 && digits.length <= 15 ? digits : null;
}
