from django.conf import settings
from django import forms
from frontend.models import UserProfile, AlertTypes, DataEnquiry
from contact_form.forms import ContactForm
from registration.forms import RegistrationForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from captcha.fields import CaptchaField
from codewiki.models import SCHEDULE_OPTIONS, Scraper, Code


#from django.forms.extras.widgets import Textarea
class SearchForm(forms.Form):
    q = forms.CharField(label='Find datasets', max_length=50)
    
    
def get_emailer_for_user(user):
    try:
        queryset = Scraper.objects.exclude(privacy_status="deleted")
        queryset = queryset.filter(Q(usercoderole__role='owner') & Q(usercoderole__user=user))
        queryset = queryset.filter(Q(usercoderole__role='email') & Q(usercoderole__user=user))
        return queryset.latest('id')
    except:
        return None

    
class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        self.user = self.instance.user
        self.emailer = get_emailer_for_user(self.user)

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
        if email != self.user.email and User.objects.filter(email__iexact=email).count > 0:
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
        
    subject_dropdown = forms.ChoiceField(label="Subject type", choices=(('suggestion', 'Suggestion about how we can improve something'),('request', 'Request data'),('help', 'Help using ScraperWiki'), ('bug', 'Report a bug'), ('other', 'Other')))
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

class DataEnquiryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DataEnquiryForm, self).__init__(*args, **kwargs)
        self.fields['frequency'].initial = 'daily'

    urls = forms.CharField(required=False, label='At which URL(s) can we find the data currently?')
    columns = forms.CharField(required=False, label='What information do you want scraped?')
    due_date = forms.DateField(required=False, label='When do you need it by?')
    first_name = forms.CharField(label='First name:')
    last_name = forms.CharField(label='Last name:')
    email = forms.CharField(label='Your email address:')
    telephone = forms.CharField(required=False, label='Your telephone number:')
    company_name = forms.CharField(required=False, label='Your company name:')
    broadcast = forms.BooleanField(required=False, label='I\'m happy for this request to be posted on Twitter/Facebook')
    description = forms.CharField(required=False, widget=forms.Textarea, label='What are your ETL needs?')
    visualisation = forms.CharField(required=False, widget=forms.Textarea, label='What visualisation do you need?')
    application = forms.CharField(required=False, widget=forms.Textarea, label='What application do you want built?')
    frequency = forms.ChoiceField(label='How often does the data need to be scraped?', choices=DataEnquiry.FREQUENCY_CHOICES)

    class Meta:
        model = DataEnquiry
