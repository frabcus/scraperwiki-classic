import sys
import os
import datetime
import re
import random
import urllib

now = datetime.datetime.now()

class LinkedMessage:
    def __init__(self, smessage, stip, surl, sdate, feedname):
        self.smessage = smessage
        self.stip = stip
        self.surl = surl
        self.sdate = sdate
        self.feedname = feedname

    def GetMessage(self):
        if self.feedname == "planningalert":
            return "Plan: " + self.smessage
        if self.feedname == "pledgebank":
            return "Pledge: " + self.smessage
        if self.feedname == "fixmystreet":
            return "Broken: " + self.smessage
        if self.feedname == "theyworkforyou":
            return "MP: " + re.sub("(?:\[[^\]]*\]|Orders of the day)[\s\-:]*", "", self.smessage) # clear up mess in TWFY titles
        if self.feedname == "ononemap":
            return "House: " + re.sub("\[[^\]]*\][\s\-]*", "", self.smessage)
        return self.smessage

    def TimeAgo(self):
        timeago = datetime.datetime.now() - self.sdate
        hours = timeago.seconds / 3600
        minutes = timeago.seconds / 60 - hours * 60
        if timeago.days:
            if timeago.days < 5:
                return "%d days, %d hours ago" % (timeago.days, hours)
            if timeago.days < 60:
                return "%d days ago" % timeago.days
            months = timeago.days / 28
            return "%d months ago" % months
        if hours == 0:
            return "%d minutes ago" % minutes
        if hours < 3:
            return "%d hours, %d minutes ago" % (hours, minutes)
        return "%d hours ago" % hours

class MessagePot:
    def __init__(self, postcode, feed, bquiet):
        self.nonewsmessage = LinkedMessage("No news yet", "for real", "http://www.freesteel.co.uk/cgi-bin/hackday/hackdaydb.py", None, "")
        self.placeholdermessage = LinkedMessage("*", "", None, None, "")
        self.feed = feed
        self.bquiet = bquiet

        self.newmessages = [ ]
        self.usedmessages = [ ]
        self.headlinekeys = set()
        self.fetchnum = 0

        self.GetMoreMessages()
        self.GetMoreMessages()
        self.GetMoreMessages()
        self.GetMoreMessages()

    def GetMoreMessages(self):
        if len(self.newmessages) > 20:
            return

        fin = urllib.urlopen("http://www.freesteel.co.uk/cgi-bin/hackday/hackdaydb.py?f=999")
        ftext = fin.read()
        fin.close()
        for s in re.findall("\n\S+\t\S+\t\S+\t\S+\t\S+\t(.*)", ftext):
            self.newmessages.append(LinkedMessage(s, "", "", None, "fixmystreet"))

    def Notify(self):
        self.GetMoreMessages()

    def NextMessage(self):
        if not self.newmessages:
            return self.nonewsmessage
        isw = int(random.uniform(0, len(self.newmessages)))
        res = self.newmessages.pop(isw)
        self.usedmessages.append(res)
        return res



