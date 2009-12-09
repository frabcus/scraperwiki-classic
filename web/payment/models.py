from django.dispatch import Signal
from django.db import models
from django.contrib.auth.models import User
from paypal.standard.ipn.signals import payment_was_successful

payment_done = Signal()

def process_payment(sender, **kwargs):
    ipn = sender

    #find the invoice, raise an exception if it doesnt exist
    invoice = Invoice.objects.get(id=ipn.invoice, delete=False)
    if not invoice:
        raise Exception("Unable to find invoice for ID: " + ipn.invoice)

    #update the invoice to complete
    invoice.complete = True
    invoice.save()
    
    #TODO: save all details in a new transactions table

    #send a signal
    payment_done.send(invoice)

#pickup PayPal signals
payment_was_successful.connect(process_payment)

class Invoice(models.Model):
    """
        Things that can be paid for. parent id might be a user or solicitation etc
    """
    title   = models.CharField(max_length = 100, null=False, blank=False)
    item_type = models.CharField(max_length = 50, null=False, blank=False)
    price = models.IntegerField(null=True, blank=True)
    parent_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    user = models.ForeignKey(User)
    deleted = models.BooleanField()
    complete = models.BooleanField()
