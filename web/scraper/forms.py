from django import forms
from models import Scraper

class SearchForm(forms.Form):
    q = forms.CharField(label='Find datasets', max_length=50)

class RunIntervalForm (forms.ModelForm):

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
                                
    class Meta:
        model = Scraper
        fields = ('run_interval')