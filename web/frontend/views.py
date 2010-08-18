from django import forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.contrib import auth
from django.shortcuts import get_object_or_404
import settings
from frontend.forms import SigninForm, UserProfileForm, SearchForm

from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from codewiki.models import Scraper, Code
from market.models import Solicitation
from frontend.forms import CreateAccountForm
from frontend.models import UserToUserRole
from registration.backends import get_backend
from profiles import views as profile_views
from codewiki.forms import ChooseTemplateForm
import django.contrib.auth.views
import os
import re
import datetime

from utilities import location

from codewiki.models import Scraper as ScraperModel  # is this renaming necessary?

def frontpage(request, public_profile_field=None):
    user = request.user

    # The following items are only used when there is a logged in user.	
    if user.is_authenticated():
        hide_logo = False
        grey_body = False   
        my_scrapers = user.code_set.filter(usercoderole__role='owner', deleted=False).order_by('-created_at')
        following_scrapers = user.code_set.filter(usercoderole__role='follow', deleted=False).order_by('-created_at')
        following_users = user.to_user.following()
        following_users_count = len(following_users)
        # contribution_scrapers needs to be expanded to include scrapers you have edit rights on
        contribution_scrapers = my_scrapers
        template = 'frontend/frontpage_logged_in.html'        
    
    # the following is for an anonymous user
    else:
        hide_logo = True
        grey_body = True
        my_scrapers = []
        following_scrapers = []
        following_users = []
        following_users_count = 0
        contribution_scrapers = []
        profile_obj = None
        template = 'frontend/frontpage.html'
        
    contribution_count = len(contribution_scrapers)
    good_contribution_scrapers = []
    # cut number of scrapers displayed on homepage down to the most recent 10 items
    my_scrapers = my_scrapers[:10]
    print my_scrapers[0].relations.add(my_scrapers[1])
    has_scrapers = len(my_scrapers) > 0
    # also need to add filtering to limit to public published scrapers
    for scraper in contribution_scrapers:
        if scraper.is_good():
            good_contribution_scrapers.append(scraper)

    #new scrapers
    new_scrapers = Scraper.objects.filter(deleted=False, published=True, featured=False).order_by('-first_published_at')[:5]
    featured_scrapers = Scraper.objects.filter(deleted=False, published=True, featured=True).order_by('-first_published_at')[:5]    
    
    #suggested scrapers
    solicitations = Solicitation.objects.filter(deleted=False).order_by('-created_at')[:5]
    
    data = {'grey_body': grey_body, 'hide_logo': hide_logo, 'my_scrapers': my_scrapers, 'has_scrapers':has_scrapers, 
            'solicitations': solicitations, 'following_scrapers': following_scrapers, 'following_users': following_users, 'following_users_count' : following_users_count, 
            'new_scrapers': new_scrapers, 'featured_scrapers': featured_scrapers, 'contribution_count': contribution_count, }
    return render_to_response(template, data, context_instance=RequestContext(request))

def my_scrapers(request):
	user = request.user

	if user.is_authenticated():
		owned_scrapers = user.scraper_set.filter(usercoderole__role='owner', deleted=False).order_by('-created_at')
		owned_count = len(owned_scrapers) 
		# needs to be expanded to include scrapers you have edit rights on.
		contribution_scrapers = user.scraper_set.filter(usercoderole__role='editor', deleted=False)
		contribution_count = len(contribution_scrapers)
		following_scrapers = user.scraper_set.filter(usercoderole__role='follow', deleted=False)
		following_count = len(following_scrapers)
	else:
		return HttpResponseRedirect(reverse('frontpage'))

	return render_to_response('frontend/my_scrapers.html', {'owned_scrapers': owned_scrapers, 'owned_count' : owned_count, 'contribution_scrapers' : contribution_scrapers, 'contribution_count': contribution_count, 'following_scrapers' : following_scrapers, 'following_count' : following_count, }, context_instance = RequestContext(request))

def profile_detail(request, username):
    
    user = request.user
    profiled_user = get_object_or_404(User, username=username)
    owned_scrapers = profiled_user.scraper_set.filter(usercoderole__role='owner', published=True)
    solicitations = Solicitation.objects.filter(deleted=False, user_created=profiled_user).order_by('-created_at')[:5]  

    return profile_views.profile_detail(request, username=username, extra_context={ 'solicitations' : solicitations, 'owned_scrapers' : owned_scrapers, } )


def edit_profile(request):
                form = UserProfileForm()
                return profile_views.edit_profile(request, form_class=form)

def process_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('frontpage'))

def login(request):

    error_messages = []

    #grab the redirect URL if set
    redirect = request.GET.get('next') or request.POST.get('redirect', '')
    
    #Create login and registration forms
    login_form = SigninForm()
    registration_form = CreateAccountForm()

    if request.method == 'POST':

        #Existing user is logging in
        if request.POST.has_key('login'):

            login_form = SigninForm(data=request.POST)
            user = auth.authenticate(username=request.POST['user_or_email'], password=request.POST['password'])

            if user is not None:
                if user.is_active:

                    #Log in
                    auth.login(request, user)

                    #set session timeout
                    if request.POST.has_key('remember_me'):
                        request.session.set_expiry(settings.SESSION_TIMEOUT)


                    if redirect:
                        return HttpResponseRedirect(redirect)
                    else:
                        return HttpResponseRedirect(reverse('frontpage'))

                else:
                    # Account exists, but not activated                    
                    error_messages.append("This account has not been activated, please check your email and click on the link to confirm your account")

            else:
                # Account not found                  
                error_messages.append("Sorry, but we could not find that username or email address")


        #New user is registering
        elif request.POST.has_key('register'):

            registration_form = CreateAccountForm(data=request.POST)

            if registration_form.is_valid():
                backend = get_backend(settings.REGISTRATION_BACKEND)             
                new_user = backend.register(request, **registration_form.cleaned_data)

                #sign straight in
                signed_in_user = auth.authenticate(username=request.POST['username'], password=request.POST['password1'])
                auth.login(request, signed_in_user)                

                #redirect
                if redirect:
                    return HttpResponseRedirect(redirect)
                else:
                    return HttpResponseRedirect(reverse('frontpage'))

    else:
        login_form = SigninForm()
        registration_form = CreateAccountForm()
        message = None

    return render_to_response('registration/extended_login.html', {'registration_form': registration_form, 'login_form': login_form, 'error_messages': error_messages, 'redirect': redirect}, context_instance = RequestContext(request))

def tutorials(request):
    languages = Scraper.objects.filter(published=True, istutorial=True).values_list('language', flat=True).distinct()
    tutorials = {}
    for language in languages:
        tutorials[language] = Scraper.objects.filter(published=True, istutorial=True, language=language).order_by('first_published_at')
    return render_to_response('frontend/tutorials.html', {'tutorials': tutorials}, context_instance = RequestContext(request))

def search(request, q=""):
    if (q != ""):
        form = SearchForm(initial={'q': q})
        q = q.strip()

        scrapers = Code.objects.search(q)
        return render_to_response('frontend/search_results.html',
            {
                'scrapers': scrapers,
                'form': form,
                'query': q,},
            context_instance=RequestContext(request))

    # If the form has been submitted, or we have a search term in the URL
    # - redirect to nice URL
    elif (request.POST):
        form = SearchForm(request.POST)
        if form.is_valid():
            q = form.cleaned_data['q']
            # Process the data in form.cleaned_data
            # Redirect after POST
            return HttpResponseRedirect('/search/%s/' % q)
        else:
            form = SearchForm()
            return render_to_response('frontend/search.html', {
                'form': form,},
                context_instance=RequestContext(request))
    else:
        form = SearchForm()
        return render_to_response('frontend/search.html', {
            'form': form,
        }, context_instance = RequestContext(request))
