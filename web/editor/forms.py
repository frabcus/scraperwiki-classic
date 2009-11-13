from django import forms
from django.forms import widgets
import scraper

class editorForm(forms.ModelForm):
    
  class Meta:
    model = scraper.models.Scraper
    fields = ('title', 'code', 'description', 'source', 'license', 'tags')
  
  title = forms.CharField(widget=forms.TextInput(attrs={'title' : 'Untitled Scraper'}))
  commit_message = forms.CharField(required=False, widget=forms.TextInput(attrs={'title' : ''}))
  tags = forms.CharField(required=False)
  code = forms.CharField(widget=widgets.Textarea({'cols':'80', 'rows':'10', 'style':'width:90%'}))
  

