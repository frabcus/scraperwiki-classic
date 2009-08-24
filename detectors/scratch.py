# Every 5 seconds

from scraperutils import ScrapeURL, SaveScraping, FetchCorrectedText, FetchNames
from scraperutils import CreateScopeUser, PostData

import sys, re

    
    
scraper_tag = "partydonations"

user_name = "goatchurch"
user_password = "garfield"
user_email = "julian@goatchurch.org.uk"

import urllib
import re
import datetime
import sys

CreateScopeUser(user_name, user_password, user_email) # run once

if "scrape" in sys.argv:
    registerofdonationsurl = "http://registers.electoralcommission.org.uk/regulatory-issues/regdpoliticalparties.cfm"
    text = ScrapeURL(url=registerofdonationsurl)
    SaveScraping(scraper_tag=scraper_tag, name="registerofdonations", url=registerofdonationsurl, text=text)


if "parse" in sys.argv:
    print "lo there\n"*8
    sys.exit(0);

if "cron" in sys.argv:
    print "heee there\n"*8
    sys.exit(0);
    
