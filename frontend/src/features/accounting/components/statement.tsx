"use client";

import {useState} from "react";
import {useAccountingDashboard} from "@/features/accounting/hooks";

const currency = new Intl.NumberFormat("en-IN", {style: "currency", currency: "INR"});
const labels = {
  profitability: {
    revenue: "Revenue", cost_of_goods_sold: "Cost of goods sold", gross_profit: "Gross profit",
    operating_expenses: "Operating expenses", net_profit: "Net profit",
  },
  balance_sheet: {
    assets: "Total assets", liabilities: "Total liabilities", equity: "Total equity",
    current_earnings: "Current earnings", difference: "Balance difference",
  },
};

export default function Statement({kind}: {kind: keyof typeof labels}) {
  const [date, setDate] = useState("");
  const report = useAccountingDashboard({as_of_date: date || undefined});
  const values = report.data?.[kind];
  return <main className="nx-panel space-y-4">
    <h1 className="text-2xl font-semibold">{kind === "profitability" ? "Profit & loss" : "Balance sheet"}</h1>
    <label>{kind === "profitability" ? "Cumulative through" : "As of"}
      <input className="nx-input max-w-xs" type="date" value={date} onChange={event => setDate(event.target.value)}/>
    </label>
    {report.isLoading && <p>Loading statement…</p>}
    {report.error && <p role="alert">{report.error.message}</p>}
    {values && <dl>{Object.entries(labels[kind]).map(([key, label]) =>
      <div key={key} className="flex justify-between gap-3 border-b py-3">
        <dt>{label}</dt><dd className="font-semibold">{values[key] == null ? "—" : currency.format(Number(values[key]))}</dd>
      </div>
    )}</dl>}
  </main>;
}
