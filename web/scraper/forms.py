from django import forms

class SearchForm(forms.Form):
    q = forms.CharField(label='Search scrapers', max_length=50)
    