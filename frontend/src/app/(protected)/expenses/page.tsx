import BusinessWorkspace from "@/features/business/workspace";

export default function Page() {
  return (
    <BusinessWorkspace
      kinds={["expenses"]}
      title="Daily expenses"
      description="Utilities, travel, fuel, rent and everyday spending. Saving posts the expense to your books. Amounts include tax; use vendor bills when you can claim input tax, and never enter the same spend in both."
    />
  );
}
