from django import forms
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
        
class ChooseTemplateForm (forms.Form):
    language = forms.ChoiceField(required=True, label="Language", choices = code.LANGUAGES, widget=forms.RadioSelect, initial='Python')
    template = forms.ChoiceField(required=True, label="Template", choices = [], widget=forms.RadioSelect, initial='')    

    def __init__(self, wiki_type, *args, **kwargs):
        super(ChooseTemplateForm, self).__init__(*args, **kwargs)

        #get the relivent templates for this type of code object
        templates = [('', 'Blank ' + wiki_type)]
        template_objects = Code.objects.filter(deleted=False, published=True, isstartup=True, wiki_type=wiki_type)
        for template_object in template_objects:
            templates.append((template_object.short_name, template_object.title))

        #set the templates
        self.fields['template'].choices = templates