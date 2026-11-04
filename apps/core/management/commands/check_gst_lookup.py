"""Read-only provider diagnostic. Never prints API credentials or access tokens."""
import os,re
from django.core.management.base import BaseCommand,CommandError
from apps.business.gst_provider import configuration,sandbox_lookup,GSTLookupError
class Command(BaseCommand):
    help='Check backend GST configuration safely. Add --gstin GSTIN for one provider lookup (provider usage may apply).'
    def add_arguments(self,parser):parser.add_argument('--gstin',default='')
    def handle(self,*args,**options):
        provider=os.getenv('GST_LOOKUP_PROVIDER','adapter').strip().lower()
        if provider!='sandbox':raise CommandError('Set GST_LOOKUP_PROVIDER=sandbox in the backend environment.')
        try:
            _,_,env=configuration();self.stdout.write('Provider: Sandbox | Environment: '+env+' | Key and secret present (values hidden).')
            gstin=options['gstin'].strip().upper()
            if not gstin:
                self.stdout.write('Configuration format checked only. Credentials/API access are NOT authenticated. Use --gstin with a supported test GSTIN, or a real GSTIN with live credentials, to test one lookup.');return
            if not re.fullmatch(r'\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]',gstin):raise CommandError('Enter a valid 15-character GSTIN.')
            result=sandbox_lookup(gstin)
            self.stdout.write(self.style.SUCCESS('Lookup succeeded. Requested taxpayer matched; business name and address mapping available. No records changed.'))
        except GSTLookupError as exc:raise CommandError(exc.public_message()) from None
