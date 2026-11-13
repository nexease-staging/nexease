# Mobile screenshot review and sales-order discount

## Changes
- Sales-order line discounts have a rupees/percent selector using the same exact decimal conversion as invoices. Percentage is applied to quantity × unit price, rounded to paise, and sent as a rupee discount. Preview uses the same conversion. Negative, over-100% and over-line-value discounts cannot be submitted. Saved orders retain the rupee amount; reopening an order starts in rupee mode.
- Customer/product drawers get a bounded scrolling form and a separate visible heading. Their action row stays after the fields instead of floating over them. Bottom navigation and the AI launcher are hidden while a modal is open.
- Product Goods/Service and HSN fields stack on mobile; input widths respect their containers.
- Native drawer top clearance accounts for the status bar. The app shell no longer duplicates the header's top inset.
- Notifications stay within the viewport and their device-settings area is compact.
- Purchase quick-entry heading and button stack rather than squeezing the explanation into a narrow column.
- Goods-receipt and purchase-order headings use a compact single-row title/action layout on mobile.
- GST workpaper date fields use two equal-width columns and a full-width export action.
- E-invoice/document tables use the shared mobile cards with labelled fields and wrapping actions.

## Scope and validation limits
This addresses shared layout faults visible in the first nine screenshots. It is not an audit of every application screen. Existing product cards are retained. Goods-receipt and purchase-order cards still use their View details action. No real GST/IRP request was made.

Physical-device keyboard, accessibility font scaling, Android status-bar insets and final visual positioning must be checked in the rebuilt APK. No signed APK is produced by this bundle. The Android web export is checked separately from native packaging.

## Review on device
Open customer and product forms; confirm title/close are visible, all fields can be reached, and actions don't obscure fields. Open vendor-bill form and keyboard. Open notifications and scroll. Review purchase-order/goods-receipt headings, GST dates and e-invoice actions. On a sales order enter quantity 2, price 100, discount 10%; expected discount is 20.00. Switch to rupees: the entered 10 becomes a 10.00 discount. Check both save and edit flows.

## Checks completed
237 frontend tests (51 files), scoped ESLint, TypeScript, production web build and Android static web export passed. Native APK compilation and physical-device visual checks were not run.
