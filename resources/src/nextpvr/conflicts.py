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
import datetime, time, sys
import xbmcgui
import os
from XNEWAGlobals import *
from xbmcaddon import Addon
from fix_utf8 import smartUTF8

__language__ = Addon('script.kodi.knew4v5').getLocalizedString

programsListBoxId = 600
refreshButtonId = 251

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
        if controlId == refreshButtonId:
            self.render()
        elif controlId == programsListBoxId:
            self.goEditSchedule()
        else:
            print(self.conflictedData[self.programsListBox.getSelectedPosition()])
            from . import details
            if self.conflictedData[self.programsListBox.getSelectedPosition()]['start'] > datetime.datetime.now():
                oid = self.conflictedData[self.programsListBox.getSelectedPosition()]['program_oid']
                detailDialog = details.DetailDialog("nextpvr_recording_details.xml",  WHERE_AM_I,self.settings.XNEWA_SKIN, xnewa=self.xnewa, settings=self.settings, oid=oid, epg=True, type="E")
            else:
                oid = self.conflictedData[self.programsListBox.getSelectedPosition()]['recording_oid']
                detailDialog = details.DetailDialog("nextpvr_recording_details.xml",  WHERE_AM_I,self.settings.XNEWA_SKIN, xnewa=self.xnewa, settings=self.settings, oid=oid, epg=True, type="R")
            detailDialog.doModal()
            if detailDialog.returnvalue is not None:
                pass

    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        #log.debug('Key got hit: %s   Current focus: %s' % (ui.toString(action), self.getFocusId()))
        if action.getId() in (EXIT_SCRIPT) or action.getButtonCode()  in (EXIT_SCRIPT):
            self.closed = True
            self.close()

    def goEditSchedule(self):
        self.win.setProperty('busy', 'true')
        if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
            try:
                theConflicts = self.xnewa.getConflicts(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.conflictedData[self.programsListBox.getSelectedPosition()])
                theDlg = xbmcgui.Dialog()
                theArr = []
                for conflict in theConflicts:
                    theArr.append(conflict['title'] + " " + str(conflict['start']) )
                pos = theDlg.select('Choose recording to cancel', theArr)
                if pos >= 0:
                    if xbmcgui.Dialog().yesno(smartUTF8(__language__(30102)), "%s: %s?" % (smartUTF8(__language__(30103)), theArr[pos])):
                        self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, theConflicts[pos])
                        self.render()
            except:
                self.win.setProperty('busy', 'false')
                xbmcgui.Dialog().ok(smartUTF8(__language__(30104)), '%s!' % smartUTF8(__language__(30105)))
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
                    xbmcgui.Dialog().ok('%s!' % smartUTF8(__language__(30106)), '%s!' % smartUTF8(__language__(30107)))
                    self.close()
                previous = None
                for i, t in enumerate(self.conflictedData):
                    listItem = xbmcgui.ListItem('Row %d' % i)
                    airdate, previous = self.formattedAirDate(previous, self.xnewa.formatDate(t['start']))
                    listItem.setProperty('airdate', airdate)
                    listItem.setProperty('title', t['title'])
                    listItem.setProperty('start', self.xnewa.formatTime(t['start']))
                    duration = ((t['end'] - t['start']).seconds) // 60
                    listItem.setProperty('duration', str(duration) )
                    listItem.setProperty('channel', t['channel'][0])
                    if len(t['subtitle']) > 0:
                        listItem.setProperty('description', t['subtitle'] + "; " + t['desc'])
                    else:
                        listItem.setProperty('description', t['desc'])
                    listItem.setProperty('description_short', t['desc'])
                    listItem.setProperty('episode', t['subtitle'])
                    listItem.setProperty('oid', str(t['program_oid']))
                    listItems.append(listItem)
                self.programsListBox.addItems(listItems)
            except:
                self.win.setProperty('busy', 'false')
                xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), '%s!' % smartUTF8(__language__(30109)))

            self.win.setProperty('busy', 'false')
        else:
            self.win.setProperty('busy', 'false')
            xbmcgui.Dialog().ok('Error', 'Unable to contact NextPVR Server!')
            self.close()

    def formattedAirDate(self, previous, current):
        result = ''
        if not previous or previous != current:
            today = self.xnewa.formatDate(datetime.date.today())
            if current == today:
                result = 'Today'
            else:
                tomorrow = self.xnewa.formatDate(datetime.date.today() + datetime.timedelta(days=1))
                if current == tomorrow:
                    result = 'Tomorrow'
                else:
                    result = current
        return result, current
