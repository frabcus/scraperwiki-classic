'''
This is the function that the cronjob should call
for sending vault exception alerts.

:: Testing

Create a database with a bunch of the data.
Or maybe just include this test in the updater script.

'''
#!python

from django.core.management import setup_environ
import settings
setup_environ(settings)

from codewiki.models.vault import Vault
from alerts.views import alert_vault_members_of_exceptions

def main():
    for vault in Vault.objects.all():
        alert_vault_members_of_exceptions(vault)

if __name__ == '__main__':
    main()
