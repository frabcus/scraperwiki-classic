from django.template import RequestContext
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from market import models
from market import forms

def solicitation(request):

    form = forms.SolicitationForm()    
    if request.method == 'POST':
        form = forms.SolicitationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            if request.user.is_authenticated():
                solicitation = form.save(commit=False)
                solicitation.user_created = request.user
                solicitation.save()
            else:
                print "bla"

    return render_to_response('market/solicitation.html', {'form': form }, context_instance = RequestContext(request))

def list(request):
    
    return True