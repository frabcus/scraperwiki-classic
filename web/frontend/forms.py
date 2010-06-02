from django.conf import settings
from django import forms
from frontend.models import UserProfile, AlertTypes
from contact_form.forms import ContactForm
from registration.forms import RegistrationForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


#from django.forms.extras.widgets import Textarea

class UserProfileForm (forms.ModelForm):
    alert_frequency = forms.ChoiceField(required=False, label="How often do you want to be emailed?", choices = (
                                (-1, 'Never'), 
                                (3600*24, 'Once a day'),
                                (3600*24*3, 'Every couple of days'),                                
                                (3600*24*7, 'Once a week'),
                                (3600*24*7*2, 'Every two weeks'),))

    options = []
    for item in AlertTypes.objects.all():
        options.append((item.pk, item.label))

    alert_types = forms.MultipleChoiceField(options, widget=forms.CheckboxSelectMultiple())
    bio = forms.CharField(label="A bit about you", widget=forms.Textarea(), required=False)
    
    class Meta:
        model = UserProfile
        fields = ('bio', 'name', 'alert_frequency', 'alert_types')

class scraperContactForm(ContactForm):
  subject_dropdown = forms.ChoiceField(label="Subject type", choices=(('suggestion', 'Suggestion about how we can improve something'),('request', 'Request a private scraper'),('help', 'Help using ScraperWiki'), ('bug', 'Report a bug'), ('other', 'Other')))
  title = forms.CharField(widget=forms.TextInput(), label=u'Subject')
  recipient_list = [settings.FEEDBACK_EMAIL]


class SigninForm (AuthenticationForm):
    user_or_email = forms.CharField(label=_(u'Username or email'))
    remember_me = forms.BooleanField(widget=forms.CheckboxInput(),
                           label=_(u'Remember me'))


class CreateAccountForm(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which adds a required checkbox
    for agreeing to a site's Terms of Service and makes sure the email address is unique.

    """
    name = forms.CharField()
    tos = forms.BooleanField(widget=forms.CheckboxInput(),
                           label=_(u'I agree to the ScraperWiki terms and conditions'),
                           error_messages={ 'required': _("You must agree to the ScraperWiki terms and conditions") })
    data_protection = forms.BooleanField(widget=forms.CheckboxInput(),
                        label= u'I will not breach anyone\'s copyright or privacy, or breach any laws including the Data Protection Act 1998',
                        error_messages={ 'required': "You must agree to abide by the Data Protection Act 1998" })

    def clean_email(self):
       """
       Validate that the supplied email address is unique for the
       site.

       """
       if User.objects.filter(email__iexact=self.cleaned_data['email']):
           raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
       return self.cleaned_data['email']
