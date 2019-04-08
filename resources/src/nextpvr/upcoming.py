from __future__ import division
from __future__ import absolute_import
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

from builtins import str
from past.utils import old_div
import datetime, time
import xbmcgui
import os

from XNEWAGlobals import *
from xbmcaddon import Addon
from fix_utf8 import smartUTF8

__language__ = Addon('script.kodi.knew4v5').getLocalizedString

programsListBoxId = 600
conflictButtonId = 250
refreshButtonId = 251

# ==============================================================================
class UpcomingRecordingsWindow(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.closed = False
        self.win = None

        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']

    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.programsListBox = self.getControl(600)
            self.conflictButton = self.getControl(250)
            self.refreshButton = self.getControl(251)
            self.win.setProperty('busy', 'true')

            self.render()

    def onClick(self, controlId):
        if controlId == programsListBoxId:
            self.goEditSchedule()
        elif controlId == refreshButtonId:
            self.xnewa.cleanCache('upComing*.p')
            self.render()
        elif controlId == conflictButtonId:
            self.goConflicts()

    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        #log.debug('Key got hit: %s   Current focus: %s' % (ui.toString(action), self.getFocusId()))
        if action.getId() in (EXIT_SCRIPT) or action.getButtonCode()  in (EXIT_SCRIPT):
            self.closed = True
            self.close()

    def goConflicts(self):
        from . import conflicts
        mywin = conflicts.ConflictedRecordingsWindow('nextpvr_conflicts.xml', WHERE_AM_I,self.settings.XNEWA_SKIN, settings=self.settings, xnewa=self.xnewa)
        mywin.doModal()

    def goEditSchedule(self):

        from . import details

        oid = self.upcomingData[self.programsListBox.getSelectedPosition()]['recording_oid']
        detailDialog = details.DetailDialog("nextpvr_recording_details.xml", WHERE_AM_I,self.settings.XNEWA_SKIN, xnewa=self.xnewa, settings=self.settings, oid=oid, type="R")
        detailDialog.doModal()
        if detailDialog.returnvalue is not None:
            self.render()

    def render(self):
        listItems = []
        self.programsListBox.reset()
        if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
            self.win.setProperty('busy', 'true')
            try:
                self.upcomingData = self.xnewa.getUpcomingRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW)
                if self.upcomingData != None:
                    previous = None
                    for i, t in enumerate(self.upcomingData):
                        listItem = xbmcgui.ListItem('Row %d' % i)
                        airdate, previous = self.formattedAirDate(previous, self.xnewa.formatDate(t['start']))
                        listItem.setProperty('airdate', airdate)
                        listItem.setProperty('airdate_long', self.xnewa.formatDate(t['start'], withyear=True))
                        if ( t['significance'] == ''):
                            listItem.setProperty('title', t['title'])
                        else:
                            listItem.setProperty('title', '{0} : {1}'.format(t['title'],t['significance']))
                        listItem.setProperty('status', t['status'])
                        listItem.setProperty('start', self.xnewa.formatTime(t['start']))
                        listItem.setProperty('end', self.xnewa.formatTime(t['end']))
                        duration = int(old_div((t['end'] - t['start']).seconds, 60))
                        listItem.setProperty('duration', str(duration) )
                        listItem.setProperty('channel', t['channel'][0])
                        listItem.setProperty('description', t['desc'])
                        if t['season'] == 0:
                            listItem.setProperty('episode', t['subtitle'])
                        else:
                            listItem.setProperty('episode','({0}x{1}) {2}'.format(t['season'],t['episode'],t['subtitle']))
                        listItem.setProperty('oid', str(t['program_oid']))
                        listItems.append(listItem)
                    if len(listItems) > 0:
                        self.programsListBox.addItems(listItems)
                        self.win.setFocusId(600)
                    else:
                        self.win.setFocusId(999)

            except:
                self.win.setProperty('busy', 'false')
                xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), '%s!' % smartUTF8(__language__(30109)))

            self.win.setProperty('busy', 'false')
        else:
            #Todo: Show error message
            xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), '%s!' % smartUTF8(__language__(30109)))
            self.close()

    def formattedAirDate(self, previous, current):
        result = ''
        if not previous or previous != current:
            today = self.xnewa.formatDate(datetime.date.today())
            if current == today:
                result = smartUTF8(__language__(30133))
            else:
                tomorrow = self.xnewa.formatDate(datetime.date.today() + datetime.timedelta(days=1))
                if current == tomorrow:
                    result = smartUTF8(__language__(30134))
                else:
                    result = current
        return result, current
