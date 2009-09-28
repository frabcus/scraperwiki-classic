from django.forms import ModelForm
from frontend.models import UserProfile
import datetime
#from django.forms.extras.widgets import Textarea


class UserProfileForm (ModelForm):
  class Meta:
    model = UserProfile
  