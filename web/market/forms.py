from django.forms import ModelForm, ChoiceField

from market.models import Solicitation

class SolicitationForm (ModelForm):
    class Meta:
        model = Solicitation
        fields = ('title', 'link', 'details')