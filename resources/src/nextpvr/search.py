from __future__ import division
from __future__ import print_function
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
searchButtonId = 250
optionsButtonId = 251

# ==============================================================================
class SearchWindow(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.closed = False
        self.win = None

        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']
        self.option = 0

    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.programsListBox = self.getControl(600)
            self.searchButton = self.getControl(250)
            self.optionsButton = self.getControl(251)
            self.render(False)
            self.win.setFocusId(250)

    def onClick(self, controlId):
        if controlId == programsListBoxId:
            self.goEditSchedule()
        elif controlId == searchButtonId:
            self.render()
        elif controlId == optionsButtonId:
            options = [__language__(30011),__language__(30041),__language__(32008),__language__(30020)]
            self.option += 1
            if self.option > 3:
                self.option = 0
            self.optionsButton.setLabel(__language__(32007) + ': ' + options[self.option])



    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        #print 'Key got hit: %s   Current focus: %s' % (ui.toString(action), self.getFocusId())
        if action.getId() in (EXIT_SCRIPT) or action.getButtonCode()  in (EXIT_SCRIPT):
            self.closed = True
            self.close()

    def goEditSchedule(self):
        from . import details
        oid = self.searchData[self.programsListBox.getSelectedPosition()]['program_oid']
        if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
            detailDialog = details.DetailDialog("nextpvr_recording_details.xml", WHERE_AM_I,self.settings.XNEWA_SKIN, xnewa=self.xnewa, settings=self.settings, oid=oid, type="E")
            detailDialog.doModal()
            if detailDialog.returnvalue is not None:
                if detailDialog.returnvalue == "PICK":
                    detailDialog = details.DetailDialog("nextpvr_details.xml",  WHERE_AM_I,self.settings.XNEWA_SKIN, xnewa=self.xnewa, settings=self.settings, oid=oid, epg=True, type="P")
                    detailDialog.doModal()

        if detailDialog.shouldRefresh:
            self.render()

    def render(self, reload=True):
        if reload:
            myText = self._getText("%s:" % smartUTF8(__language__(30151)),"")
            if myText is None or myText == '':
                self.close()
                return
            xbmc.executebuiltin(XBMC_DIALOG_BUSY_OPEN)
            self.xnewa.cleanCache('search.List')
        else:
            myText = None

        listItems = []
        self.programsListBox.reset()
        self.win.setProperty('busy', 'true')

        if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
            try:
                self.searchData = self.xnewa.searchProgram(self.settings.NextPVR_USER, self.settings.NextPVR_PW, myText,self.option)
                previous = None
                if not self.searchData:
                    if reload == True:
                        self.win.setProperty('busy', 'false')
                        xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), smartUTF8(__language__(30123)))
                    self.win.setFocusId(250)
                else:
                    self.searchData = sorted(self.searchData, key = lambda x: (x['start']))
                    for i, t in enumerate(self.searchData):
                        if t['rec']:
                            self.win.setProperty('recording', 'true')
                        else:
                            self.win.setProperty('recording', '')
                        listItem = xbmcgui.ListItem('Row %d' % i)
                        airdate, previous = self.formattedAirDate(previous, self.xnewa.formatDate(t['start']))
                        listItem.setProperty('airdate', airdate)
                        listItem.setProperty('airdate_long',  self.xnewa.formatDate(t['start'], withyear=True))
                        listItem.setProperty('title', t['title'])
                        listItem.setProperty('start', self.xnewa.formatTime(t['start']))
                        listItem.setProperty('end', self.xnewa.formatTime(t['end']))
                        duration = int(old_div((t['end'] - t['start']).seconds, 60))
                        listItem.setProperty('duration', str(duration))
                        listItem.setProperty('channel', t['channel'][0])
                        listItem.setProperty('description', t['desc'])
                        listItem.setProperty('episode', t['subtitle'])
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
            if reload:
                xbmc.executebuiltin(XBMC_DIALOG_BUSY_CLOSE)
            self.win.setProperty('busy', 'false')
        else:
            self.win.setProperty('busy', 'false')
            xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), '%s!' % smartUTF8(__language__(30109)))
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
