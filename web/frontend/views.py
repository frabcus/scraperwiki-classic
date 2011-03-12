from django import forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.contrib import auth
from django.shortcuts import get_object_or_404
import settings
from frontend.forms import SigninForm, UserProfileForm, SearchForm, ResendActivationEmailForm
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag, calculate_cloud, LOGARITHMIC
from codewiki.models import Code, Scraper, View, HELP_LANGUAGES, LANGUAGES_DICT
from tagging.models import Tag, TaggedItem
from market.models import Solicitation, SolicitationStatus
from frontend.forms import CreateAccountForm
from frontend.models import UserToUserRole
from registration.backends import get_backend
from profiles import views as profile_views
import django.contrib.auth.views
import os
import re
import datetime
import urllib
import itertools

from utilities import location


def frontpage(request, public_profile_field=None):
    user = request.user

    #featured
    featured_scrapers = Code.objects.filter(featured=True, wiki_type='scraper').order_by('-first_published_at')[:2]    
    featured_views = Code.objects.filter(featured=True, wiki_type='view').order_by('-first_published_at')[:2]        
    
    #popular tags
    #this is a horrible hack, need to patch http://github.com/memespring/django-tagging to do it properly
    tags_sorted = sorted([(tag, int(tag.count)) for tag in Tag.objects.usage_for_model(Scraper, counts=True)], key=lambda k:k[1], reverse=True)[:10]
    tags = []
    for tag in tags_sorted:
        tags.append(tag[0])
    
    data = {'featured_views': featured_views, 'featured_scrapers': featured_scrapers, 'tags': tags, 'language': 'python'}
    return render_to_response('frontend/frontpage.html', data, context_instance=RequestContext(request))

@login_required
def dashboard(request):
    user = request.user
    owned_code_objects = user.code_set.filter(usercoderole__role='owner', deleted=False).order_by('-created_at')
    owned_count = len(owned_code_objects) 
    # needs to be expanded to include scrapers you have edit rights on.
    contribution_scrapers = user.code_set.filter(usercoderole__role='editor', deleted=False)
    contribution_count = len(contribution_scrapers)
    following_scrapers = user.code_set.filter(usercoderole__role='follow', deleted=False)
    following_count = len(following_scrapers)

    return render_to_response('frontend/dashboard.html', {'owned_code_objects': owned_code_objects, 'owned_count' : owned_count, 'contribution_scrapers' : contribution_scrapers, 'contribution_count': contribution_count, 'following_scrapers' : following_scrapers, 'following_count' : following_count,'language':'python' }, context_instance = RequestContext(request))

def profile_detail(request, username):
    
    user = request.user
    profiled_user = get_object_or_404(User, username=username)
    owned_code_objects = profiled_user.code_set.filter(usercoderole__role='owner', published=True).order_by('-created_at')
    solicitations = Solicitation.objects.filter(deleted=False, user_created=profiled_user).order_by('-created_at')[:5]  

    return profile_views.profile_detail(request, username=username, extra_context={'solicitations': solicitations, 'owned_code_objects': owned_code_objects } )


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
                    error_messages.append(mark_safe("This account has not been activated (ScraperWiki will have allowed you to use the site before activation for your first time). Please check your email (including the spam folder) and click on the link to confirm your account. If you have lost the email or the link has expired please <a href='%s'>request a new one</a>." % reverse('resend_activation_email')))

            else:
                # Account not found                  
                error_messages.append("Sorry, but we could not find that user, or the password was wrong")


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

def help(request, mode=None, language=None):
    tutorials = {}
    viewtutorials = {}
    if not language:
        language = "python"
    display_language = LANGUAGES_DICT[language]
    other_languages = [ (l, d) for (l, d) in HELP_LANGUAGES if l != language]
    if mode=="code_documentation": # Support legacy URL. 
        mode="documentation"
    if not mode or mode=="faq":
        mode = "faq"
        include_tag = "frontend/help_faq.html"
    elif mode=="tutorials":
        tutorials[language] = Scraper.objects.filter(published=True, istutorial=True, language=language).order_by('first_published_at')
        viewtutorials[language] = View.objects.filter(published=True, istutorial=True, language=language).order_by('first_published_at')
        include_tag = "frontend/help_tutorials.html"
    else: 
        include_tag = "frontend/help_%s_%s.html" % (mode, language)
    return render_to_response('frontend/help.html', { 'mode' : mode, 'language' : language, 'display_language' : display_language, \
             'include_tag' : include_tag, 'tutorials': tutorials, 'viewtutorials': viewtutorials, \
             'other_languages' : other_languages }, 
             context_instance = RequestContext(request))

def browse_wiki_type(request, wiki_type = None, page_number = 1):
    special_filter = request.GET.get('filter', None)
    return browse(request, page_number, wiki_type, special_filter)

def browse(request, page_number = 1, wiki_type = None, special_filter=None):
    if wiki_type == None:
        all_code_objects = Code.objects.filter(published=True).order_by('-created_at')
    else:
        all_code_objects = Code.objects.filter(wiki_type=wiki_type, published=True).order_by('-created_at') 

    #extra filters (broken scraper lists etc)
    if special_filter == 'sick':
        all_code_objects = all_code_objects.filter(status='sick')
    elif special_filter == 'no_description':
        all_code_objects = all_code_objects.filter(description='')
    elif special_filter == 'no_tags':
        #hack to get scrapers with no tags (tags don't recognise inheritance)
        if wiki_type == 'scraper':
            all_code_objects = TaggedItem.objects.get_no_tags(Scraper.objects.all().order_by('-created_at') )
        else:
            all_code_objects = TaggedItem.objects.get_no_tags(View.objects.all().order_by('-created_at') )


    # filter out scrapers that have no records
    if not special_filter:
        all_code_objects = all_code_objects.exclude(wiki_type='scraper', scraper__record_count=0)
    
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

    dictionary = { "scrapers": scrapers, 'wiki_type':wiki_type, "form": form, "featured_scrapers":featured_scrapers, 'special_filter': special_filter, 'language': 'python'}
    return render_to_response('frontend/browse.html', dictionary, context_instance=RequestContext(request))


def search(request, q=""):
    if (q != ""):
        form = SearchForm(initial={'q': q})
        q = q.strip()

        tags = Tag.objects.filter(name__icontains=q)
        scrapers = Code.objects.search(q)
        num_results = tags.count() + scrapers.count()
        return render_to_response('frontend/search_results.html',
            {
                'scrapers': scrapers,
                'tags': tags,
                'num_results': num_results,
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
            return render_to_response('frontend/search_results.html', {
                'form': form,},
                context_instance=RequestContext(request))
    else:
        form = SearchForm()
        return render_to_response('frontend/search_results.html', {
            'form': form,
        }, context_instance = RequestContext(request))

def get_involved(request):

        scraper_count = Scraper.objects.count()
        view_count = View.objects.count()
        
        #no description
        scraper_no_description_count = Scraper.objects.filter(description='').count()
        scraper_description_percent = 100 - int(scraper_no_description_count / float(scraper_count) * 100)

        view_no_description_count = View.objects.filter(description='').count()
        view_description_percent = 100 - int(view_no_description_count / float(view_count) * 100)

        #no tags
        scraper_no_tags_count = TaggedItem.objects.get_no_tags(Scraper.objects.filter()).count()
        scraper_tags_percent = 100 - int(scraper_no_tags_count / float(scraper_count) * 100)
    
        view_no_tags_count = TaggedItem.objects.get_no_tags(View.objects.filter()).count()
        view_tags_percent = 100 - int(view_no_tags_count / float(view_count) * 100)

        #scraper requests
        status = SolicitationStatus.objects.get(status='open')
        solicitation_count = Solicitation.objects.filter().count()
        solicitation_open_count = Solicitation.objects.filter(status=status).count()    
        try:
            solicitation_percent = int(solicitation_open_count / float(solicitation_count) * 100)        
        except ZeroDivisionError:
            solicitation_percent = 100
        
        #scraper status
        scraper_sick_count = Scraper.objects.filter(status='sick').count()
        scraper_sick_percent = 100 - int(scraper_sick_count / float(scraper_count) * 100)

        data = {
            'scraper_count': scraper_count,
            'view_count': view_count,
            'scraper_no_description_count': scraper_no_description_count,
            'scraper_description_percent': scraper_description_percent,
            'view_no_description_count': view_no_description_count,
            'view_description_percent': view_description_percent,
            'scraper_no_tags_count': scraper_no_tags_count,
            'scraper_tags_percent': scraper_tags_percent,
            'view_no_tags_count': view_no_tags_count,
            'view_tags_percent': view_tags_percent,
            'solicitation_count': solicitation_count,
            'solicitation_open_count': solicitation_open_count,
            'solicitation_percent': solicitation_percent,
            'scraper_sick_count': scraper_sick_count,
            'scraper_sick_percent': scraper_sick_percent,
            'language': 'python',
        }

        return render_to_response('frontend/get_involved.html', data, context_instance=RequestContext(request))

def stats(request):

    return render_to_response('frontend/stats.html', {}, context_instance=RequestContext(request))

#hack - get a merged list of scraper and soplicitation tags
def _get_merged_tags(min_count = None):
    scraper_tags = Tag.objects.usage_for_model(Scraper, counts=True)
    view_tags = Tag.objects.usage_for_model(View, counts=True)
    solicitation_tags = Tag.objects.usage_for_model(Solicitation, counts=True)

    all_tags = {}

    for tag in itertools.chain(scraper_tags, view_tags, solicitation_tags):
        existing = all_tags.get(tag.name, None)
        if existing:
            existing.count += tag.count
        else:
            all_tags[tag.name] = tag

    return calculate_cloud(all_tags.values(), steps=4, distribution=LOGARITHMIC)
    

def tags(request):

    tags = _get_merged_tags()

    return render_to_response('frontend/tags.html', {'tags':tags,}, context_instance=RequestContext(request))
    
def tag(request, tag):
    tag = get_tag(tag)
    if not tag:
        raise Http404

    #get all scrapers and views with this tag
    scrapers = TaggedItem.objects.get_by_model(Scraper.objects.all(), tag)
    views = TaggedItem.objects.get_by_model(View.objects.all(), tag)
    code_objects = sorted(list(scrapers) + list(views), key=lambda x: x.created_at, reverse=True)
    
    #get all open and pending solicitations with this tag
    solicitations_open = Solicitation.objects.filter(deleted=False, status=SolicitationStatus.objects.get(status='open')).order_by('created_at')
    solicitations_pending = Solicitation.objects.filter(deleted=False, status=SolicitationStatus.objects.get(status='pending')).order_by('created_at')
    solicitations_completed = Solicitation.objects.filter(deleted=False, status=SolicitationStatus.objects.get(status='completed')).order_by('created_at')

    solicitations_open = TaggedItem.objects.get_by_model(solicitations_open, tag)
    solicitations_pending = TaggedItem.objects.get_by_model(solicitations_pending, tag)
    solicitations_completed = TaggedItem.objects.get_by_model(solicitations_completed, tag)

    #do some maths to work out how complete the tag is at the moment
    solicitations_percent_complete = 0
    total_solicitations = solicitations_completed.count() + solicitations_open.count() + solicitations_pending.count()
    if total_solicitations > 0:
        solicitations_percent_complete = float(solicitations_completed.count()) / float(total_solicitations) * 100

    scrapers_fixed_percentage = 0
    if scrapers.count() > 0:
        scrapers_fixed_percentage = 100.0 - float(scrapers.filter(status='sick').count()) / float(scrapers.count()) * 100
        
    return render_to_response('frontend/tag.html', {
        'tag' : tag,
        'scrapers': code_objects,
        'solicitations_open':solicitations_open,
        'solicitations_pending':solicitations_pending,
        'solicitations_percent_complete': solicitations_percent_complete,
        'scrapers_fixed_percentage': scrapers_fixed_percentage,
    }, context_instance = RequestContext(request))

def resend_activation_email(request):
    form = ResendActivationEmailForm(request.POST or None)

    template = 'frontend/resend_activation_email.html'
    if form.is_valid():
        template = 'frontend/resend_activation_complete.html'
        try:
            user = User.objects.get(email=form.cleaned_data['email_address'])
            if not user.is_active:
                site = Site.objects.get_current()
                user.registrationprofile_set.get().send_activation_email(site)
        except Exception, ex:
            print ex

    return render_to_response(template, {'form': form}, context_instance = RequestContext(request))
