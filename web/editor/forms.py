import django.forms
from django.forms import widgets
import scraper

class editorForm(django.forms.ModelForm):
    
  class Meta:
    model = scraper.models.Scraper
    fields = ('code',)
  
  
  code = django.forms.CharField(widget=widgets.Textarea({'cols':'80', 'rows':'10', 'style':'width:90%'}))

