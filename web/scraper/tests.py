"""
At the moment, this only tests some scraper.views
"""

from django.test import TestCase

__test__ = {"doctest": """
    >>> from django.test import Client
    >>> import datetime
    >>> from django.core.urlresolvers import reverse
    >>> client = Client()
    
    
    >>> response = client.get(reverse('scraper_list'))
    >>> response.status_code
    200
    >>> response = client.get(reverse('scraper_create'))
    >>> response.status_code
    200
"""}

