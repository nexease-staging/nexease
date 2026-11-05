# NexEase Sales documents and pricing

## Prices

| Plan | Monthly | Annual |
| --- | ---: | ---: |
| NexEase | ₹749 | ₹7,499 |
| NexEase Plus | ₹999 | ₹9,999 |
| NexEase Pro | ₹1,299 | ₹12,999 |

GST compliance service: ₹499 per month. Monthly bundles that include GST
reflect the ₹500 reduction and retain their previous rupee discount. Website
and downloadable price list use the new prices.

Annual checkout uses a separate Razorpay plan. If payments are already
configured, publish annual checkout for each plan from /owner, then verify
in Razorpay Test mode before publishing in Live. Existing monthly contracts
are unchanged; annual customers retain monthly usage limits. A live payment
or plan publication was not performed as part of this update.

## Sandbox e-invoicing

1. Confirm with Sandbox that your account can use the live e-invoice endpoints,
   what they cost, and whether multi-tenant usage is enabled. A working GSTIN
   lookup alone does not verify this.
2. On the Django backend set EINVOICE_ENCRYPTION_KEY to a new persistent
   Fernet key. Generate one privately with
   `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   and store it in Render, not in Git. Keep the key backed up securely.
   E-invoice uses the existing GST_SANDBOX_API_KEY, GST_SANDBOX_API_SECRET
   and GST_SANDBOX_ENV. If needed, use a separate staging deployment with
   test credentials and database. EINVOICE_SANDBOX_API_VERSION defaults to 1.0.0.
3. With an active Pro workspace, configure the regular seller GSTIN and
   legal name in Taxation. Create dedicated API credentials for the seller
   GSTIN at the IRP, choosing Quicko Infosoft Pvt. Ltd. as GSP.
4. Under Sales → E-Invoices → Connect IRP, enter the API username/password and
   registered address, city and PIN. Each workspace connects its own seller.
5. Use an issued, reviewed domestic B2B tax invoice. Verify the buyer GSTIN,
   legal name, city, address, PIN, place of supply, HSN/SAC, goods unit codes
   and invoice totals. From Sales → E-Invoices, review and confirm Generate IRN.
   On live registration, the invoice PDF includes IRN, acknowledgment and
   the signed QR. Test IRNs are marked as test and do not print a live QR.
6. If a request was sent but the response could not be verified, use Recover
   IRN promptly. Sandbox limits recovery by document to recent registrations.
   Do not create another invoice or submit a replacement while the outcome
   is uncertain. If recovery fails, verify the original document at the IRP
   and contact support with the provider transaction reference.
7. IRP cancellation and local invoice cancellation are separate. Resolve
   the IRP first, then use the existing NexEase invoice correction workflow.
   IRP cancellation is subject to the provider's time limit.

This e-invoice workflow covers domestic B2B tax invoices. See GST_DOCUMENTS_GO_LIVE.md for e-way bills. It does not submit
credit/debit notes, exports, SEZ supplies or GST returns.

## Delivery challans

Sales → Delivery Challans is available with normal Sales access. Choose an
existing customer and goods from the product master. Enter dispatch date,
reason, place of supply, quantities, taxable value and GST where applicable.
Optionally link a sales invoice for the same customer. The PDF includes
consignor and consignee details, goods and taxes, space for signature, and
labelled consignee, transporter and consignor copies. Issuance records a
movement document only; inventory, accounting and e-way bills are separate.
