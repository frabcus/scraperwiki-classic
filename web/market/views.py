from django.conf import settings
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag

from collections import defaultdict

from paypal.standard.forms import PayPalPaymentsForm

from market import models
from market import forms
from payment.models import Invoice

def request_solicitation(request):
    initial = {'tags': request.GET.get('tags', None)}
    form = forms.SolicitationForm(initial=initial)

    if request.method == 'POST':
        form = forms.SolicitationForm(data=request.POST)
        if form.is_valid():
            solicitation = form.save(commit=False)
            if not request.user.is_authenticated():
                request.notifications.add("You need to sign in or create an account - don't worry, your request is safe")                
                request.session['SolicitationDraft'] = solicitation
                return HttpResponseRedirect(reverse('login') + "?next=%s" % reverse('market_list'))    
            else:
                solicitation.user_created = request.user
                solicitation.save()
                solicitation.tags = request.POST.get('tags')
                return HttpResponseRedirect(reverse('market_list'))
    status = models.SolicitationStatus.objects.get(status='open')
    recent_solicitations = models.Solicitation.objects.filter(deleted=False, status=status).order_by('-created_at')[:5]  
    return render_to_response('market/solicitation.html', {'form': form, 'recent_solicitations' : recent_solicitations, 'market_bounty_charge': settings.MARKET_BOUNTY_CHARGE }, context_instance = RequestContext(request))

@login_required
# edit an existing soliciation - can only do this if you are the owner
def edit(request, solicitation_id):
    solicitation = get_object_or_404(models.Solicitation, id=solicitation_id)
	#check if open, redirect if not
    if solicitation.status.status != 'open':
        return HttpResponseRedirect(reverse('market_view', args=(solicitation_id,)))
    #check user owns it, redirect if not
    if (solicitation.user_created == request.user):
        if request.method == 'POST':
            form = forms.SolicitationForm(request.POST, instance=solicitation)
            if form.is_valid():
                solicitation = form.save(commit=False)
                solicitation.user_created = request.user
                solicitation.save()
                solicitation.tags = request.POST.get('tags')                
                return HttpResponseRedirect(reverse('market_view', args=(solicitation_id,)))
        else:
            solicitation.__dict__['tags'] = ", ".join(tag.name for tag in solicitation.tags)
            form = forms.SolicitationForm(solicitation.__dict__, instance=solicitation)
            return render_to_response('market/market_edit.html', {'solicitation': solicitation, 'form': form, 'market_bounty_charge': settings.MARKET_BOUNTY_CHARGE, 'selected_tab': 'edit'}, context_instance = RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('market_view', args=(solicitation_id,)))

def market_list (request, mode='open'):

    #TODO: move this to a seperate view
    # save any items in the session
    session_solicitation_draft = request.session.get('SolicitationDraft', None)
    if session_solicitation_draft:
        session_solicitation_draft.user_created = request.user
        session_solicitation_draft.save()
        del request.session['SolicitationDraft']            

    #get all scrapers not marked deleted or
    status = models.SolicitationStatus.objects.get(status=mode)
    solicitations = models.Solicitation.objects.filter(deleted=False, status=status).order_by('-created_at')    
    return render_to_response('market/market_list.html', {'solicitations': solicitations, 'status': status}, context_instance = RequestContext(request))

def single (request, solicitation_id):
    solicitation = get_object_or_404(models.Solicitation, id=solicitation_id)
    solicitation_tags = Tag.objects.get_for_object(solicitation)
    status = models.SolicitationStatus.objects.get(status='open')
    recent_solicitations = models.Solicitation.objects.filter(deleted=False, status=status).order_by('-created_at')[:5]    
    return render_to_response('market/market_single.html', {'solicitation': solicitation, 'solicitation_tags': solicitation_tags, 'recent_solicitations': recent_solicitations, 'selected_tab': 'overview'}, context_instance = RequestContext(request))


def discuss (request, solicitation_id):
    solicitation = get_object_or_404(models.Solicitation, id=solicitation_id)
    solicitation_tags = Tag.objects.get_for_object(solicitation)
    status = models.SolicitationStatus.objects.get(status='open')
    recent_solicitations = models.Solicitation.objects.filter(deleted=False, status=status).order_by('-created_at')[:5]    
    return render_to_response('market/market_discuss.html', {'solicitation': solicitation, 'solicitation_tags': solicitation_tags, 'recent_solicitations': recent_solicitations, 'selected_tab': 'comments'}, context_instance = RequestContext(request))

def leaders(xs, top=5):
    counts = defaultdict(int)
    for x in xs:
        counts[x] += 1
    return sorted(counts.items(), reverse=True, key=lambda tup: tup[1])[:top]

@login_required
def claim (request, solicitation_id):
    #check if open
    solicitation = get_object_or_404(models.Solicitation, id=solicitation_id)

    if solicitation.status.status != 'open':
        return HttpResponseRedirect(reverse('market_view', args=(solicitation_id,)))

    #this is a custom form, so we need to pass the user_id
    user_id = request.user.pk

    form = forms.SolicitationClaimForm(request.POST or None, user_id=user_id)

    if form.is_valid():
        user = request.user
        scraper = form.cleaned_data['scraper']

        #mark as claimed
        solicitation.claim(scraper=scraper, user=user)

        #redirect & add message
        request.notifications.add("Thanks, we've emailed " + solicitation.user_created.username + " to let them know")
        return HttpResponseRedirect(reverse('market_view', args=(solicitation_id,)))

    return render_to_response('market/claim.html', {'solicitation': solicitation, 'form': form}, context_instance = RequestContext(request))

@login_required
def complete (request, solicitation_id):

    #get the solicitation and make sure it is 'pending' and has a scraper associated with it 
    solicitation = get_object_or_404(models.Solicitation, id=solicitation_id)
    status = models.SolicitationStatus.objects.get(status='pending')
    if solicitation.scraper == False or solicitation.status != status:
        raise Http404

    #make sure signed in user is the person who created the solicitation
    if solicitation.user_created != request.user:
        raise Http404

    context = {}
    context['solicitation'] = solicitation
    context['scraper'] = solicitation.scraper

    if solicitation.has_bounty():
        #find the invoice
        invoice = get_object_or_404(Invoice, parent_id=solicitation_id, item_type='solicitation', deleted = False)

        #setup the paypal form
        domain = 'http://' + Site.objects.get_current().domain
        paypal_dict = {
            "business": settings.PAYPAL_RECEIVER_EMAIL,
            "amount": "%.2f" % invoice.price,
            "item_name": invoice.title,
            "invoice": invoice.pk,
            "notify_url": domain + reverse('paypal-ipn'),
            "return_url": domain + reverse('market_paypal_return'),
            "cancel_return": domain + reverse('market_paypal_cancel'),
            "currency_code": "GBP",
        }

        # Create the instance.
        context['use_sandbox'] = settings.DEBUG
        context['form'] = PayPalPaymentsForm(initial=paypal_dict)
    else:
        form = forms.SolicitationAcceptForm(request.POST or None)
        context['form'] = form

        if form.is_valid():
            if form.cleaned_data['choice'] == 'accept':
                solicitation.complete()
                request.notifications.add("Scraper Accepted")
            else:
                solicitation.reject()
                request.notifications.add("Scraper Rejected")

            return HttpResponseRedirect(reverse('market_view', args=(solicitation_id,)))

    return render_to_response('market/complete.html', context, context_instance = RequestContext(request))

def paypal_return (request):
    return render_to_response('market/paypal_return.html', context_instance = RequestContext(request))
    
def paypal_cancel (request):
    return render_to_response('market/paypal_cancel.html', context_instance = RequestContext(request))
