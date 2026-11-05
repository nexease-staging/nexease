# NexEase GST documents: launch checklist

- **Sales → Delivery Challans** is the digital goods movement challan (not a traffic challan or a payment challan). It produces a PDF and does not require Sandbox. It does not issue a tax invoice, post stock, or replace an e-way bill.
- **Sales → E-Invoices** is the existing Pro-only IRP workflow. See EINVOICE_DELIVERY_CHALLAN_UPDATE.md.
- **Sales → E-Way Bills** is Pro-only. It supports eligible outward goods documents: an unlinked delivery challan, a reviewed domestic B2B goods invoice confirmed not to need IRN, or combined IRN and e-way bill generation for an eligible goods invoice. It does not decide whether the statutory requirement applies.

## Setup and acceptance

1. Confirm your Sandbox subscription enables both live e-invoice and e-way bill endpoints. Keep platform keys and EINVOICE_ENCRYPTION_KEY in the backend environment. Do not commit them. The default API version for e-way bills is 1.0.0 and can be set with EWAY_SANDBOX_API_VERSION.
2. Register Quicko as GSP on the relevant government portal for each seller GSTIN. Under Sales → E-Invoices, save the seller credentials and registered address. Sandbox documents that e-invoice API user credentials can also be used for its e-way bill authentication; confirm that your specific account has access to both.
3. Start with test keys and a separate test database. Confirm that a challan PDF prints, an eligible test invoice gets an IRN, and both combined and standalone test generation return a real response from Sandbox's test API. Test a rejected submission and recovery. Never use test results for real dispatch.
4. In live mode, have an authorized user review the first genuine transaction before submitting. Cross-check the number and validity against the portal. Verify the signed QR on the registered invoice PDF before sending it to the customer.
5. If a request outcome is uncertain, verify the original document in the portal first. The app blocks repeat submissions. For an already registered IRN needing a separate e-way bill, amendments, cancellation, extensions, or split dispatch, use the applicable government portal. Record a checked number or cancellation in NexEase; these are user-attested records, not API-verified status.

Provider reference: https://sandbox-docs.readme.io/reference/generate-e-way-bill-api
Government portal: https://ewaybillgst.gov.in/
