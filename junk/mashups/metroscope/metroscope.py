import sys
import wx
import os
import webbrowser
import datetime
import time
import random
import re
from optparse import OptionParser

from metropot import MessagePot


parser = OptionParser()
parser.set_usage("""

Metroscope
  animated display of news from your local area sourced from a variety
  of feeds, including links that open in your browser.
""")


parser.add_option("--feed", dest="feed", metavar="feed", default="local",
                  help="defaults to 'local', but can be set to 'journalisted'")
parser.add_option("--postcode",
                  dest="postcode", metavar="postcode", default="l17ay",
                  help="Over-rides the postcode centre where possible (default is Liverpool)")
parser.add_option("--quiet", action="store_true", dest="quiet", default=False,
                  help="stops all printing of messages")

(options, args) = parser.parse_args()

framesize_start = (800, 160)
summaryframewidth = 200
messagegap = 22
scrollpixels = 7
minnummessages = 5
mousewheelscrollpixels = 90
frametime_microseconds = 33
timetokeepmessageopen = 8.0

# maybe we want more than one row of messages
backcolours = {
        "theyworkforyou": (220, 250, 230),
        "ononemap":(190, 130, 170),
        "planningalert":(210, 160, 190),
        "fixmystreet":(230, 150, 170),
        "pledgebank":(230, 150, 230),
        "groupsnearyou":(180, 220, 200),
        "topix":(202, 210, 255),
            }
backcoloursvalues = backcolours.values()


class DerTimer(wx.Timer):
    def __init__(self, frame, microseconds):
        wx.Timer.__init__(self)
        self.frame = frame
        frame.dertimer = self
        self.Start(microseconds)
    def Notify(self):  self.frame.Notify()


class MovingMessage:
    def __init__(self, frame):
        self.frame = frame
        self.spanel = wx.Panel(frame, wx.ID_ANY, style=wx.SIMPLE_BORDER)
        self.stext = wx.StaticText(self.spanel, wx.ID_ANY, label="ssssssssssNone")
        self.stext.SetFont(wx.Font(12, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.spanel.Bind(wx.EVT_ENTER_WINDOW, self.mouseenter)  # this doesn't work
        self.spanel.Bind(wx.EVT_LEAVE_WINDOW, self.mouseexit)   # this doesn't work
        self.stext.Bind(wx.EVT_LEFT_DOWN, self.mouseleftdown)
        self.stext.Bind(wx.EVT_LEFT_UP, self.mouseleftup)

    def SetMessage(self, smessage, stip, surl, sfeedname):
        self.smessage = smessage
        self.surl = surl
        self.stip = stip
        self.sfeedname = sfeedname

        self.stext.SetLabel(smessage)
        self.stextsize = self.stext.GetSize()
        self.stextsize = (self.stextsize[0] + 2, self.stextsize[1] + 2)

        self.foregroundcolour = (0, 0, 190)
        if sfeedname == "journalisted":
            self.backgroundcolour = backcoloursvalues[int(random.uniform(0, len(backcoloursvalues)))]
        else:
            self.backgroundcolour = backcolours.get(sfeedname, (220, 220, 250))

        self.stext.SetBackgroundColour(self.backgroundcolour)
        self.stext.SetForegroundColour(self.foregroundcolour)

        self.spanelwidth = 0
        self.spanelheight = self.stextsize[1]
        self.spanel.SetSize((0, 0))

    def SetSummaryMessage(self, movingmessage, framesize):
        self.smessage = movingmessage.stip
        self.surl = movingmessage.surl
        self.stip = None
        self.stext.SetLabel(movingmessage.stip)
        self.stext.SetSize((summaryframewidth, framesize[1]))
        self.stextsize = self.stext.GetSize()
        print "summess size", self.stextsize
        self.stext.SetBackgroundColour((220, 250, 220))
        self.stext.SetForegroundColour((11, 111, 19))
        self.spanel.MoveXY(framesize[0] - summaryframewidth, 0)
        self.spanel.SetSize(self.stext.GetSize())

    def ClearSummaryMessage(self):
        self.spanel.SetSize((0, 0))


    def OverlappingMessage(self, omessage):
        if self.posx > omessage.posx + omessage.stextsize[0]:
            return False
        if omessage.posx > self.posx + self.stextsize[0]:
            return False
        if self.posy > omessage.posy + omessage.stextsize[1]:
            return False
        if omessage.posy > self.posy + self.stextsize[1]:
            return False
        return True

    def ScrollOpen(self):
        if self.spanelwidth >= self.stextsize[0]:
            return True
        self.spanelwidth = min(self.stextsize[0], self.spanelwidth + scrollpixels)
        self.spanel.SetSize((self.spanelwidth, self.spanelheight))
        return False

    def ScrollClosed(self):
        if self.spanelheight == 0:
            return True
        self.spanelheight = max(0, self.spanelheight - 1)
        self.spanel.SetSize((self.spanelwidth, self.spanelheight))
        return False

    # these don't work
    def mouseenter(self, evt):
        self.frame.inmovingmessage = self
        self.frame.inmovingmessage_since = 0
        if self.surl:
            self.stext.SetBackgroundColour((155, 255, 160))
            self.spanel.Refresh()

            #frame.helpprovider.ShowHelp(self.spanel)

    def mouseexit(self, evt):
        self.frame.inmovingmessage = None
        if self.surl:
            self.stext.SetBackgroundColour(self.backgroundcolour)
            self.spanel.Refresh()

    def mouseleftdown(self, evt):
        if self.surl:
            self.foregroundcolour = (225, 16, 16)
            self.stext.SetForegroundColour(self.foregroundcolour)
            #print "LinkTo:", self.smessage
            self.spanel.Refresh()
            #print "iiii", self.stip.encode("ascii", "ignore")
            webbrowser.open(self.surl)

    def mouseleftup(self, evt):
        pass #print "Up LinkTo:", self.smessage



# key and mouse events not working
class MetroScrollPanel(wx.Panel):
    def mainpanel_leave(self, evt):  self.bmainpanel_mousein = False
    def mainpanel_getfocus(self, evt):  self.bmainpanel_focus = True
    def mainpanel_losefocus(self, evt):  self.bmainpanel_focus = False
    def mousewheelscroll(self, evt):
        #self.ScrollAllLeft(evt.GetWheelRotation() < 0 and mousewheelscrollpixels or -mousewheelscrollpixels)
        print "kkkkk", evt.GetWheelRotation()
    def resizewindow(self, evt):  self.framesize = self.GetSize()

    def mainpanel_enter(self, evt):
        self.bmainpanel_mousein = True;

    def keydown(self, evt):
        keycode = evt.GetKeyCode()
        print "kkkkk", self.Dname, keycode
        if keycode == wx.WXK_RIGHT:
            self.AdvanceAll()
        #elif keycode == wx.WXK_LEFT:
        #    self.ScrollAllLeft(mousewheelscrollpixels)
        evt.Skip()


    def __init__(self, frame, messagepot):
        wx.Panel.__init__(self, frame, wx.ID_ANY, style=wx.SIMPLE_BORDER, size=(500, 30), pos=(5,5))

        self.bmainpanel_mousein = False
        self.bmainpanel_focus = True
        self.inmovingmessage = None
        self.inmovingmessage_since = 0

        self.timesincelastnew = 10.0

        self.SetAutoLayout(False)
        self.SetBackgroundColour((255, 255, 255))

        self.Bind(wx.EVT_ENTER_WINDOW, self.mainpanel_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.mainpanel_leave)
        self.Bind(wx.EVT_SET_FOCUS, self.mainpanel_getfocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.mainpanel_losefocus)
        self.Bind(wx.EVT_MOUSEWHEEL, self.mousewheelscroll)
        self.Bind(wx.EVT_KEY_DOWN, self.keydown)
        self.Bind(wx.EVT_SIZE, self.resizewindow)

        self.messagepot = messagepot
        self.summarymessage = MovingMessage(self)
        self.summarymessage.ClearSummaryMessage()

        self.waitingmessages = [ ]
        self.workingmessages = [ ]
        self.sparemessages = [ ]
        self.bforcecontinueclosing = False

        self.nmessagesnumber = 0

        self.framesize = self.GetSize()
        self.scrollpixels = scrollpixels

        self.stexttip = None #wx.StaticText(self, wx.ID_ANY, style=wx.SIMPLE_BORDER, label="", size=(90, 40))
        self.timelast = time.time()

    def MakeNextMessage(self, nnews):
        nextmessage = (self.sparemessages and self.sparemessages.pop()) or MovingMessage(self)
        self.nmessagesnumber += 1

        smessage = nnews.GetMessage()
        #smessage = (nnews.surl and nnews.sdate) and "%s (%s)" % (nnews.smessage, nnews.TimeAgo()) or nnews.smessage
        nextmessage.SetMessage(smessage, nnews.stip, nnews.surl, nnews.feedname)
        nextmessage.nnews = nnews
        nextmessage.moperation = "waiting"
        return nextmessage

    def PositionMessage(self, message, framesize):
        xr = max(1, framesize[0] - message.stextsize[0] - summaryframewidth)
        yr = max(1, framesize[1] - message.stextsize[1])
        message.posx = int(random.uniform(0, xr))
        message.posy = int(random.uniform(0, yr))

        for omessage in self.workingmessages:
            if message.OverlappingMessage(omessage):
                return False

        message.spanel.MoveXY(message.posx, message.posy)
        return True


# queue next messages looking for a place for them to fit
# get the delay right
# allow for older messages to appear in the stack
# pop-up of the summary...
# it blows your mind

    def Notify(self):
        timenow = time.time()
        timepassedsincelastnotify = timenow - self.timelast
        self.timelast = timenow

        if self.bmainpanel_focus and not self.bmainpanel_mousein and not self.inmovingmessage:
            self.timesincelastnew += timepassedsincelastnotify
            baddnewmessages = (self.timesincelastnew > 2.5)
        else:
            baddnewmessages = (len(self.workingmessages) < minnummessages and len(self.waitingmessages) <= 3)

        if baddnewmessages:
            self.timesincelastnew = 0.0
            nnews = self.messagepot.NextMessage()
            nextmessage = self.MakeNextMessage(nnews)
            self.waitingmessages.append(nextmessage)

        for i in range(len(self.waitingmessages) - 1, -1, -1):
            message = self.waitingmessages[i]
            if self.PositionMessage(message, self.framesize):
                del self.waitingmessages[i]
                self.workingmessages.append(message)
                message.moperation = "opening"

        for i in range(len(self.workingmessages) - 1, -1, -1):
            message = self.workingmessages[i]

            if message.moperation == "opening":
                if message.ScrollOpen():
                    message.timeopen = 0
                    message.moperation = "open"
                    self.bforcecontinueclosing = False

            if message.moperation == "open":
                if self.bmainpanel_focus and not self.bmainpanel_mousein and not self.inmovingmessage:
                    message.timeopen += timepassedsincelastnotify
                    if message.timeopen > timetokeepmessageopen:  # seconds
                        message.moperation = "closing"

            if message.moperation == "closing":
                if (not self.bmainpanel_mousein and not self.inmovingmessage) or self.bforcecontinueclosing:
                    if message.ScrollClosed():
                        del self.workingmessages[i]
                        self.sparemessages.append(message)
                # reopen closing ones
                elif self.bmainpanel_focus and (self.bmainpanel_mousein or self.inmovingmessage):
                    print "reopening"
                    message.spanelheight = message.stextsize[1]
                    message.spanel.SetSize((message.spanelwidth, message.spanelheight))
                    message.timeopen = timetokeepmessageopen - random.uniform(0.2, 0.6)
                    message.moperation = "open"

        #if not self.stexttip:
        #    pass
        if self.inmovingmessage:
            self.inmovingmessage_since += 1
            if self.inmovingmessage_since == 10 and self.inmovingmessage.stip:
                #self.stexttip.SetLabel(self.inmovingmessage.stip)
                #self.stexttip.MoveXY(self.inmovingmessage.posx + 5, self.inmovingmessage.posy + 20)
                #self.stexttip.SetSize((90, 30))
                #print self.stexttip.GetSize(), self.inmovingmessage.stip, self.inmovingmessage.posx
                self.summarymessage.SetSummaryMessage(self.inmovingmessage, self.framesize)
                print "\n-- Summary for this is:\n\n", self.inmovingmessage.stip.encode("ascii", "ignore"), "\n\n"

        elif self.inmovingmessage_since:
            #self.stexttip.SetLabel("")
            if self.inmovingmessage_since:
                self.inmovingmessage_since = 0
                self.summarymessage.ClearSummaryMessage()

    def AdvanceAll(self):
        for message in self.workingmessages:
            message.moperation = "closing"
        self.bforcecontinueclosing = True

class MetroFrame(wx.Frame):
    def mainpanel_getfocus(self, evt):  self.bmainframe_focus = True
    def mainpanel_losefocus(self, evt):  self.bmainframe_focus = False

    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Metronews", size=framesize_start, pos=(400,200))
        self.messagepot = MessagePot(options.postcode, options.feed, options.quiet)
        self.mainpanel = MetroScrollPanel(self, self.messagepot)
        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.bmainframe_focus = True
        self.Centre()
        self.Show(True)

        DerTimer(self, frametime_microseconds)
        DerTimer(self.messagepot, 30000)

    def Notify(self):
        if self.bmainframe_focus:
            self.mainpanel.Notify()
            #self.mainpanel2.Notify()



if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = MetroFrame()
    app.MainLoop()



