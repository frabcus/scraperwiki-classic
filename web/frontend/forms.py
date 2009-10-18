from django.forms import ModelForm, ChoiceField
from frontend.models import UserProfile

#from django.forms.extras.widgets import Textarea


class UserProfileForm (ModelForm):
    alert_frequency = ChoiceField(choices = ((0, 'Instant'), (3600, 'Once an hour')))
    class Meta:
        model = UserProfile
        fields = ('bio', 'alert_frequency')
        
