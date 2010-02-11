import django.forms
from django.conf import settings
from django.forms import ModelForm, ChoiceField
from frontend.models import UserProfile
from contact_form.forms import ContactForm
from registration.forms import RegistrationForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


#from django.forms.extras.widgets import Textarea

class UserProfileForm (ModelForm):

    alert_frequency = ChoiceField(required=False, choices = ((0, 'Instant'), (3600, 'Once an hour')))

    class Meta:
        model = UserProfile
        fields = ('bio',)

class scraperContactForm(ContactForm):
  subject_dropdown = django.forms.ChoiceField(label="Subject type", choices=(('suggestion', 'Suggestion about how we can improve something'),('request', 'Request a private scraper'),('help', 'Help using ScraperWiki'), ('bug', 'Report a bug'), ('other', 'Other')))
  title = django.forms.CharField(widget=django.forms.TextInput(), label=u'Subject')
  recipient_list = [settings.FEEDBACK_EMAIL]

class SigninForm (AuthenticationForm):
    remember_me = django.forms.BooleanField(widget=django.forms.CheckboxInput(),
                           label=_(u'Remember me'))


class CreateAccountForm(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which adds a required checkbox
    for agreeing to a site's Terms of Service and makes sure the email address is unique.

    """
    tos = django.forms.BooleanField(widget=django.forms.CheckboxInput(),
                           label=_(u'I agree to the ScraperWiki terms and conditions'),
                           error_messages={ 'required': _("You must agree to the ScraperWiki terms and conditions") })
    data_protection = django.forms.BooleanField(widget=django.forms.CheckboxInput(),
                        label= u'I will not breach anyone\'s copyright or privacy, or breach any laws including the Data Protection Act 1998',
                        error_messages={ 'required': "You must agree to abide by the Data Protection Act 1998" })

    def clean_email(self):
       """
       Validate that the supplied email address is unique for the
       site.

       """
       if User.objects.filter(email__iexact=self.cleaned_data['email']):
           raise django.forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
       return self.cleaned_data['email']