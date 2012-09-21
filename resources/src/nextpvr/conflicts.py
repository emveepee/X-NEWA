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
class ConflictedRecordingsWindow(xbmcgui.WindowXML):
    
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

            self.render()
        
    def onClick(self, controlId):
        source = self.getControl(controlId)
        if source == self.programsListBox: 
            self.goEditSchedule()
        elif source == self.refreshButton:
            self.render()
             
    def onFocus(self, controlId):
        pass
            
    def onAction(self, action):
        #log.debug('Key got hit: %s   Current focus: %s' % (ui.toString(action), self.getFocusId()))
        if action.getId() in (EXIT_SCRIPT):
            self.closed = True
            self.close()

    def goEditSchedule(self):
	self.win.setProperty('busy', 'true')
	if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
            try:
                    theConflicts = self.xnewa.getConflicts(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.conflictedData[self.programsListBox.getSelectedPosition()])
                    theDlg = xbmcgui.Dialog()
                    theArr = []
                    for prog in theConflicts:
                        print prog['title']
                        theArr.append(prog['title'])
                    pos = theDlg.select('Choose recording to cancel', theArr)
                    if pos >= 0:
                        if xbmcgui.Dialog().yesno("Delete Recording", "Are you sure you want to delete recording: " + theArr[pos] + "?"):
                                self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, theConflicts[pos])
                                self.render()
            except:
                    self.win.setProperty('busy', 'false')
                    xbmcgui.Dialog().ok('Sorry', 'An error occurred!')                
            self.win.setProperty('busy', 'false')
        else:
            self.win.setProperty('busy', 'false')
            xbmcgui.Dialog().ok('Sorry', 'An error occurred!')

    def render(self):
	listItems = []

	self.win.setProperty('busy', 'true')
	if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                try:
                        self.conflictedData = self.xnewa.getConflictedRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW)
                        if len(self.conflictedData) == 0:
                            xbmcgui.Dialog().ok('Good News!', 'No conflicted recordings found!')
                            self.close()
                            
                        previous = None
                        for i, t in enumerate(self.conflictedData):
                                listItem = xbmcgui.ListItem('Row %d' % i)
                                airdate, previous = self.formattedAirDate(previous, t['start'].strftime('%a, %b %d'))
                                listItem.setProperty('airdate', airdate)
                                listItem.setProperty('title', t['title'])
                                listItem.setProperty('start', t['start'].strftime("%H:%M"))
                                duration = int((t['end'] - t['start']).seconds / 60)
                                listItem.setProperty('duration', str(duration) )
                                listItem.setProperty('channel', t['channel'])
                                if len(t['subtitle']) > 0:
                                        listItem.setProperty('description', t['subtitle'] + "; " + t['desc'])
                                else:
                                        listItem.setProperty('description', t['desc'])
                                listItem.setProperty('oid', str(t['program_oid']))
                                listItems.append(listItem)
                        self.programsListBox.addItems(listItems)
                except:
                        self.win.setProperty('busy', 'false')
                        xbmcgui.Dialog().ok('Error', 'Unable to contact NextPVR Server!')
                    
		self.win.setProperty('busy', 'false')
	else:
		self.win.setProperty('busy', 'false')
		xbmcgui.Dialog().ok('Error', 'Unable to contact NextPVR Server!')
		self.close()

    def formattedAirDate(self, previous, current):
        result = ''
        if not previous or previous <> current:
            today = datetime.date.today().strftime('%a, %b %d')
            if current == today:
                result = 'Today'
            else:
		tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%a, %b %d')
		if current == tomorrow:
                	result = 'Tomorrow'
            	else:
                	result = current
        return result, current
