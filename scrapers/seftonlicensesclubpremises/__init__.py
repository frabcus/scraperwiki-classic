import mechanize
from scraperutils import SaveScraping
import re
from codewiki.models import ScraperModule

def ss(d):
    return re.sub("<", "&lt;", str(d))

def Scrape():
    br = mechanize.Browser()

    # front page that lets you select three different licensing types and has buttons instead of links    
    url = "http://www.sefton.gov.uk/Default.aspx?page=7801"
    br.open(url)
    ff = list(br.forms())[0]
    rr = ff.click(name="Template$ctl10$ctl00$BtnPremLic")
    br.open(url, rr.get_data())
    #SaveScraping(scraper_tag="seftonlicensesclub", name="formpagegeneral", url=url, text=br.response().read())

    # form that lets you narrow the search area and town, but which we can leave blank to get all
    ff2 = list(br.forms())[0]
    rr2 = ff2.click(name="Template$ctl10$ctl00$BtnSubmit")
    br.open(url, rr2.get_data())
    #SaveScraping(scraper_tag="seftonlicensesclub", name="formpagegeneralG", url=url, text=br.response().read())

    # there are 30 pages. get each one using the index buttons at the bottom
    ffi = list(br.forms())[0]
    for i in range(0, 1):
        name = "Template$ctl10$ctl00$RepeaterPageNo$ctl%02d$BtnPageNo" % i
        rri = ffi.click(name=name)    
        br.open(url, rri.get_data())
        reading = SaveScraping(scraper_tag="seftonlicenseclubP", name="page %02d" % i, url=url, text=br.response().read())
        print ss(reading.soup().table.findAll("tr"))
    
    # <input type="submit" name="Template$ctl10$ctl00$RepeaterPageNo$ctl19$BtnPageNo" value="20" id="Template_ctl10_ctl00_RepeaterPageNo_ctl19_BtnPageNo" title="Page 20" class="btnpage" onmouseover="hov(this,'btnpagehov')" onmouseout="hov(this,'btnpage')" onfocus="hov(this,'btnpagehov')" onblur="hov(this,'btnpage')" />



def DoesApply(reading):
    return reading.scraper_tag == "seftonlicensegneral"

def Parse(reading):
    # get all the rows from the table in the page that contains the license applications
    rows = reading.soup().table.findAll("tr")
    
    # get the column headings: ['Ref No', 'Premise Name', 'Address', 'Licence', 'Licence Issue Date', 'Licence Expiry Date']
    cols = [ td.string  for td in rows[0].findAll("td") ]

    res = [ ]

    # zip the values in the fields against the headings and put into the result
    for row in rows[1:]:
        vals = [ td.string  for td in row.findAll("td") ]
        res.append(dict(zip(cols, vals)))  # very terse this

    return res

def Collect():
    pass


def Observe(tailurl):
    scrapermodule = ScraperModule.objects.get(modulename="seftonlicenses")
    alllicenses = [ ]
    for detection in scrapermodule.detection_set.filter(status="parsed"):
        alllicenses.extend(detection.contents())  
    
    cols = ['Licence', 'Premise Name', 'Address' ]
    alllicenses.sort(key=lambda x: x.get('Licence'))
    print "<table>"
    for ll in alllicenses:
        print "<tr>"
        for col in cols:
            print "<td>%s</td>" % ll.get(col)
        print "</tr>"
    print "</table>"       
                 
