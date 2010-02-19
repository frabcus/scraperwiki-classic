import random
from django import forms
from django.conf import settings
from django.template import RequestContext
from django.template import loader, Context
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag

from collections import defaultdict

from paypal.standard.forms import PayPalPaymentsForm

from market import models
from market import forms
from payment.models import Invoice
from scraper.models import Scraper
    
    
def solicitation (request):
    form = forms.SolicitationForm()    
    if request.method == 'POST':
        form = forms.SolicitationForm(data=request.POST, files=request.FILES)
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
            return render_to_response('market/market_edit.html', {'form': form, 'market_bounty_charge': settings.MARKET_BOUNTY_CHARGE }, context_instance = RequestContext(request))
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
    return render_to_response('market/market_single.html', {'solicitation': solicitation, 'solicitation_tags': solicitation_tags, 'recent_solicitations': recent_solicitations}, context_instance = RequestContext(request))

def tag(request, tag):
    from tagging.utils import get_tag
    from tagging.models import Tag, TaggedItem

    tag = get_tag(tag)

    # possibly not the best way of doing this
    status = models.SolicitationStatus.objects.get(status='open')
    solicitations_open = models.Solicitation.objects.filter(deleted=False, status=status).order_by('created_at')
    status = models.SolicitationStatus.objects.get(status='pending')
    solicitations_pending = models.Solicitation.objects.filter(deleted=False, status=status).order_by('created_at')
    status = models.SolicitationStatus.objects.get(status='completed')
    solicitations_complete = models.Solicitation.objects.filter(deleted=False, status=status).order_by('created_at')
    queryset_open = TaggedItem.objects.get_by_model(solicitations_open, tag)
    queryset_pending = TaggedItem.objects.get_by_model(solicitations_pending, tag)	
    queryset_complete = TaggedItem.objects.get_by_model(solicitations_complete, tag)

    # calculate percentage complete 
    closed_count = queryset_complete.count()
    total_count = queryset_open.count() + queryset_pending.count() + queryset_complete.count()
    percentage_complete = (float(closed_count)/float(total_count)) * 100

    # calculate top scraper writers, and sort
    writers = []
    for closed in queryset_complete:
	    temp_user = closed.scraper.owner()
	    writers.append(temp_user)
    top_writers = leaders(writers)

    return render_to_response('market/tag.html', {
        'queryset_open': queryset_open, 
        'queryset_pending': queryset_pending, 
        'queryset_complete': queryset_complete, 
        'closed_count': closed_count, 
        'total_count': total_count, 
        'percentage_complete': percentage_complete, 
        'top_writers': top_writers, 
        'tag' : tag,
    }, context_instance = RequestContext(request))

def leaders(xs, top=5):
    counts = defaultdict(int)
    for x in xs:
        counts[x] += 1
    return sorted(counts.items(), reverse=True, key=lambda tup: tup[1])[:top]

@login_required
def claim (request, solicitation_id):

    #this is a custom form, so we need to pass the user_id
    user_id = request.user.pk
    solicitation = get_object_or_404(models.Solicitation, id=solicitation_id)
    form = forms.SolicitationClaimForm(instance=solicitation, user_id=user_id)

    #check if open
    if solicitation.status.status != 'open':
        return HttpResponseRedirect(reverse('market_view', args=(solicitation_id,)))

    #postback
    if request.method == 'POST':
        form = forms.SolicitationClaimForm(request.POST, instance = solicitation, user_id = user_id)
        if form.is_valid():
            user = request.user
            scraper = Scraper.objects.get(id=request.POST['scraper'])

            #mark as claimed
            solicitation.claim(scraper=scraper, user=user)

            #email the creator telling them it is done, and to pay if nesesary
            title = "The scraper you requested for " + solicitation.title + " has been written"
            template = loader.get_template('emails/market_claim.txt')
            context = Context({
                'scraper': scraper,
                'solicitation': solicitation,         
                'url': 'http://' + Site.objects.get_current().domain       
            })
            send_mail(title, template.render(context), settings.EMAIL_FROM, [solicitation.user_created.email], fail_silently=False)

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

    #find the invoice
    invoice = get_object_or_404(Invoice, parent_id=solicitation_id, item_type='solicitation', deleted = False)
    if invoice == False:
        raise Http404

    #setup the paypal form
    domain = 'http://' + Site.objects.get_current().domain
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": invoice.price,
        "item_name": invoice.title,
        "invoice": invoice.pk,
        "notify_url": domain + reverse('paypal-ipn'),
        "return_url": domain + reverse('market_paypal_return'),
        "cancel_return": domain + reverse('market_paypal_cancel'),
        "currency_code": "GBP",
    }

    # Create the instance.
    use_sandbox = settings.DEBUG
    form = PayPalPaymentsForm(initial=paypal_dict)
    return render_to_response('market/complete.html', {'use_sandbox': use_sandbox, 'solicitation': solicitation, 'scraper': solicitation.scraper, 'form': form}, context_instance = RequestContext(request))


def paypal_notify (request):
    return render_to_response('market/paypal_return.html',context_instance = RequestContext(request))
    
def paypal_return (request):

    return render_to_response('market/paypal_return.html',context_instance = RequestContext(request))
    
def paypal_cancel (request):

    return render_to_response('market/paypal_cancel.html',context_instance = RequestContext(request))
            