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
import os
import xbmcgui
import operator

from XNEWAGlobals import *
from xbmcaddon import Addon
from fix_utf8 import smartUTF8

__language__ = Addon('script.kodi.knew4v5').getLocalizedString

schedulesListBoxId = 600
refreshButtonId = 250
sortButtonId = 253

# ==============================================================================
class SchedulesWindow(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.closed = False
        self.win = None
        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']
        self.sortkey = self.settings.XNEWA_SORT_RECURRING

    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.schedulesListBox = self.getControl(600)
            self.refreshButton = self.getControl(250)
            try:
                self.sortButton = self.getControl(253)
            except RuntimeError:
                self.sortButton = False
            self.win.setProperty('busy', 'true')

            self.render()

    def onClick(self, controlId):
        if controlId == schedulesListBoxId:
            self.goEditSchedule()
        elif controlId == refreshButtonId:
            self.xnewa.cleanCache('scheduledRecordings.p')
            self.render()
        elif controlId == sortButton.Id:
            order = [smartUTF8(__language__(30011)),smartUTF8(__language__(30012)),smartUTF8(__language__(30042))]
            ret = xbmcgui.Dialog().select(smartUTF8(__language__(30122)), order);
            if ret != -1:
                if ret == 0:
                    self.sortkey = 'title'
                elif ret == 1:
                    self.sortkey = 'channel'
                elif ret == 2:
                    self.sortkey = 'priority'
                if self.sortkey != self.settings.XNEWA_SORT_RECURRING:
                    self.settings.XNEWA_SORT_RECURRING = self.sortkey
                    addon = Addon()
                    addon.setSetting(id='recurringSort',value=self.sortkey)
                self.render()

    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        if action.getId() in (EXIT_SCRIPT) or action.getButtonCode()  in (EXIT_SCRIPT):
            self.closed = True
            self.close()

    def goEditSchedule(self):

        from . import details
        oid = self.scheduleData[self.schedulesListBox.getSelectedPosition()]['recording_oid']
        detailDialog = details.DetailDialog("nextpvr_details.xml", WHERE_AM_I,self.settings.XNEWA_SKIN, xnewa=self.xnewa, settings=self.settings, oid=oid,type="F")
        detailDialog.doModal()
        if detailDialog.returnvalue is not None:
            self.render()

    def render(self):
        listItems = []
        self.schedulesListBox.reset()
        if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
            self.win.setProperty('busy', 'true')
            try:
                self.scheduleData = self.xnewa.getScheduledRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW)
                self.scheduleData.sort(key=operator.itemgetter(self.sortkey))
                previous = None
                for i, t in enumerate(self.scheduleData):
                    listItem = xbmcgui.ListItem('Row %d' % i)
                    listItem.setProperty('title', t['name'])
                    showIcon = self.xnewa.getShowIcon(t['title'])
                    listItem.setProperty('showicon',showIcon)
                    if t['channel_oid']!=0:
                        listItem.setProperty('channel', t['channel'][0])
                    else:
                        listItem.setProperty('channel', '%s %s' % (smartUTF8(__language__(30020)), smartUTF8(__language__(30057))))
                    listItem.setProperty('rectype', t['rectype'])
                    listItem.setProperty('priority', str(t['priority']))
                    listItem.setProperty('oid', str(t['recording_oid']))
                    listItems.append(listItem)
                if len(listItems) > 0:
                    self.schedulesListBox.addItems(listItems)
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


    def renderPosters(self):
        # split up poster lookup to run in parallel
        for schedules in util.slice(list(self.listItemsBySchedule.keys()), 4):
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
