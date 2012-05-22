from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def alert_vault_members_of_exceptions(vault):
    result = []

    context = locals()
    subject ='Script errors in your %s ScraperWiki vault' % vault.name
    def select_exceptions_that_have_not_been_notified(member):
        return [{'scraper_name': 'Test', 'short_name': 'test',
            'exception_message': 'LOIOError (Basdiusfu)'},
         {'scraper_name': 'HAHAHA', 'short_name': 'hahaha',
          'exception_message': 'sdfsdfsdf'}]

    for member in vault.members.all():
        context['exceptions'] = select_exceptions_that_have_not_been_notified(member)

        text_content = render_to_string('emails/vault_exceptions.txt', context) 
        html_content = render_to_string('emails/vault_exceptions.html', context)

        msg = EmailMultiAlternatives(subject, text_content,
            'ScraperWiki Alerts <noreply@scraperwiki.com>', to=[member.email])
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send(fail_silently=False)
            result.append({
                'recipient': member.email,
                'status': 'okay'
            })
            #set notified flag for all runevents
        except EnvironmentError as e:
            result.append({
                'recipient': member.email,
                'status' : 'fail',
                'error' : "Couldn't send email",
            })
 
    return result
