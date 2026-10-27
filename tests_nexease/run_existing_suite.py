"""Original regression suite against an isolated in-memory MongoDB mock.
Install requirements-test.txt. This never connects to a production database.
"""
import sys
sys.argv.append('test')
import bootstrap
from django.core.management import call_command
call_command('seed_permissions',verbosity=0)
call_command('test','apps',verbosity=1,interactive=False)
