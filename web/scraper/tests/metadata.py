from django.test import TestCase
from django.core.urlresolvers import reverse

from scraper.models import Scraper, ScraperMetadata

try:
    import json
except:
    import simplejson as json

class MetadataTest(TestCase):
    def setUp(self):
        self.scraper = Scraper(title="Test")
        self.scraper.save()

        self.metadata = ScraperMetadata()
        self.metadata.name = "age"
        self.metadata.scraper = self.scraper
        self.metadata.run_id = 0
        self.metadata.value = 32
        self.metadata.save()

    def get_metadata_value(self, response):
        metadata = json.loads(response.content)
        return json.loads(metadata['value'])

class MetadataReadTest(MetadataTest):
    def test_access_not_through_proxy(self):
        resp = self.client.get(reverse('metadata_api', args=[self.scraper.guid, 'title']), {})
        self.assertEquals(401, resp.status_code)

    def test_getting_title_or_short_name(self):
        resp = self.client.get(reverse('metadata_api', args=[self.scraper.guid, 'title']), {}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(self.scraper.title, self.get_metadata_value(resp))

        resp = self.client.get(reverse('metadata_api', args=[self.scraper.guid, 'short_name']), {}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(self.scraper.short_name, self.get_metadata_value(resp))

    def test_read(self):
        resp = self.client.get(reverse('metadata_api', args=[self.scraper.guid, 'age']), {}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(self.metadata.value, self.get_metadata_value(resp))

    def test_absent_metadata(self):
        resp = self.client.get(reverse('metadata_api', args=[self.scraper.guid, 'absent']), {}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(410, resp.status_code)

    def test_absent_scraper(self):
        resp = self.client.get(reverse('metadata_api', args=['absent', 'absent']), {}, HTTP_X_SCRAPERID='absent')
        self.assertEquals(410, resp.status_code)

class MetadataCreateTest(MetadataTest):
    def test_missing_run_id_or_value(self):
        resp = self.client.post(reverse('metadata_api', args=[self.scraper.guid, 'new']), {'value': 'AAA'}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(400, resp.status_code)

        resp = self.client.post(reverse('metadata_api', args=[self.scraper.guid, 'new']), {'run_id': 0}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(400, resp.status_code)

    def test_absent_scraper(self):
        resp = self.client.post(reverse('metadata_api', args=['absent', 'new']), {'value': 'BBB', 'run_id': 0}, HTTP_X_SCRAPERID='absent')
        self.assertEquals(410, resp.status_code)

    def test_duplicate_entry(self):
        resp = self.client.post(reverse('metadata_api', args=[self.scraper.guid, 'age']), {'value': 'CCC', 'run_id': 0}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(409, resp.status_code)

    def test_create(self):
        resp = self.client.post(reverse('metadata_api', args=[self.scraper.guid, 'new']), {'value': json.dumps('DDD'), 'run_id': 0}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(200, resp.status_code)

        resp = self.client.get(reverse('metadata_api', args=[self.scraper.guid, 'new']), {}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals('DDD', self.get_metadata_value(resp))

class MetadataUpdateTest(MetadataTest):
    def test_missing_run_id_or_value(self):
        resp = self.client.put(reverse('metadata_api', args=[self.scraper.guid, 'new']), {'value': 'EEE'}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(400, resp.status_code)

        resp = self.client.put(reverse('metadata_api', args=[self.scraper.guid, 'new']), {'run_id': 0}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(400, resp.status_code)

    def test_absent_scraper(self):
        resp = self.client.put(reverse('metadata_api', args=['absent', 'new']), {'value': 'FFF', 'run_id': 0}, HTTP_X_SCRAPERID='absent')
        self.assertEquals(410, resp.status_code)

    def test_absent_metadata(self):
        resp = self.client.put(reverse('metadata_api', args=[self.scraper.guid, 'new']), {'value': 'GGG', 'run_id': 0}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(410, resp.status_code)

    def test_update(self):
        resp = self.client.put(reverse('metadata_api', args=[self.scraper.guid, 'age']), {'value': json.dumps(99), 'run_id': 0}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(200, resp.status_code)

        resp = self.client.get(reverse('metadata_api', args=[self.scraper.guid, 'age']), {}, HTTP_X_SCRAPERID=self.scraper.guid)
        self.assertEquals(99, self.get_metadata_value(resp))
