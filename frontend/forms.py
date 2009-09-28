from django import forms

class UserProfileForm(forms.Form):
    bio = forms.CharField(widget=Textarea, required=False)
    
