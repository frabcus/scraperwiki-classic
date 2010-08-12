from django import forms
from models import Scraper

LICENSE_CHOICES = ( 
    ('Public domain', 'Public domain'),
    ('Share-alike', 'Share-alike'),
    ('Crown copyright', 'Crown copyright'),
    ('Other', 'Other'),
    ('Unknown', 'Unknown'),
)

class SearchForm(forms.Form):
    q = forms.CharField(label='Find datasets', max_length=50)

class ScraperAdministrationForm (forms.ModelForm):
    run_interval = forms.ChoiceField(required=True, label="Re-run this scraper", choices = (
                                (-1, 'Never'),
                                (3600*24, 'Once a day'),
                                (3600*24*2, 'Every two days'),                                
                                (3600*24*3, 'Every three days'),                                                                
                                (3600*24*7, 'Once a week'),
                                (3600*24*14, 'Every two weeks'),
                                (3600*24*31, 'Once a month'),
                                (3600*24*63, 'Every two months'),
                                (3600*24*182, 'Every six months'),
                                ))
    title = forms.CharField(label="Title")
    license = forms.ChoiceField(choices=LICENSE_CHOICES, label='Data licence')
    
           # label should be this, but for html escaping: <small class="hint taghint">e.g. europe<em>,</em> grants<em>,</em> transport</small>
           # (there's some magic that does the comma separating and making of tag objects that I can't find how it works)
    tags = forms.CharField(required=False, label="Tags (comma separated)")


    class Meta:
        model = Scraper
        fields = ('run_interval', 'title', 'description', 'license', 'published', 'featured')
