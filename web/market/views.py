from django.template import RequestContext
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from market import models
from market import forms

from django.contrib.auth.decorators import login_required

@login_required
def solicitation(request):

    form = forms.SolicitationForm()    
    if request.method == 'POST':
        form = forms.SolicitationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            solicitation = form.save(commit=False)
            solicitation.user_created = request.user
            solicitation.save()
            return HttpResponseRedirect(reverse('market_list'))

    return render_to_response('market/solicitation.html', {'form': form }, context_instance = RequestContext(request))


def market_list(request):
    solicitations = models.Solicitation.objects.filter(deleted=False).order_by('-created_at')    
    return render_to_response('market/market_list.html', {'solicitations': solicitations}, context_instance = RequestContext(request))