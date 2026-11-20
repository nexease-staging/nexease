from django.core.management.base import BaseCommand
from mongoengine.connection import get_db
from apps.inventory.models import Inventory, StockMovement


class Command(BaseCommand):
    help = "Create additive production-order, history and inventory indexes."

    def handle(self, *args, **options):
        db = get_db()
        Inventory.ensure_indexes()
        StockMovement.ensure_indexes()
        db.manufacturing_orders.create_index(
            [("organization", 1), ("number", 1)], unique=True
        )
        db.manufacturing_orders.create_index(
            [("organization", 1), ("status", 1), ("due", 1)]
        )
        db.manufacturing_orders.create_index([("organization", 1), ("sales_order", 1)])
        db.manufacturing_events.create_index(
            [("organization", 1), ("order", 1), ("revision", 1)], unique=True
        )
        self.stdout.write("Manufacturing indexes ready.")
