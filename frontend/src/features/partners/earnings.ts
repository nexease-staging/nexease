/** Partner commission maths, kept in one place so the portal and the proposal deck agree. */
export const PLANS = [
  { code: "basic", name: "NexEase", monthly: 199, annual: 1999 },
  { code: "plus", name: "NexEase Plus", monthly: 349, annual: 3499 },
  { code: "pro", name: "NexEase Pro", monthly: 599, annual: 5999 },
] as const;
export const FIRST_RATE = 0.2;
export const RENEWAL_RATE = 0.1;
/** Plan prices include 18% GST; commission is paid on the amount excluding GST. */
export const GST = 1.18;

export type Billing = "monthly" | "annual";

/** Commission for one client in its first year and in each later year, in rupees. */
export function perClient(price: number, billing: Billing) {
  const base = price / GST;
  return billing === "monthly"
    ? { firstYear: base * (FIRST_RATE + 11 * RENEWAL_RATE), laterYear: base * 12 * RENEWAL_RATE, firstPayment: base * FIRST_RATE }
    : { firstYear: base * FIRST_RATE, laterYear: base * RENEWAL_RATE, firstPayment: base * FIRST_RATE };
}

export function estimate(clients: number, planCode: string, billing: Billing) {
  const plan = PLANS.find((p) => p.code === planCode) ?? PLANS[1];
  const one = perClient(billing === "monthly" ? plan.monthly : plan.annual, billing);
  return { plan, firstYear: one.firstYear * clients, laterYear: one.laterYear * clients, firstPayment: one.firstPayment };
}

export const rupees = (n: number) => "₹" + Math.round(n).toLocaleString("en-IN");
