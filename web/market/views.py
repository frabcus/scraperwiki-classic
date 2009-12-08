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

from paypal.standard.forms import PayPalPaymentsForm

from market import models
from market import forms
from payment.models import Invoice
from scraper.models import Scraper

@login_required
def solicitation (request):

    form = forms.SolicitationForm()    
    if request.method == 'POST':
        form = forms.SolicitationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            solicitation = form.save(commit=False)
            solicitation.user_created = request.user
            solicitation.save()
            return HttpResponseRedirect(reverse('market_list'))

    return render_to_response('market/solicitation.html', {'form': form, 'market_bounty_charge': settings.MARKET_BOUNTY_CHARGE }, context_instance = RequestContext(request))

def market_list (request, mode='open'):

    #get all scrapers not marked deleted or 
    status = models.SolicitationStatus.objects.get(status=mode)
    solicitations = models.Solicitation.objects.filter(deleted=False, status=status).order_by('-created_at')    
    return render_to_response('market/market_list.html', {'solicitations': solicitations, 'status': status}, context_instance = RequestContext(request))

def single (request, solicitation_id):
    solicitation = get_object_or_404(models.Solicitation, id=solicitation_id)
    status = models.SolicitationStatus.objects.get(status='open')
    recent_solicitations = models.Solicitation.objects.filter(deleted=False, status=status).order_by('-created_at')[:5]    
    return render_to_response('market/market_single.html', {'solicitation': solicitation, 'recent_solicitations': recent_solicitations}, context_instance = RequestContext(request))

@login_required
def claim (request, solicitation_id):

    #this is a custom form, so we need to pass the user_id
    user_id = request.user.pk
    solicitation = get_object_or_404(models.Solicitation, id=solicitation_id)
    form = forms.SolicitationClaimForm(instance = solicitation, user_id = user_id)

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
    print "HELLO!!!!!!!!!!!!!!!!!!!!!!!!!"
    return render_to_response('market/paypal_return.html',context_instance = RequestContext(request))
    
def paypal_return (request):

    return render_to_response('market/paypal_return.html',context_instance = RequestContext(request))
    
def paypal_cancel (request):

    return render_to_response('market/paypal_cancel.html',context_instance = RequestContext(request))
            