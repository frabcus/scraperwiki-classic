from django import forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.contrib import auth
from django.shortcuts import get_object_or_404
import settings
from frontend.forms import SigninForm, UserProfileForm, SearchForm
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from codewiki.models import Scraper, Code, UserCodeEditing
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
import urllib

from utilities import location

from codewiki.models import Scraper as ScraperModel  # is this renaming necessary?

def frontpage(request, public_profile_field=None):
    user = request.user

    #featured
    featured_scrapers = Code.objects.filter(featured=True, wiki_type='scraper').order_by('-first_published_at')[:5]    
    featured_views = Code.objects.filter(featured=True, wiki_type='view').order_by('-first_published_at')[:5]        
    
    #market
    solicitations = Solicitation.objects.filter(deleted=False).order_by('-created_at')[:5]
    
    data = {'solicitations': solicitations, 'featured_views': featured_views, 'featured_scrapers': featured_scrapers,}
    return render_to_response('frontend/frontpage.html', data, context_instance=RequestContext(request))
@login_required
def dashboard(request):
	user = request.user
	owned_scrapers = user.code_set.filter(usercoderole__role='owner', deleted=False).order_by('-created_at')
	owned_count = len(owned_scrapers) 
	# needs to be expanded to include scrapers you have edit rights on.
	contribution_scrapers = user.code_set.filter(usercoderole__role='editor', deleted=False)
	contribution_count = len(contribution_scrapers)
	following_scrapers = user.code_set.filter(usercoderole__role='follow', deleted=False)
	following_count = len(following_scrapers)

	return render_to_response('frontend/your_scrapers.html', {'owned_scrapers': owned_scrapers, 'owned_count' : owned_count, 'contribution_scrapers' : contribution_scrapers, 'contribution_count': contribution_count, 'following_scrapers' : following_scrapers, 'following_count' : following_count, }, context_instance = RequestContext(request))

def profile_detail(request, username):
    
    user = request.user
    profiled_user = get_object_or_404(User, username=username)
    owned_scrapers = profiled_user.code_set.filter(usercoderole__role='owner', wiki_type="scraper", published=True)
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

def browse(request, page_number = 1, wiki_type = None):
    if wiki_type == None:
        all_code_objects = Code.objects.filter(published=True).order_by('-created_at')
    else:
        all_code_objects = Code.objects.filter(published=True, wiki_type=wiki_type).order_by('-created_at')

    # Number of results to show from settings
    paginator = Paginator(all_code_objects, settings.SCRAPERS_PER_PAGE)

    try:
        page = int(page_number)
    except (ValueError, TypeError):
        page = 1

    if page == 1:
        featured_scrapers = Code.objects.filter(published=True, featured=True).order_by('-created_at')
    else:
        featured_scrapers = None

    # If page request (9999) is out of range, deliver last page of results.
    try:
        scrapers = paginator.page(page)
    except (EmptyPage, InvalidPage):
        scrapers = paginator.page(paginator.num_pages)

    form = SearchForm()

    # put number of people here so we can see it
    #npeople = UserCodeEditing in models.UserCodeEditing.objects.all().count()
    # there might be a slick way of counting this, but I don't know it.
    npeople = len(set([userscraperediting.user  for usercodeediting in UserCodeEditing.objects.all() ]))
    dictionary = { "scrapers": scrapers, "form": form, "featured_scrapers":featured_scrapers, "npeople": npeople }
    return render_to_response('frontend/browse.html', dictionary, context_instance=RequestContext(request))


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
            return HttpResponseRedirect('/search/%s/' % urllib.quote(q.encode('utf-8')))
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

