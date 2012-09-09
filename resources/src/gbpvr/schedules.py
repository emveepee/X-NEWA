#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2009 analogue@yahoo.com
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
import xbmcgui
import operator

from myGBPVRGlobals import *

# ==============================================================================
class SchedulesWindow(xbmcgui.WindowXML):
    
    def __init__(self, *args, **kwargs):
        self.closed = False
	self.win = None

       	self.settings = kwargs['settings']
       	self.gbpvr = kwargs['gbpvr']
        
    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.schedulesListBox = self.getControl(600)
            self.refreshButton = self.getControl(250)
            self.win.setProperty('busy', 'true')

            self.render()

    def onClick(self, controlId):
        source = self.getControl(controlId)
        if source == self.schedulesListBox: 
            self.goEditSchedule()
        elif source == self.refreshButton:
            self.render()
             
    def onFocus(self, controlId):
        pass
            
    def onAction(self, action):
        if action.getId() in (EXIT_SCRIPT):
            self.closed = True
            self.close()

    def goEditSchedule(self):

	import details

	oid = self.scheduleData[self.schedulesListBox.getSelectedPosition()]['recording_oid']
        detailDialog = details.DetailDialog("nextpvr_details.xml", WHERE_AM_I, gbpvr=self.gbpvr, settings=self.settings, oid=oid,type="F")
        detailDialog.doModal()
        if detailDialog.returnvalue is not None:
            self.render()
                             
    def render(self):
	listItems = []

	if self.gbpvr.AreYouThere(self.settings.usewol(), self.settings.GBPVR_MAC, self.settings.GBPVR_BROADCAST):
		self.win.setProperty('busy', 'true')
		try:
                        self.scheduleData = self.gbpvr.getScheduledRecordings(self.settings.GBPVR_USER, self.settings.GBPVR_PW)
                        self.scheduleData.sort(key=operator.itemgetter('priority'))
                        previous = None
                        for i, t in enumerate(self.scheduleData):
                                listItem = xbmcgui.ListItem('Row %d' % i)
                                listItem.setProperty('title', t['title'])
                                listItem.setProperty('channel', t['channel'])
                                listItem.setProperty('rectype', t['rectype'])
                                listItem.setProperty('priority', str(t['priority']))
                                listItem.setProperty('oid', str(t['recording_oid']))
                                listItems.append(listItem)
                        self.schedulesListBox.addItems(listItems)
                except:
                        self.win.setProperty('busy', 'false')
                        xbmcgui.Dialog().ok('Error', 'Unable to contact GBPVR Server!')
                    
		self.win.setProperty('busy', 'false')
	else:
		#Todo: Show error message
		xbmcgui.Dialog().ok('Error', 'Unable to contact GBPVR Server!')
		self.close()
        

    def renderPosters(self):
        # split up poster lookup to run in parallel
        for schedules in util.slice(self.listItemsBySchedule.keys(), 4):
            self.renderPostersThread(schedules)

    def renderPostersThread(self, schedules):
        for i, schedule in enumerate(schedules):
            if self.closed:
                return
            # Lookup poster if available
            #log.debug('Poster %d/%d for %s' % (i+1, len(self.listItemsBySchedule), schedule.title()))
            posterPath = self.fanArt.getRandomPoster(schedule)
            listItem = self.listItemsBySchedule[schedule]
            if posterPath:
                self.setListItemProperty(listItem, 'poster', posterPath)
            else:
                channel =  self.channelsById[schedule.getChannelId()]
                if channel.getIconPath():
                    self.setListItemProperty(listItem, 'poster', self.mythChannelIconCache.get(channel))

