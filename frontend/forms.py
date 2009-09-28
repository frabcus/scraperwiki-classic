from django import forms
from frontend.models import UserProfile
import datetime
#from django.forms.extras.widgets import Textarea

class UserProfileForm(forms.Form):
    bio             = forms.CharField(widget=forms.Textarea, required=False)
    alert_frequency = forms.ChoiceField(choices=(('0', 'instant'),('3600', 'One Hour')))

    def __init__(instance = None):
        if instance:
	        self.instance = instance
	        self.data['bio'] = self.instance.bio
	        self.data['alert_frequency'] = self.instance.alert_frequency
        else:
	        self.instance = UserProfile()

    def save(self, commit=True):
        self.instance.bio = self.get_bio()
        self.instance.alert_frequency = self.get_alert_frequency()
        self.instance.alerts_last_sent = datetime.datetime.now()
        if commit:
            self.instance.save()
		
        return self.instance

    def get_bio(self):
        return self.data['bio']
	
    def get_alert_frequency(self):
        return self.data['alert_frequency']	
