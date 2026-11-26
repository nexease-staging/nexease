"""Keep `updated_at` current on every save of the records Tally sync sends, so the NexEase → Tally
outbox sees each change (some older code paths save without touching it)."""
from datetime import datetime

from mongoengine import signals

TRACKED = {"Customer", "Supplier", "Product", "Invoice", "VendorBill", "CustomerPayment", "SupplierPayment", "CreditNote", "VendorDebitNote",
           "SalesOrder", "PurchaseOrder", "JournalEntry", "BusinessRecord"}


def touch(sender, document, **kwargs):
    if type(document).__name__ in TRACKED and "updated_at" in getattr(document, "_fields", {}):
        document.updated_at = datetime.utcnow()


signals.pre_save.connect(touch, weak=False)
