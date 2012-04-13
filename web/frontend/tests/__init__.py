from django.core.management import call_command 

from frontend.tests.test_views import *
from frontend.tests.test_messages import *

call_command('flush', interactive=False)
call_command('loaddata', 'test-fixture.yaml')
