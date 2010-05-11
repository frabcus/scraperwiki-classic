class ScraperAuth(object):
    """
    Check to make sure the scraper accessing the API and the
    scraper whos metadata is being accessed are the same
    """
    def is_authenticated(self, request):
        # TODO check that the scrapers are the same and return True or False
        # or add the scraper id to the request and let the handler check later
        return True
