from django.conf import settings
from django import forms
from frontend.models import UserProfile, AlertTypes
from contact_form.forms import ContactForm
from registration.forms import RegistrationForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from captcha.fields import CaptchaField
from codewiki.models import SCHEDULE_OPTIONS, Scraper


#from django.forms.extras.widgets import Textarea
class SearchForm(forms.Form):
    q = forms.CharField(label='Find datasets', max_length=50)
    
class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        self.user = self.instance.user
        self.emailer = Scraper.objects.get_emailer_for_user(self.user)

        if self.emailer:
            self.fields['alert_frequency'].initial = self.emailer.run_interval
        else:
            # Fallback on frequency in profile while not all users have an emailer
            self.fields['alert_frequency'].initial = self.instance.alert_frequency

        self.fields['email'].initial = self.user.email

    alert_frequency = forms.ChoiceField(required=False, 
                                        label="How often do you want to be emailed?", 
                                        choices = SCHEDULE_OPTIONS)
    bio = forms.CharField(label="A bit about you", widget=forms.Textarea(), required=False)
    email = forms.EmailField(label="Email Address")
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).count > 0:
            raise forms.ValidationError("This email address is already used by another account.")

        return email

    class Meta:
        model = UserProfile
        fields = ('bio', 'name')

    def save(self, *args, **kwargs):
        self.user.email = self.cleaned_data['email']
        self.user.save()

        if self.emailer:
            self.emailer.run_interval = self.cleaned_data['alert_frequency']
            self.emailer.save()

        return super(UserProfileForm, self).save(*args,**kwargs)

class scraperContactForm(ContactForm):
    def __init__(self, data=None, files=None, request=None, *args, **kwargs):
        super(scraperContactForm, self).__init__(data=data, files=files, request=request, *args, **kwargs)
        if not request.user.is_authenticated():
            self.fields['captcha'] = CaptchaField()
        
    subject_dropdown = forms.ChoiceField(label="Subject type", choices=(('suggestion', 'Suggestion about how we can improve something'),('request', 'Request a private scraper'),('help', 'Help using ScraperWiki'), ('bug', 'Report a bug'), ('other', 'Other')))
    title = forms.CharField(widget=forms.TextInput(), label=u'Subject')
    recipient_list = [settings.FEEDBACK_EMAIL]

    def from_email(self):
        return self.cleaned_data['email']


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

    def clean_email(self):
       """
       Validate that the supplied email address is unique for the
       site.

       """
       if User.objects.filter(email__iexact=self.cleaned_data['email']):
           raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
       return self.cleaned_data['email']

class ResendActivationEmailForm(forms.Form):
    email_address = forms.EmailField()
