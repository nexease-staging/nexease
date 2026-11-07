# NexEase Quick Billing

Open **Sales → Invoices → Quick invoice**. Choose a saved customer, add items by name or barcode, and review dates and GST. Customer contact fields and extra invoice fields are available when needed. A typed customer or product can be created when saving if your role has permission.

The footer shows the estimated total, including entered discounts and GST. Save a draft and open it to review and issue. Use **From sales order** when billing against a fulfilled sales order. Direct invoices do not dispatch inventory.

On the web, **Download PDF** saves the file, and **WhatsApp message** prepares text for an issued invoice. Attach the downloaded PDF in WhatsApp if needed. In the APK, **Share PDF** opens the Android share sheet, where WhatsApp can be selected if installed. The **Email** action still uses the existing email delivery setup.

This release uses the existing backend APIs. Deploy the frontend update and rebuild the APK to receive the new screens. It does not introduce quotation or pro forma workflows, inventory batch or serial tracking, or new GST integrations.
