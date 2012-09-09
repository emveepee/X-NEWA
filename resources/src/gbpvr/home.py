#
#  myGBPVR for XBMC
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
import os
import sys

import xbmc
import xbmcgui
from xbmcaddon import Addon

from myGBPVRGlobals import *
from GBPVR_Connect import GBPVR_Connect
from GBPVR_Settings import GBPVR_Settings

# =============================================================================
class HomeWindow(xbmcgui.WindowXML):
    
    def __init__(self, *args, **kwargs):
		self.win = None
		self.busy = False
		self.progressDialog = None
		self.settings = GBPVR_Settings()
		self.gbpvr = GBPVR_Connect(self.settings.GBPVR_HOST, self.settings.GBPVR_PORT)
        
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
            
            # button ids -> funtion ptr
            self.dispatcher = {
                248 : self.goUpcomingDetails,
                249 : self.goRecentDetails,
                250 : self.goWatchRecordings,
                251 : self.goTvGuide,
                252 : self.goRecordingSchedules,
                253 : self.goUpcomingRecordings,
                254 : self.goSearch,
                255 : self.goSettings,
                256 : self.refreshOnInit,
				257 : self.goExit,
                258 : self.goRecentRecordings
            }
            
            self.refreshOnInit()
        else:
            self.refresh()
   
    def onAction(self, action):
        if action.getId() in (EXIT_SCRIPT):
            self.closed = True
            self.close()

    def onClick(self, controlId):
        try:
            self.dispatcher[controlId]()
        except KeyError:
            debug('onClick')
               
    def goSearch(self):
		import search
		mywin = search.SearchWindow('nextpvr_search.xml', WHERE_AM_I, settings=self.settings, gbpvr=self.gbpvr)
		mywin.doModal()

    def goExit(self):
		self.closed = True
		self.close()

    def goRecentDetails(self):
		import details
		oid = self.recentData[self.recentListBox.getSelectedPosition()]['recording_oid']
		detailDialog = details.DetailDialog("nextpvr_details.xml", WHERE_AM_I, settings=self.settings, gbpvr=self.gbpvr, oid=oid, type="R" )
		detailDialog.doModal()
		if detailDialog.shouldRefresh:
			self.render()

    def goUpcomingDetails(self):
		import details

		oid = self.upcomingData[self.comingListBox.getSelectedPosition()]['program_oid']
		detailDialog = details.DetailDialog("nextpvr_details.xml", WHERE_AM_I, settings=self.settings, gbpvr=self.gbpvr, oid=oid, type="P")
		detailDialog.doModal()
		if detailDialog.shouldRefresh:
			self.render()

    def goWatchRecordings(self):
        xbmc.executebuiltin('XBMC.ActivateWindow(videolibrary,tvshowtitles)')
        
    def goTvGuide(self):
		import epg
		mywin = epg.EpgWindow('nextpvr_epg.xml', WHERE_AM_I, gbpvr=self.gbpvr, settings=self.settings)
		mywin.doModal()
    
    def goRecordingSchedules(self):
		import schedules
		mywin = schedules.SchedulesWindow('nextpvr_schedules.xml', WHERE_AM_I, settings=self.settings, gbpvr=self.gbpvr)
		mywin.doModal()
            
    def goUpcomingRecordings(self):
		import upcoming
		mywin = upcoming.UpcomingRecordingsWindow('nextpvr_upcoming.xml', WHERE_AM_I, settings=self.settings, gbpvr=self.gbpvr)
		mywin.doModal()
        
    def goRecentRecordings(self):
		import recent
		mywin = recent.RecentRecordingsWindow('nextpvr_recent.xml', WHERE_AM_I, settings=self.settings, gbpvr=self.gbpvr)
		mywin.doModal()
        
    def goSettings(self):
		import settings
		mywin = settings.settingsDialog('nextpvr_settings.xml', WHERE_AM_I, settings=self.settings)
		mywin.doModal()
		self.gbpvr = GBPVR_Connect(self.settings.GBPVR_HOST, self.settings.GBPVR_PORT)
		#self.statusData = self.gbpvr.GetGBPVRInfo(self.settings.GBPVR_USER, self.settings.GBPVR_PW)

		self.refreshOnInit()

    def refresh(self):
		self.renderUpComing()
		self.renderRecent()
		self.renderStats()

    def refreshOnInit(self):
		self.win.setProperty('busy', 'true')
		if self.gbpvr.AreYouThere(self.settings.usewol(), self.settings.GBPVR_MAC, self.settings.GBPVR_BROADCAST):
			try:
				self.statusData = self.gbpvr.GetGBPVRInfo(self.settings.GBPVR_USER, self.settings.GBPVR_PW)
				self.upcomingData = self.gbpvr.getUpcomingRecordings(self.settings.GBPVR_USER, self.settings.GBPVR_PW, 10)
				self.recentData = self.gbpvr.getRecentRecordings(self.settings.GBPVR_USER, self.settings.GBPVR_PW, 10)
				self.renderUpComing()
				self.renderRecent()
				self.renderStats()				
				self.win.setProperty('busy', 'false')
			except:
				handleException()
				self.win.setProperty('busy', 'false')
				xbmcgui.Dialog().ok('Error', 'Unable to contact GBPVR Server!')
		else:
			self.win.setProperty('busy', 'false')
			xbmcgui.Dialog().ok('Error', 'Unable to contact GBPVR Server!')
			#self.close()

    def renderUpComing(self):
		listItems = []
		for i, t in enumerate(self.upcomingData):
			listItem = xbmcgui.ListItem('Row %d' % i)
			listItem.setProperty('title', t['title'])
			listItem.setProperty('date', t['start'].strftime("%a, %b %d %H:%M"))
			listItem.setProperty('end', t['end'].strftime("%H:%M"))
			listItem.setProperty('description', t['desc'])
			listItem.setProperty('channel', t['channel'][0])
			listItem.setProperty('oid', str(t['program_oid']))
			listItems.append(listItem)
		self.comingListBox.addItems(listItems)

    def renderRecent(self):
        listItems = []
        for i, t in enumerate(self.recentData):
            listItem = xbmcgui.ListItem('Row %d' % i)
            listItem.setProperty('title', t['title'])
            listItem.setProperty('date', t['start'].strftime("%a, %b %d %H:%M"))
            listItem.setProperty('end', t['end'].strftime("%H:%M"))
            listItem.setProperty('description', t['desc'])
            listItem.setProperty('status', t['status'])
            listItem.setProperty('oid', str(t['program_oid']))
            listItems.append(listItem)
        self.recentListBox.addItems(listItems)
               
    def renderStats(self):
		# Set up free-space indication
		# First, the text part
		# Todo: Make safe for other languages / sizes (GB/MB, etc.)
		tmp = self.statusData['directory'][0]['Total'].split(' ')
		lTotal = float(tmp[0].replace(',','.'))
		tmp = self.statusData['directory'][0]['Free'].split(' ')
		lFree = float(tmp[0].replace(',','.'))
		lUsed = lTotal - lFree
		self.spaceFree.setLabel(str(lFree) + " Gb")
		self.spaceUsed.setLabel(str(lUsed) + " Gb")
		# Then, the images part
		x, y = self.spaceGreen.getPosition()
		redWidth = int((250 / (lTotal) ) * lUsed)
		greenWidth = 250 - redWidth
		self.spaceGreen.setWidth(greenWidth)
		self.spaceRed.setWidth(redWidth)
		self.spaceRed.setPosition(x+greenWidth, y)
	
		# Set up display of counters
		self.countPending.setLabel(self.statusData['schedule']['Pending'])
		self.countProgress.setLabel(self.statusData['schedule']['InProgress'])
		self.countAvailable.setLabel(self.statusData['schedule']['Available'])
		self.countFailed.setLabel(self.statusData['schedule']['Failed'])
		self.countConflict.setLabel(self.statusData['schedule']['Conflict'])
		self.countSeason.setLabel(self.statusData['schedule']['Recurring'])
