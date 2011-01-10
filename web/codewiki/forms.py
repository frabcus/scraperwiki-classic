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

    # this form seems like an obstruction as well - there's nothing in it
class editorForm(forms.ModelForm):

    class Meta:
        model = Code
        fields = ('title', 'code', 'wiki_type')
        
    title =     forms.CharField(widget=forms.TextInput(attrs={'title' : 'Untitled'}), label="Title*",)
    wiki_type = forms.ChoiceField(choices=code.WIKI_TYPES, widget=forms.HiddenInput())    
    code =      forms.CharField(widget=widgets.Textarea(attrs={'cols':'80', 'rows':'10', 'style':'width:90%'}))
    
    def clean_title(self):
        title = self.cleaned_data['title']
        if not title or title == '' or title.lower() == 'untitled':
            raise forms.ValidationError("Scraper needs a title")
        return title


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

