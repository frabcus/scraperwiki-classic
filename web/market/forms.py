from django import forms
from django.forms import ModelForm, ChoiceField
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User

from market.models import Solicitation
from scraper.models import Scraper

class SolicitationForm (ModelForm):

    title = forms.CharField(max_length=150, label = "Title*")
    details = forms.CharField(widget=forms.Textarea, label = "Details*")
    link = forms.URLField(label = "Link*")
    price = forms.ChoiceField(label="Bounty", choices=((50, mark_safe('&pound;50')),(100, mark_safe('&pound;100')), (250, mark_safe('&pound;250')), (500, mark_safe('&pound;500')), (1000, mark_safe('&pound;1000')), (0, 'Just a suggestion, no bounty')))

    class Meta:
        model = Solicitation
        fields = ('title', 'link', 'details', 'price')

class SolicitationClaimForm (ModelForm):

    def __init__(self, *args, **kwargs):
         user = User.objects.get(id=kwargs.pop('user_id'))
         queryset = user.scraper_set.filter(userscraperrole__role='owner', deleted=False).order_by('-created_at')
         super(SolicitationClaimForm, self).__init__(*args, **kwargs)
         self.fields['scraper'] = forms.ModelChoiceField(
                 required=True,
                 queryset=queryset,)

         self.fields['confirmed'] = forms.BooleanField(widget=forms.CheckboxInput(),
                               required=True, 
                               label=u'I have written and tested this scraper',
                               error_messages={ 'required': "Please confirm that you have written and tested this scraper" })                 

