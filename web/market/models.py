from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template import loader, Context
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from codewiki.models import Scraper
from payment.models import Invoice
from payment.models import payment_done

import market
import tagging

def solicitation_paid(sender, invoice, **kwargs):

    solicitation = Solicitation.objects.get(id=invoice.parent_id, deleted=False)
    if not solicitation:
        raise Exception("Unable to find solicitation for ID")

    solicitation.complete()    


#pickup payment signals
payment_done.connect(solicitation_paid)

class SolicitationStatus(models.Model):
    """
        Potential statuses of a solicitation
    """
    status = models.CharField(max_length = 50)
    display_name = models.CharField(max_length = 50)    

    class Meta:
        verbose_name_plural = "SolicitationStatuses"

    def __unicode__(self):
        return self.display_name

class Solicitation(models.Model):

    """
	   Requests for scrapers to be written. 
    """

    title   = models.CharField(max_length = 100, null=False, blank=False)
    details = models.TextField(null=False, blank=False)
    link    = models.URLField(verify_exists=True, max_length=200, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add = True)
    deleted = models.BooleanField()
    price = models.FloatField()
    user_created = models.ForeignKey(User)
    status = models.ForeignKey(SolicitationStatus)
    scraper = models.ForeignKey(Scraper, null=True, blank=True)

    objects = models.Manager()
    
    def has_bounty(self):
        return self.price > 0

    def total_price(self):
        total_price = 0
        if self.price > 0:
            bounty_charge = float(0)
            bounty_charge = (float(self.price) / 100) * settings.MARKET_BOUNTY_CHARGE
            total_price = float(self.price) + bounty_charge
        return total_price
        
        
    def save(self):

    #if a new solicitation, then set the status to 'new'
        if not self.pk:
            status = SolicitationStatus.objects.get(status='open')
            self.status = status

        super(Solicitation, self).save()

    def complete(self):
        #update status
        status = SolicitationStatus.objects.get(status='completed')
        self.status = status
        self.save()

        if self.has_bounty():
            #send an email to the team saying that money needs to be sent to the developer of the scraper
            template = loader.get_template('emails/send_bounty.txt')
            context = Context({
                'solicitation': self,
                'recipient_user': self.scraper.owner()
            })
            send_mail('Send Bounty', template.render(context), settings.EMAIL_FROM, [settings.TEAM_EMAIL], fail_silently=False)

        #send an email to scraper owner to tell them they have been accepted and if bounty to expect an email about payment
        template = loader.get_template('emails/bounty_accepted.txt')
        context = Context({
            'solicitation': self,
            'developer': self.scraper.owner()
        })
        send_mail('Your scraper has been accepted', template.render(context), settings.EMAIL_FROM, [self.scraper.owner().email], fail_silently=False)

    def reject(self):
        #send email to scraper owner to tell them they have been rejected
        template = loader.get_template('emails/bounty_rejected.txt')
        context = Context({
            'solicitation': self,
            'developer': self.scraper.owner()
        })
        send_mail('Your scraper has been rejected', template.render(context), settings.EMAIL_FROM, [self.scraper.owner().email], fail_silently=False)

        status = SolicitationStatus.objects.get(status='open')
        self.status = status
        self.scraper = None
        self.save()

    def claim(self, scraper, user):

        #set the scraper_id on the solicitation
        if scraper and user == scraper.owner():

            #set the status of the solicitation to 'pending'
            status = SolicitationStatus.objects.get(status='pending')
            self.status = status
            self.scraper = scraper

            #save the solicitation
            self.save()

            #if a bounty has been set, then generate an invoice (the invoice is used to mnanage the paypal payment)
            if self.price > 0:
                invoice = Invoice()
                invoice.title = "Scraper Bounty - " + self.title
                invoice.item_type = "solicitation"
                invoice.price = self.total_price()
                invoice.parent_id = self.pk
                invoice.user = self.user_created
                invoice.save()

            #email the creator telling them it is done, and to pay if nesesary
            title = "The scraper you requested for " + self.title + " has been written"
            template = loader.get_template('emails/market_claim.txt')
            context = Context({
                'scraper': scraper,
                'solicitation': self,
                'url': 'http://' + Site.objects.get_current().domain
            })
            send_mail(title, template.render(context), settings.EMAIL_FROM, [self.user_created.email], fail_silently=False)
        else:
            #someone is messing about if we are here, throw an exception
            raise Exception("Unable to find a scraper (for this user) to add to this solicitation")
   
    def __unicode__(self):
        return "%s (%s)" % (self.title, self.price)
    
    def content_type(self):
        return ContentType.objects.get(app_label="market", model="Solicitation")
    

#register tags
tagging.register(Solicitation)
