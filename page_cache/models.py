from django.db import models

# models to define cached pages and to connect them to scraper invocations.
class CachedPage(models.Model):
    """
        This records the information used to request a page, along with the content that was retrieved
        and when this was done.

        PRM: Don't know whether content should be a TextField or an XmlField.
    """
    url          = models.URLField()
    method       = models.CharField(max_length = 1) # 'P' = Post, 'G' = Get.
    post_data    = models.CharField(max_length = 1000)
    cached_at    = models.DateTimeField(auto_now_add = True)
    time_to_live = models.IntegerField() # number of seconds after 'cached_at' for which this is fald
    content      = models.TextField()

