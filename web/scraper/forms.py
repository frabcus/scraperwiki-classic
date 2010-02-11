from django import forms

class SearchForm(forms.Form):
    q = forms.CharField(label='Find datasets', max_length=50)
    