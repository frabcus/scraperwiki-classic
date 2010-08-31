from django import forms
from django.forms import widgets
import codewiki

class editorForm(forms.ModelForm):

    class Meta:
        model = codewiki.models.Code
        fields = ('title', 'code', 'wiki_type')
        
    title = forms.CharField(widget=forms.TextInput(attrs={'title' : 'Untitled'}),label = "Title*",)
    wiki_type = forms.ChoiceField(choices=codewiki.models.code.WIKI_TYPES, widget=forms.HiddenInput())    
    code = forms.CharField(widget=widgets.Textarea({'cols':'80', 'rows':'10', 'style':'width:90%'}))

    def clean_title(self):
        title = self.cleaned_data['title']
        if not title or title == '' or title.lower() == 'untitled':
            raise forms.ValidationError("Scraper needs a title")
        return title
