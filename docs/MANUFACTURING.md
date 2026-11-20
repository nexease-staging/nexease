# Manufacturing in NexEase

## Enable the module

Install the backend and frontend from the same commit. Use the application's normal MongoDB replica set or transaction-capable sharded cluster. Run the following commands against the target application database before the first order.

    python manage.py ensure_manufacturing_indexes
    python manage.py seed_permissions

Assign manufacturing.read to viewers. Production operators also need manufacturing.manage and inventory.adjust. Grant the usual inventory lookup permissions, sales_orders.read to link orders, and invoices.read to view billed amounts. Initialize the organization's normal chart of accounts. Production adds accounts 1201 (work in progress) and 5091 (expenses absorbed) on first use. Review those codes against the organization's chart. Production absorption assumes the underlying expenses are recorded through normal accounting.

## Use a manufacturing order

1. Open Inventory → Manufacturing. Choose the warehouse, due date, and optional sales order. Add each finished item, its quantity, custom specifications and dimensions, material quantities per finished unit, and estimated expenses. Repeat an existing plan for another standard job.
2. Open the order to check warehouse availability. Choose the finished line and enter a batch reference. Allocate materials if reservations are needed. Issue actual quantities and return unused materials before posting the batch. Each material uses its inventory unit.
3. Post accepted and rejected quantities plus actual labour, machine, consumables and other expense amounts. Only accepted units enter finished stock. Rejected quantities and extra material consumed contribute to batch cost. Use another batch reference for a later partial completion.
4. Close after recording production on each output and settling open batches. Compare planned and actual costs, review batch history and export material, batch or cost reports. Date filters use the planned due date.
5. Fulfil linked sales orders in Sales using the established delivery, invoice and payment workflows. The order shows linked billing and collections. Revenue less job cost compares net billed lines before tax with the entire job cost. If two jobs share the same sales order and product, individual revenue allocation requires a business allocation rule and the figure is omitted.

## Database and APIs

The additive index command prepares manufacturing_orders and manufacturing_events along with existing inventory indexes. Order history records actor, request, revision and time. Production uses existing products, warehouses, inventory, stock movements, chart of accounts and journals. Issue debits WIP and credits inventory. Return reverses that posting. Completion absorbs entered expenses, clears the batch's WIP and updates accepted stock at a blended cost. A wholly rejected batch charges its cost to the existing cost-of-goods-sold account.

GET and POST /api/v1/business/manufacturing/ list, report or create orders. GET and POST /api/v1/business/manufacturing/<order_id>/ read a job or submit an action. Actions include edit, allocate, release, issue, return, produce and close. Every mutation requires a UUID request_key. An existing order also requires its current revision. Retry an uncertain request with the original key and payload.

## Release boundaries

The existing sales system permits partial dispatches and payments and one invoice per fulfilled sales order. This release does not introduce multi-invoice billing against one sales order, a new dispatch-time manufacturing COGS posting, or batch selection at sales dispatch. Manufacturing batch history traces materials and receipts to the job. Mixed units use each product's existing stock unit and require quantities in that unit. The native mobile inventory update is separate from the responsive manufacturing web page.

## Acceptance check before client deployment

On staging, use a test organization with the same permissions and chart as production. Create raw steel and a finished bracket, receive 10 kg at ₹100/kg, and plan 2 brackets at 2 kg each. Issue 5 kg, return 1 kg, post 2 accepted brackets and ₹100 labour. With no prior finished stock, expect 6 kg steel remaining, 2 brackets added, ₹500 actual cost, ₹250 per bracket and zero batch WIP. Repeat the submission with the same request key and verify both balances are unchanged. Confirm inventory movements, journal lines and sales fulfilment in the owner's normal screens.
