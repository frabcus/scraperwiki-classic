import django.forms
from django.forms import ModelForm, ChoiceField
from frontend.models import UserProfile
from contact_form.forms import ContactForm

#from django.forms.extras.widgets import Textarea


class UserProfileForm (ModelForm):
    alert_frequency = ChoiceField(choices = ((0, 'Instant'), (3600, 'Once an hour')))
    class Meta:
        model = UserProfile
        fields = ('bio', 'alert_frequency')
        

class scraperContactForm(ContactForm):
  subject_dropdown = django.forms.ChoiceField(label="Subject", choices=(('a', 'a'),('b', 'a'),))
    