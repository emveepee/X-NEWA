from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
#
#  xnewa for XBMC
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
from builtins import str
from past.utils import old_div
import os
import sys

import xbmc
import xbmcgui
from xbmcaddon import Addon

from XNEWAGlobals import *
from XNEWA_Connect import XNEWA_Connect
from XNEWA_Settings import XNEWA_Settings
from fix_utf8 import smartUTF8

__language__ = Addon('script.kodi.knew4v5').getLocalizedString

# =============================================================================
class HomeWindow(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.win = None
        self.busy = False
        #self.progressDialog = None
        #self.settings = XNEWA_Settings()
        #self.xnewa = XNEWA_Connect(settings=self.settings)
        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']
        self.offline = self.xnewa.offline
        self.getChannels = True
        self.returnvalue = None

    def onFocus(self, controlId):
        pass

    def onInit(self):

        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.recentListBox = self.getControl(249)
            self.comingListBox = self.getControl(248)
            self.spaceGreen = self.getControl(247)
            self.spaceRed = self.getControl(246)
            self.spaceFree = self.getControl(245)
            self.spaceUsed = self.getControl(244)
            self.countPending = self.getControl(243)
            self.countProgress = self.getControl(242)
            self.countAvailable = self.getControl(241)
            self.countFailed = self.getControl(240)
            self.countConflict = self.getControl(239)
            self.countSeason = self.getControl(238)
            try:
                self.spacePercent = self.getControl(237)
                self.includePercentages = True
            except RuntimeError:
                self.includePercentages = False
            if self.settings.XNEWA_READONLY == True:
                self.win.setProperty('readonly', 'true')
                print('invisible')

            # button ids -> funtion ptr
            self.dispatcher = {
                248 : self.goUpcomingDetails,
                249 : self.goRecentDetails,
                250 : self.goWatchRecordings,
                251 : self.goTvGuide,
                252 : self.goRecordingSchedules,
                253 : self.goUpcomingRecordings,
                254 : self.goSearch,
                256 : self.refreshButton,
                257 : self.goExit,
                258 : self.goRecentRecordings,
                259 : self.goOnline,
                260 : self.goNextPVR
            }
            self.winOnline()
            if self.offline == True:
                self.win.setProperty('offline', 'true')
            else:
                self.goOnline()

        else:
            self.refresh()
            if self.offline == True:
                self.win.setProperty('offline', 'true')

    def onAction(self, action):
        if action.getId() in (EXIT_SCRIPT) or action.getButtonCode() in EXIT_SCRIPT:
            self.closed = True
            self.close()

    def onClick(self, controlId):
        try:
            self.dispatcher[controlId]()
            if self.xnewa.changedRecordings:
                self.xnewa.cleanOldCache('guideListing-*.p')
                self.xnewa.cleanCache('*.p')
                self.xnewa.changedRecordings = False
                self.refreshOnInit()

        except KeyError:
            debug('onClick')

    def goSearch(self):
        from . import search
        mywin = search.SearchWindow('nextpvr_search.xml', WHERE_AM_I,self.settings.XNEWA_SKIN, settings=self.settings, xnewa=self.xnewa)
        mywin.doModal()

    def goExit(self):
        self.xnewa.cleanCoverCache()
        self.closed = True
        self.close()
        return

    def goOnline(self):
        self.refreshOnInit()
        if self.offline == False:
            self.win.setProperty('recent', 'true')
            self.win.setProperty('scheduled', 'true')
            self.win.setProperty('upcoming', 'true')
            self.win.setProperty('offline', 'false')
            xbmc.sleep(100)
            return
            try:
                self.getControl(999)
                self.win.setFocusId(999)
            except RuntimeError:
                self.win.setFocusId(251)

    def goRecentDetails(self):
        from . import details
        oid = self.recentData[self.recentListBox.getSelectedPosition()]['recording_oid']
        detailDialog = details.DetailDialog("nextpvr_recording_details.xml", WHERE_AM_I,self.settings.XNEWA_SKIN, settings=self.settings, xnewa=self.xnewa, oid=oid, type="R" )
        detailDialog.doModal()
        print(detailDialog.returnvalue)
        if detailDialog.shouldRefresh:
            #self.xnewa.changedRecordings = False
            #self.recentData = self.xnewa.getRecentRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW, 10)
            self.xnewa.cleanCache('*.p')
            self.refresh()

    def goUpcomingDetails(self):
        from . import details
        oid = self.upcomingData[self.comingListBox.getSelectedPosition()]['recording_oid']
        detailDialog = details.DetailDialog("nextpvr_recording_details.xml", WHERE_AM_I,self.settings.XNEWA_SKIN, settings=self.settings, xnewa=self.xnewa, oid=oid, type="R")
        detailDialog.doModal()
        if detailDialog.shouldRefresh:
            self.xnewa.cleanCache('*.p')
            self.refresh()

    def goTvGuide(self):
        from . import epg
        mywin = epg.EpgWindow('nextpvr_epg.xml', WHERE_AM_I,self.settings.XNEWA_SKIN, xnewa=self.xnewa, settings=self.settings)
        mywin.doModal()
        if self.xnewa.changedRecordings:
            self.xnewa.cleanOldCache('guideListing-*.p')
            self.xnewa.cleanCache('*.p')
            self.xnewa.changedRecordings = False
            self.refreshOnInit()


    def goWatchRecordings(self):
        xbmc.executebuiltin('XBMC.ActivateWindow(videos,tvshowtitles)')

    def goNextPVR(self):
        from . import emulate
        emulateWindow = emulate.EmulateWindow("nextpvr_emulate.xml", WHERE_AM_I,self.settings.XNEWA_SKIN, settings=self.settings, xnewa=self.xnewa)
        emulateWindow.doModal()


    def goRecordingSchedules(self):
        from . import schedules
        mywin = schedules.SchedulesWindow('nextpvr_schedules.xml', WHERE_AM_I,self.settings.XNEWA_SKIN, settings=self.settings, xnewa=self.xnewa)
        mywin.doModal()

    def goUpcomingRecordings(self):
        from . import upcoming
        mywin = upcoming.UpcomingRecordingsWindow('nextpvr_upcoming.xml', WHERE_AM_I,self.settings.XNEWA_SKIN, settings=self.settings, xnewa=self.xnewa)
        mywin.doModal()

    def goRecentRecordings(self):
        from . import recent
        mywin = recent.RecentRecordingsWindow('nextpvr_recent.xml', WHERE_AM_I,self.settings.XNEWA_SKIN, settings=self.settings, xnewa=self.xnewa)
        mywin.doModal()
        #if mywin.shouldRefresh:
        #    self.renderRecent()

    def goSettings(self):
        from . import settings
        mywin = settings.settingsDialog('nextpvr_settings.xml', WHERE_AM_I, settings=self.settings,xnewa=self.xnewa)
        mywin.doModal()
        if self.settings.Reload:
            print("Reloading")
            self.xnewa = XNEWA_Connect(settings=self.settings)
            if self.xnewa.offline == False:
                self.win.setProperty('recent', 'true')
                self.win.setProperty('scheduled', 'true')
                self.win.setProperty('upcoming', 'true')
            self.refreshButton()

    def refresh(self):
        self.renderStats()
        self.renderUpComing()
        self.renderRecent()


    def refreshButton(self):
        self.getChannels = True
        self.xnewa.cleanCache('channel.List')
        self.xnewa.cleanCache('summary.List')
        self.xnewa.cleanCache('guideListing-*.p')
        self.xnewa.cleanCache('*.p')
        self.refreshOnInit()

    def refreshOnInit(self):
        self.win.setProperty('busy', 'true')
        if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
            try:
                self.statusData = self.xnewa.GetNextPVRInfo(self.settings.NextPVR_USER, self.settings.NextPVR_PW,self.getChannels)
                self.getChannels = False
                if self.settings.XNEWA_INTERFACE != 'NextPVR':
                    self.upcomingData = self.xnewa.getUpcomingRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW, 10)
                    self.recentData = self.xnewa.getRecentRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW, 10)
                    self.renderUpComing()
                    self.renderRecent()
                    self.renderStats()
                self.offline = False
            except:
                handleException()
                self.win.setProperty('busy', 'false')
                xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), smartUTF8(__language__(30120)))
                self.offline = True
        else:
            self.offline = False
            self.win.setProperty('busy', 'false')
            self.winOnline();
            xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), '%s!' % smartUTF8(__language__(30109)))
            self.offline = True
            self.win.setFocusId(257)
        self.win.setProperty('busy', 'false')

    def renderUpComing(self):
        listItems = []
        if self.upcomingData != None:
            self.comingListBox.reset()
            for i, t in enumerate(self.upcomingData):
                listItem = xbmcgui.ListItem('Row %d' % i)
                if t['season'] == 0:
                    listItem.setProperty('title', t['title'])
                elif ( t['significance'] == ''):
                    listItem.setProperty('title','{0} ({1}x{2})'.format(t['title'],t['season'],t['episode']))
                else:
                    listItem.setProperty('title', '{0} : {1}'.format(t['title'],t['significance']))
                listItem.setProperty('channel', t['channel'][0])
                listItem.setProperty('date', self.xnewa.formatDate(t['start']))
                listItem.setProperty('date_long', self.xnewa.formatDate(t['start'], withyear=True))
                listItem.setProperty('start', self.xnewa.formatTime(t['start']))
                listItem.setProperty('end', self.xnewa.formatTime(t['end']))
                listItem.setProperty('description', t['desc'])
                listItem.setProperty('status', t['status'])
                listItem.setProperty('oid', str(t['program_oid']))
                listItems.append(listItem)
            if len(listItems) > 0:
                self.comingListBox.addItems(listItems)
                self.win.setFocus(self.comingListBox)
            else:
                self.win.setFocusId(999)


    def renderRecent(self):
        listItems = []
        self.recentListBox.reset()
        if self.recentData != None:
            for i, t in enumerate(self.recentData):
                listItem = xbmcgui.ListItem('Row %d' % i)
                if t['season'] == 0:
                    listItem.setProperty('title', t['title'])
                elif ( t['significance'] == ''):
                    listItem.setProperty('title','{0} ({1}x{2})'.format(t['title'],t['season'],t['episode']))
                else:
                    listItem.setProperty('title', '{0} : {1}'.format(t['title'],t['significance']))
                listItem.setProperty('channel', t['channel'][0])
                listItem.setProperty('date', self.xnewa.formatDate(t['start']))
                listItem.setProperty('date_long', self.xnewa.formatDate(t['start'], withyear=True))
                listItem.setProperty('start', self.xnewa.formatTime(t['start']))
                listItem.setProperty('end', self.xnewa.formatTime(t['end']))
                listItem.setProperty('description', t['desc'])
                listItem.setProperty('status', t['status'])
                listItem.setProperty('oid', str(t['program_oid']))
                listItems.append(listItem)
            if len(listItems) > 0:
                self.recentListBox.addItems(listItems)
                if self.comingListBox.size() == 0:
                    self.win.setFocus(self.recentListBox)


    def renderStats(self):
        # Set up free-space indication
        # First, the text part
        # Todo: Make safe for other languages / sizes (GB/MB, etc.)
        if self.statusData['directory'] != None:
            tmp = self.statusData['directory'][0]['Total'].split(' ')
            uom = tmp[1]
            print(type(tmp[0].replace(',','.')))
            lTotal = float(str(tmp[0].replace(',','.')))
            tmp = self.statusData['directory'][0]['Free'].split(' ')
            if uom != tmp[1]:
                lTotal = lTotal * 1000
            lFree = float(tmp[0].replace(',','.'))
            self.spaceFree.setLabel(str(lFree) + tmp[1])
            lUsed = lTotal - lFree
            self.spaceUsed.setLabel(str(lUsed) + tmp[1])
            # Then, the images part
            x, y = self.spaceGreen.getPosition()
            redWidth = int((old_div(250, (lTotal)) ) * lUsed)
            greenWidth = 250 - redWidth
            self.spaceGreen.setWidth(greenWidth)
            self.spaceRed.setWidth(redWidth)
            self.spaceRed.setPosition(x+greenWidth, y)
            if self.includePercentages:
                self.spacePercent.setPercent(old_div(100*lUsed,lTotal))
        # Set up display of counters
        self.countPending.setLabel(self.statusData['schedule']['Pending'])
        self.countProgress.setLabel(self.statusData['schedule']['InProgress'])
        self.countAvailable.setLabel(self.statusData['schedule']['Available'])
        self.countFailed.setLabel(self.statusData['schedule']['Failed'])
        self.countConflict.setLabel(self.statusData['schedule']['Conflict'])
        self.countSeason.setLabel(self.statusData['schedule']['Recurring'])

    def winOnline(self):
        if self.xnewa.offline:
            if self.xnewa.checkCache('recentRecordings-0.p') == False:
                self.win.setProperty('recent', 'false')
            if self.xnewa.checkCache('scheduledRecordings-0.p') == False:
                self.win.setProperty('scheduled', 'false')
            if self.xnewa.checkCache('upcomingRecordings-0.p') == False:
                self.win.setProperty('upcoming', 'false')
            self.win.setFocusId(257)
        if self.offline != self.xnewa.offline:
            self.offline = self.xnewa.offline
            if self.offline == True:
                self.win.setProperty('offline', 'true')
                self.win.setFocusId(257)
            else:
                self.win.setProperty('offline', 'false')
