from django.forms import ModelForm, ChoiceField

from scraper.models import ScraperRequest

class ScraperRequestForm (ModelForm):
    class Meta:
        model = ScraperRequest
        fields = ('description', 'source_link',)
