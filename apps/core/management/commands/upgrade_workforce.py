"""Additive upgrade: no financial documents or secrets are rewritten."""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.authorization.models import Permission,Role
from apps.products.models import Product
from apps.inventory.models import Inventory
class Command(BaseCommand):
    help='Prepare goods/services, dedicated Workforce and invoice formats.'
    def handle(self,*args,**options):
        call_command('seed_permissions')
        codes=['products.read_cost','payroll.read','payroll.manage','labour.read','labour.manage','taxation.read','taxation.manage','expenses.read','expenses.manage']
        permissions=list(Permission.objects(code__in=codes,is_active=True))
        count=0
        for role in Role.objects(name='Admin',is_system=True,is_active=True):
            role.update(add_to_set__permissions=permissions);count+=1
        converted=0
        for product in Product.objects(sku='LABOUR-SERVICE'):
            if product.item_type=='service':continue
            if Inventory.objects(organization=product.organization,product=product).first():
                self.stdout.write(self.style.WARNING('Skipped labour master with inventory history in organization '+str(product.organization.id)+'. Review before conversion.'));continue
            product.item_type='service';product.save();converted+=1
        self.stdout.write(self.style.SUCCESS(f'Updated {count} system Admin roles; converted {converted} labour service masters. Log out and back in. Configure invoice defaults, GST registration and reviewed HSN/SAC. Existing invoice classifications and journals are unchanged.'))
