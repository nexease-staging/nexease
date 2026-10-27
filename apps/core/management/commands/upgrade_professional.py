"""Add the new expense permissions to existing system Admin roles only."""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.authorization.models import Role,Permission
class Command(BaseCommand):
    help='Prepare Professional update permissions. Does not change financial transactions or custom roles.'
    def handle(self,*args,**kwargs):
        call_command('seed_permissions')
        permissions=list(Permission.objects(code__in=['expenses.read','expenses.manage'],is_active=True))
        count=0
        for role in Role.objects(is_system=True,name='Admin',is_active=True):
            role.update(add_to_set__permissions=permissions);count+=1
        self.stdout.write(self.style.SUCCESS(f'Updated {count} system Admin roles. Log out and back in. Review custom role access in Settings > Roles. Prepare system accounts in Settings > Business modules & books.'))
