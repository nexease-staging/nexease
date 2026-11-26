# NexEase Tally Connector

Keeps TallyPrime and NexEase in sync, both ways, every 30 seconds.

## Set up (once, on the computer where Tally runs)

1. **Turn on Tally's connection port.** In TallyPrime: `F1 Help → Settings → Connectivity → Client/Server configuration`
   (older versions: `Gateway of Tally → F12 → Advanced Configuration`). Set **TallyPrime acts as** = *Both*,
   **Enable ODBC** = *Yes*, **Port** = *9000*. Restart Tally and open your company.
2. **Download** `NexEase-Tally-Connector.exe` from NexEase → Tally → Connect (or the GitHub release `tally-connector`).
3. **Open it**, enter the pairing code shown in NexEase → Tally → Connect, and press *Connect*.
4. Tick **Start with Windows** so sync keeps running in the background.

Keep Tally open with the company loaded; the connector syncs whenever both are running and catches up after a break.

## What syncs

| Direction | What |
| --- | --- |
| Tally → NexEase | Companies, groups, ledgers (with balances, GSTIN, contacts), stock groups/items/units/godowns, cost centres, voucher types and every voucher. Sundry debtors → customers, sundry creditors → suppliers, stock items → products. Deletions in Tally are detected. |
| NexEase → Tally | Customers, suppliers, products, sales invoices, purchase bills, receipts, payments, credit/debit notes, sales/purchase orders, expenses and manual journals. Edits update the same Tally voucher; cancellations cancel it. |

Choose the Tally ledgers for sales, purchases, GST, cash, bank and round-off in NexEase → Tally → Settings.

## Command line

```
NexEase-Tally-Connector.exe --headless           # no window (used by "Start with Windows")
python nexease_tally.py --pair ABCD-1234 --server https://…/api/v1
python nexease_tally.py --once                   # one sync round
```

Settings and the activity log live in `%APPDATA%\NexEase Tally\`.
