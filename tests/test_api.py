import unittest
import uuid, os, urllib, urllib2, re, datetime, time
import json, csv
from selenium import selenium
from selenium_test import SeleniumTest

class TestApi(SeleniumTest):
    
    populate_db_name = None
    
    user_name = None
    user_pass = None
    
    site_base = None
    api_base = None
    
    # Check attaching a database in datastore API
    # Check all apis for privacy leaking (i.e. _private_datastore_api)

    def test_datastore_api(self):
        self._get_api_base()
        self._setup_db()
        self._basic_datastore_api_query()
        
        
    def test_scraper_info_api(self):
        self._get_api_base()
        self._setup_db()
        self._scraperinfo_quietfields_test()
        #self._scraperinfo_date_test() 
        self._scraperinfo_version_test()
        
        
    def _scraperinfo_version_test(self):
        """ Make a small change in the code, save and check versions api works as expected """
        s = self.selenium
        populate_db_file = open(os.path.join( os.path.dirname( __file__ ), 'sample_data/populate_db_scraper.txt'))
        code = populate_db_file.read()
        html_code = code.replace('&','&amp').replace('<','&lt').replace('>','&gt').replace('\n', '<br>')
        populate_db_file.close()
        
        s.type_keys('//body[@class="editbox"]', "\16")
        s.wait_for_condition("selenium.browserbot.getCurrentWindow().document.getElementById('btnCommitPopup').disabled == false", 10000)
        s.type('//body[@class="editbox"]', "%s" % (html_code + '# A change'))
        s.click('btnCommitPopup')

        json = self._get_info(self.populate_db_name)
        self.failUnless(json[0]['code'] == code + '# A change')
        json = self._get_info(self.populate_db_name, version='-1')
        self.failUnless(json[0]['code'] == code + '# A change')
        json = self._get_info(self.populate_db_name, version='0')
        self.failUnless(json[0]['code'] == code)
        
        
    # WAITING ON THE CODEMIRROR 'RUN' BUTTON TO GENERATE A RUN EVENT
    ##def _scraperinfo_date_test(self):
    ##    """ Check that scraper info correctly filters run events """
    ##    # Arbitrary date in the future
    ##    futuredate = str(datetime.date.fromtimestamp(time.time()+1000000).isoformat())
    ##    # Check a future date filter returns no run events and that one is returned by default
    ##    checks = [{'json':self._get_info(self.populate_db_name, history_start_date=futuredate), 'results':0 },
    ##              {'json':self._get_info(self.populate_db_name),                                'results':1 }]
    ##              
    ##    for check in checks:
    ##        json = check['json']
    ##        self.failUnless(len(json[0]['runevents']) == check['results']


    def _scraperinfo_quietfields_test(self):
        """ Check scraper info response fields are as expected """
        always_fields = ['license','description','language','title','tags','short_name','created','records','filemodifieddate',
                         'wiki_type','privacy_status','attachable_here','attachables','modifiedcommitdifference']
        fields = ['code','runevents','datasummary','userroles','history','prevcommit']
        
        # Check trying to make all fields quiet leaves irremovable ones alone, and that all fields are present by default
        checks = [{'json':self._get_info(self.populate_db_name, quietfields='|'.join(always_fields+fields)), 'keys':always_fields[:]     },
                  {'json':self._get_info(self.populate_db_name),                                             'keys':always_fields+fields }]
        
        for check in checks:
            json = check['json']
            keys = check['keys']
            for key in json[0].keys():
                keys.remove(key)
            self.failUnless(keys == [])
            self.failUnless(json[0]['short_name'] ==self.populate_db_name)
        
        
    def _basic_datastore_api_query(self):
        """ Basic tests on parameters of datastore api queries """
        # Check download of sqlite file
        sqlite_file = urllib2.urlopen(self.site_base + "scrapers/export_sqlite/%s/" % self.populate_db_name)
        self.failUnless(int(sqlite_file.headers.dict['content-length']) > 0)
        self.failUnless(sqlite_file.headers.dict['content-type'] == 'application/octet-stream')
        self.failUnless(sqlite_file.headers.dict['content-disposition'] == 'attachment; filename=%s.sqlite' % self.populate_db_name)
        
        # Perform common tests on different types of api output formats
        self._datastore_api_response_check('jsondict')
        self._datastore_api_response_check('jsonlist')
        self._datastore_api_response_check('csv')
        self._datastore_api_response_check('htmltable')

        # RSS uses very different queries because of required column names
        rss2_response = self._get_data(type='rss2', scraper=self.populate_db_name, content_type='application/rss+xml; charset=utf-8',
                                        query="select a as title, b as link, c as description, d as guid, datetime(julianday('now'+key)) as pubDate from swdata limit 20").read()
        rss2_vals = re.findall('<item><title>[a-z0-9\-]*</title><link>[a-z0-9\-]*</link><description>[a-z0-9\-]*</description>' + 
                               '<guid isPermaLink="true">[a-z0-9\-]*</guid><(?:pubDate)|(?:date)>[a-z0-9\-]*</(?:pubDate)|(?:date)></item>', rss2_response)
        self.failUnless(len(rss2_vals)==20)
        rss2_response = self._get_data(type='rss2', scraper=self.populate_db_name, content_type='application/rss+xml; charset=utf-8',
                                        query="select a as title, b as link, c as description, datetime(julianday('now'+key)) as date from swdata limit 6").read()
        rss2_vals = re.findall('<item><title>[a-z0-9\-]*</title><link>[a-z0-9\-]*</link><description>[a-z0-9\-]*</description>' + 
                               '<guid isPermaLink="true">[a-z0-9\-]*</guid><(?:pubDate)|(?:date)>[a-z0-9\-]*</(?:pubDate)|(?:date)></item>', rss2_response)
        self.failUnless(len(rss2_vals)==6)  
        
        
    ##def _private_datastore_api(self):
    ##    """ Check that private scrapers behave as expected """
    ##    self.set_code_privacy("private", "scraper", self.populate_db_name, {'username':user_name,'password':user_pass})
    ##    
    ##    # Check sqlite download
    ##    # SHOULD ERROR
    ##    sqlite_file = urllib2.urlopen(self.site_base + "scrapers/export_sqlite/%s/" % self.populate_db_name)
    ##    self.failUnless(sqlite_file.headers.dict['content-type'] == 'application/octet-stream')
    ##    
    ##    # Check sql query json
    ##    # SHOULD ERROR
    ##    response = urllib2.urlopen(self.api_base + "datastore/sqlite?" + 
    ##                                urllib.urlencode({"format":"jsondict","name":self.populate_db_name,"query":"select * from swdata"}))
    ##    self.failUnless(sqlite_file.headers.dict['content-type'] == 'application/json; charset=utf-8')
    ##    
    ##    # Attach DB privacy
    ##    # Scraper info fields
    ##    # Directly using private scraper name in the API

        
    def _datastore_api_response_check(self, format):
        """ Get some data from the datastore api and check the response is as expected """
        # Format specific information
        format_dict = { 
                        "jsondict":{  'content_type':'application/json; charset=utf-8',   'load':(lambda r:json.loads(r.read())), 
                                      'keys':(lambda v:v[0]),                             'num_results':(lambda v:len(v))            }, 
                        "jsonlist":{  'content_type':'application/json; charset=utf-8',   'load':(lambda r:json.loads(r.read())), 
                                      'keys':(lambda v:v['keys']),                        'num_results':(lambda v:len(v['data']))    },
                        "csv":{       'content_type':'text/csv',                          'load':(lambda r:csv.DictReader(r)), 
                                      'keys':(lambda v:v.fieldnames),                     'num_results':(lambda v:len(list(v)))      },
                        "htmltable":{ 'content_type':'text/html',                         'load':(lambda r:r.read()), 
                                      'keys':(lambda v:re.findall("<th>(.*?)</th>",v)),   'num_results':(lambda v:v.count('<tr>')-1) }
                      }
        # Values as expected from the loaded script in _setup_db
        keys = ['key','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        limit_keys = ['key','1','2']
        records = 20
        limit_records = 6
        # Perform a test for each set of values in the list below
        query_expected_records =[("select * from swdata", records, keys), 
                                ("select key, a as '1', b as '2' from swdata limit " + str(limit_records), limit_records, limit_keys)]
        
        for item in query_expected_records:
            # Load the raw api response
            response = self._get_data(type=format, scraper=self.populate_db_name, content_type=format_dict[format]['content_type'], query=item[0])
            # Load the response into a format-specific structure
            vals = format_dict[format]['load'](response)
            # Check the number of rows returned is as expected
            self.failUnless(format_dict[format]['num_results'](vals) == item[1])
            # Verify the column names are correct
            for key in format_dict[format]['keys'](vals):
                item[2].remove(key)
            self.failUnless(item[2] == [])
            
            
    def _get_data(self, type, scraper, content_type, query):
        """ Send a post request to the datastore api and return a response object """
        params = {
                    "format" : type,
                    "name": scraper,
                    "query" : query
                 }
        response = urllib2.urlopen(self.api_base + "datastore/sqlite?" + urllib.urlencode(params))
        # Check the content types and possibly content disposition
        if type == "jsondict" or type == "jsonlist":
            self.failUnless(response.headers.dict['content-disposition'] == "attachment; filename=" + scraper + ".json" )
        elif type == "csv":
            self.failUnless(response.headers.dict['content-disposition'] == "attachment; filename=" + scraper + ".csv" )
        self.failUnless(response.headers.dict['content-type'] == content_type)
        return response
        
        
    def _get_info(self, scraper, version="-1", history_start_date="", quietfields=""):
        """ Send a post request to the scraper info api and return json """
        params = {
                    "name" : scraper,
                    "version" : version,
                    "history_start_date": history_start_date,
                    "quietfields" : quietfields
                 }
        for param in params.keys():
            if not params[param]:
                del(params[param])
        response = urllib2.urlopen(self.api_base + "scraper/getinfo?" + urllib.urlencode(params))
        self.failUnless(response.headers.dict['content-disposition'] == "attachment; filename=scraperinfo.json" )
        self.failUnless(response.headers.dict['content-type'] == 'application/json; charset=utf-8')
        return json.loads(response.read())
        
    
    def _get_api_base(self):
        """ Get url of main site and apis """
        s = self.selenium
        
        s.open("/")
        self.wait_for_page()
        self.site_base = s.get_location()

        s.open("/docs/api#sqlite")
        self.wait_for_page()
        html = s.get_html_source()
        self.api_base = re.search('id="id_api_base" value="(?P<api_base>http[s]?://[^"]*)', html).group('api_base')
        
    
    def _setup_db(self):
        """ Initial setup of a sample scraper for querying in the API """
        s = self.selenium
        s.open("/")
        self.wait_for_page()
        
        populate_db_file = open(os.path.join( os.path.dirname( __file__ ), 'sample_data/populate_db_scraper.txt'))
        populate_db_code = populate_db_file.read().replace('&','&amp').replace('<','&lt').replace('>','&gt').replace('\n', '<br>')
        populate_db_file.close()
        
        self.user_pass = str( uuid.uuid4() )[:18].replace('-', '_')
        self.user_name = self.create_user(name="test user", password = self.user_pass)
        
        self.populate_db_name = self.create_code("python", code_type='scraper', code_source=populate_db_code)
        
        # Assume scraper run will be successful, only do basic completion checking
        run_enabled = "selenium.browserbot.getCurrentWindow().document.getElementById('run').disabled == false"
        s.wait_for_condition(run_enabled, 10000)
        s.click('run')
        time = 20
        while not (s.is_text_present('Starting run ...') and s.is_text_present('runfinished')):
            if time == 0:
                self.fail()
            time = time -1
        if not self.selenium.is_text_present('seconds elapsed'):
            self.fail()