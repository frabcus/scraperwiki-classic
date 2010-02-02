from django import forms
from django.forms import widgets
import scraper

LICENSE_CHOICES = ( 
    ('Public domain', 'Public domain'),
    ('Share-alike', 'Share-alike'),
    ('Crown copyright', 'Crown copyright'),
    ('Other', 'Other'),
    ('Unknown', 'Unknown'),
)

# RUN_INTERVAL_CHOICES = (
#     ('once', 'Once a day'),
#     ('never', 'Never'),
#     )

class editorForm(forms.ModelForm):
    
  class Meta:
    model = scraper.models.Scraper
    fields = ('title', 'code', 'description', 'license', 'tags',)
  
  title = forms.CharField(
    widget=forms.TextInput(attrs={'title' : 'Untitled Scraper'})
  )
  commit_message = forms.CharField(
    required=False, 
    widget=forms.TextInput(attrs={'title' : ''})
    )
  description = forms.CharField(
    required=False, 
    widget=forms.TextInput(attrs={'title' : ''})
    )

  # run_interval = forms.ChoiceField(
  #   label="Run once a day", 
  #   choices=RUN_INTERVAL_CHOICES,
  #   )
    
  tags = forms.CharField(required=False)
  license = forms.ChoiceField(choices=LICENSE_CHOICES, label='Data licence')
  code = forms.CharField(
    widget=widgets.Textarea({'cols':'80', 'rows':'10', 'style':'width:90%'})
    )
  

