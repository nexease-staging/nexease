from django.core.management.base import BaseCommand
from django.core.management import call_command
from mongoengine.connection import get_db

class Command(BaseCommand):
    help='Seed NexEase permissions and replace the legacy sales-order invoice index with a partial unique index.'
    def handle(self,*args,**kwargs):
        db=get_db();collection=db['invoices']
        # Only the obsolete index with this exact key pattern is replaced.
        for name,spec in collection.index_information().items():
            if spec.get('key')==[('organization',1),('sales_order',1)] and not spec.get('partialFilterExpression'):
                collection.drop_index(name)
        collection.create_index([('organization',1),('sales_order',1)],name='invoice_sales_order_unique_present',unique=True,partialFilterExpression={'sales_order':{'$type':'objectId'}})
        call_command('seed_permissions')
        from apps.organizations.models import Organization
        for organization in Organization.objects(is_active=True):
            call_command('seed_roles', organization=str(organization.id))
        self.stdout.write(self.style.SUCCESS('NexEase indexes and role catalog updated. Review custom role permissions.'))
