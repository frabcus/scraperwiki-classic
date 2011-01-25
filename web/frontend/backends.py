from registration.backends.default import DefaultBackend
from codewiki.models import Scraper, UserCodeRole

class UserWithNameBackend(DefaultBackend):
    def register(self, request, **kwargs):
        user = super(UserWithNameBackend, self).register(request, **kwargs)
        profile = user.get_profile()
        profile.name = kwargs['name']
        profile.save()

        Scraper.objects.create_emailer_for_user(user)

        return user
