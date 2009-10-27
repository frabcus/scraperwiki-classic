import django.forms
from django.conf import settings
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
  subject_dropdown = django.forms.ChoiceField(label="Subject type", choices=(('suggestion', 'Suggestion about how we can improve something'),('help', 'Help using ScraperWiki'), ('bug', 'A bug or error')))
  title = django.forms.CharField(widget=django.forms.TextInput(), label=u'Subject')
  recipient_list = ["julian@goatchurch.org.uk"] # temporary save because this isn't set [settings.FEEDBACK_EMAIL]