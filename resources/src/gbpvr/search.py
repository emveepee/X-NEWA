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

from myGBPVRGlobals import *

# ==============================================================================
class SearchWindow(xbmcgui.WindowXML):
    
    def __init__(self, *args, **kwargs):
        self.closed = False
	self.win = None

       	self.settings = kwargs['settings']
       	self.gbpvr = kwargs['gbpvr']
        
    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.programsListBox = self.getControl(600)
            self.searchButton = self.getControl(250)
            self.render()
        
    def onClick(self, controlId):
        source = self.getControl(controlId)
        if source == self.programsListBox: 
            self.goEditSchedule()
        elif source == self.searchButton:
            self.render()
             
    def onFocus(self, controlId):
        pass
            
    def onAction(self, action):
        #log.debug('Key got hit: %s   Current focus: %s' % (ui.toString(action), self.getFocusId()))
        if action.getId() in (EXIT_SCRIPT):
            self.closed = True
            self.close()

    def goEditSchedule(self):
		import details
		oid = self.searchData[self.programsListBox.getSelectedPosition()]['program_oid']
		detailDialog = details.DetailDialog("nextpvr_details.xml", WHERE_AM_I, gbpvr=self.gbpvr, settings=self.settings, oid=oid, type="P")
		detailDialog.doModal()
		if detailDialog.shouldRefresh:
			self.render()

    def render(self):
        myText = self._getText("Please enter search phrase:","")
        if myText is None:
            self.close()
    
	listItems = []
	self.win.setProperty('busy', 'true')

	if self.gbpvr.AreYouThere(self.settings.usewol(), self.settings.GBPVR_MAC, self.settings.GBPVR_BROADCAST):
                try:
                        self.searchData = self.gbpvr.searchProgram(self.settings.GBPVR_USER, self.settings.GBPVR_PW, myText)
                        previous = None
                        if len(self.searchData) == 0:
                            self.win.setProperty('busy', 'false')
                            xbmcgui.Dialog().ok('Error', 'Search returned no results')
                            
                        for i, t in enumerate(self.searchData):
                                if t['rec']:
                                        pre = '[B]'
                                        post = '[/B]'
                                else:
                                        pre = ''
                                        post = ''
                                listItem = xbmcgui.ListItem('Row %d' % i)
                                airdate, previous = self.formattedAirDate(previous, t['start'].strftime('%a, %b %d'))
                                listItem.setProperty('airdate', airdate)
                                listItem.setProperty('title', pre + t['title'] + post)
                                listItem.setProperty('start', pre + t['start'].strftime("%H:%M") + post)
                                duration = int((t['end'] - t['start']).seconds / 60)
                                listItem.setProperty('duration', pre + str(duration) + post)
                                listItem.setProperty('channel', pre + t['channel'] + post)
                                if len(t['subtitle']) > 0:
                                        listItem.setProperty('description', pre + t['subtitle'] + "; " + t['desc'] + post)
                                else:
                                        listItem.setProperty('description', pre + t['desc'] + post)
                                listItem.setProperty('oid', str(t['program_oid']))
                                listItems.append(listItem)
                        self.programsListBox.addItems(listItems)
                except:
                        self.win.setProperty('busy', 'false')
                        xbmcgui.Dialog().ok('Error', 'Unable to contact GBPVR Server!')
                    
		self.win.setProperty('busy', 'false')
	else:
                self.win.setProperty('busy', 'false')
		xbmcgui.Dialog().ok('Error', 'Unable to contact GBPVR Server!')
		self.close()

    def _getText(self, cTitle, cText):
	kbd = xbmc.Keyboard(cText, cTitle)

	kbd.doModal()

        txt = None
	if kbd.isConfirmed():
		txt = kbd.getText()
		
	return txt

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
