from django.contrib.auth.models import User
from django.conf import settings
import helper
from froth.views import check_key

def setUp():    
    global user, profile
    user = User.objects.create_user('dcameron', 'dcameron@scraperwiki.com', 'bagger288')
    profile = user.get_profile()

def ensure_staff_key_returns_valid_response():
    assert response.status_code == 200

def ensure_premium_account_holder_key_returns_valid_response():
    for plan in ('individual', 'business', 'corporate'):
        profile.plan = plan
        assert response.status_code == 200

def ensure_invalid_key_returns_invalid_response():
    assert response.status_code == 403 # Forbidden

def it_should_present_documentation_on_invalid_query():
    assert response.status_code == 400 # BadRequest

def ensure_peasant_key_returns_invalid_response():
    """Users who are not staff and not holders of premium accounts
    should not have valid API keys."""
    assert response.status_code == 402 # PaymentRequired
