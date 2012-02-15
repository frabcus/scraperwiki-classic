from lettuce import before
from django.conf import settings
from django.core.management import call_command 
from south.management.commands import patch_for_test_db_setup

@before.harvest
def sync_db(variables):
    patch_for_test_db_setup() 
    call_command('syncdb', interactive=False)
