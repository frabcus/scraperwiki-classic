from django import forms
from django.forms import widgets
from api.models import api_key

class applyForm(forms.ModelForm):
    
  class Meta:
    model = api_key
    fields = ('description',)
  
  # title = forms.CharField(widget=forms.TextInput(attrs={'title' : 'Untitled'}))
  # commit_message = forms.CharField(required=False, widget=forms.TextInput(attrs={'title' : ''}))
  # tags = forms.CharField(required=False)
  # code = forms.CharField(widget=widgets.Textarea({'cols':'80', 'rows':'10', 'style':'width:90%'}))
  

