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

import datetime, time
import xbmcgui
import os

from XNEWAGlobals import *

# ==============================================================================
class RecentRecordingsWindow(xbmcgui.WindowXML):
    
    def __init__(self, *args, **kwargs):
        self.closed = False
	self.win = None

       	self.settings = kwargs['settings']
       	self.xnewa = kwargs['xnewa']
        
    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.programsListBox = self.getControl(600)
            self.refreshButton = self.getControl(251)
            self.win.setProperty('busy', 'true')

            self.render()
        
    def onClick(self, controlId):
		source = self.getControl(controlId)
		if source == self.programsListBox: 
			self.goEditSchedule()
		elif source == self.refreshButton:
			self.xnewa.cleanCache('recentRecordings*.p')
			self.render()
		elif source == self.conflictButton:
			self.goConflicts()
             
    def onFocus(self, controlId):
        pass
            
    def onAction(self, action):
        #log.debug('Key got hit: %s   Current focus: %s' % (ui.toString(action), self.getFocusId()))
        if action.getId() in (EXIT_SCRIPT):
            self.closed = True
            self.close()

    def goEditSchedule(self):

	import details

	oid = self.recentData[self.programsListBox.getSelectedPosition()]['recording_oid']
        detailDialog = details.DetailDialog("nextpvr_recording_details.xml", WHERE_AM_I, xnewa=self.xnewa, settings=self.settings, oid=oid, type="R")
        detailDialog.doModal()
        if detailDialog.returnvalue is not None:
            self.render()

    def render(self):
	listItems = []

	if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
		self.win.setProperty('busy', 'true')
		try:
			self.recentData = self.xnewa.getRecentRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW)
			previous = None
			for i, t in enumerate(self.recentData):
				if t:
					listItem = xbmcgui.ListItem('Row %d' % i)
					airdate, previous = self.formattedAirDate(previous, t['start'].strftime('%a, %b %d'))
					listItem.setProperty('airdate', airdate)
					listItem.setProperty('title', t['title'])
					listItem.setProperty('status', t['status'])
					listItem.setProperty('start', t['start'].strftime("%H:%M"))
					duration = int((t['end'] - t['start']).seconds / 60)
					listItem.setProperty('duration', str(duration) )
					listItem.setProperty('channel', t['channel'][0])
					if len(t['subtitle']) > 0:
							listItem.setProperty('description', t['subtitle'] + "; " + t['desc'])
					else:
							listItem.setProperty('description', t['desc'])
					listItem.setProperty('oid', str(t['program_oid']))
					listItems.append(listItem)
				else:
					i = i - 1

			self.programsListBox.addItems(listItems)
		except:
			self.win.setProperty('busy', 'false')
			xbmcgui.Dialog().ok('Error', 'Unable to contact NextPVR Server!')
		self.win.setProperty('busy', 'false')
	else:
		xbmcgui.Dialog().ok('Error', 'Unable to contact NextPVR Server!')
		self.close()

    def formattedAirDate(self, previous, current):
        result = ''
        if not previous or previous <> current:
            today = datetime.date.today().strftime('%a, %b %d')
            if current == today:
                result = 'Today'
            else:
		tomorrow = (datetime.date.today() + datetime.timedelta(days=-1)).strftime('%a, %b %d')
		if current == tomorrow:
                	result = 'Yesterday'
            	else:
                	result = current
        return result, current
