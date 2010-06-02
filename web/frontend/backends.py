from registration.backends.default import DefaultBackend

class UserWithNameBackend(DefaultBackend):
    def register(self, request, **kwargs):
        user = super(UserWithNameBackend, self).register(request, **kwargs)
        profile = user.get_profile()
        profile.name = kwargs['name']
        profile.save()
        return user
