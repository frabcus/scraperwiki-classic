from django import forms
from django.forms import widgets
from models import Scraper, Code, code, View
from models.scraper import SCHEDULE_OPTIONS

LICENSE_CHOICES = ( 
    ('Public domain', 'Public domain'),
    ('Share-alike', 'Share-alike'),
    ('Crown copyright', 'Crown copyright'),
    ('Other', 'Other'),
    ('Unknown', 'Unknown'),
)

class CodeTagForm (forms.Form):
    tags = forms.CharField(required=False, label="Add new tags (comma separated)")

class ScraperAdministrationForm (forms.ModelForm):
    run_interval = forms.ChoiceField(required=True, label="Re-run this scraper", choices = SCHEDULE_OPTIONS)
    title = forms.CharField(label="Title")
    license = forms.ChoiceField(choices=LICENSE_CHOICES, label='Data licence')
    license_link = forms.URLField(label="License link")
    tags = forms.CharField(required=False, label="Tags (comma separated)")

    class Meta:
        model = Scraper
        fields = ('run_interval', 'title', 'description', 'license', 'published', 'featured')

class ViewAdministrationForm (forms.ModelForm):
    title = forms.CharField(label="Title")
    tags = forms.CharField(required=False, label="Tags (comma separated)")

    class Meta:
        model = View
        fields = ('title', 'description', 'published', 'featured')

