from django.template.defaultfilters import slugify

def SlugifyUniquely(value, model, slugfield="slug", instance=None):
    """
    Taken from: http://code.djangoproject.com/wiki/SlugifyUniquely
    
    Returns a slug on a name which is unique within a model's table

    This code suffers a race condition between when a unique
    slug is determined and when the object with that slug is saved.
    It's also not exactly database friendly if there is a high
    likelyhood of common slugs being attempted.

    A good usage pattern for this code would be to add a custom save()
    method to a model with a slug field along the lines of:

            from django.template.defaultfilters import slugify

            def save(self):
                if not self.id:
                    # replace self.name with your prepopulate_from field
                    self.slug = SlugifyUniquely(self.name, self.__class__)
            super(self.__class__, self).save()

    Original pattern discussed at
    http://www.b-list.org/weblog/2006/11/02/django-tips-auto-populated-fields
    """
    suffix = 0
    max_length = model._meta.get_field(slugfield).max_length
    potential = base = slugify(value)[:max_length]
    while True:
        if suffix:
            prefix = base[:max_length - (len(str(suffix)) + 1)]
            if prefix[-1] == '-': # remove trailing - so we don't get -- in the slug
                prefix = prefix[:-1]

            potential = "-".join([prefix, str(suffix)])

        matches = model.objects.filter(**{slugfield: potential})
        if matches.count() == 0 or (instance and matches[0].pk == instance.pk):
            return potential

        # we hit a conflicting slug, so bump the suffix & try again
        suffix += 1

