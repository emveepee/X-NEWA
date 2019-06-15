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
from builtins import range
import datetime, time
import _strptime
import xbmcgui
import os

from XNEWAGlobals import *
from xbmcaddon import Addon
from fix_utf8 import smartUTF8

__language__ = Addon('script.kodi.knewc').getLocalizedString

programsListBoxId = 600
refreshButtonId = 251
importButtonId = 252
sortButtonId = 253
actionButtonId = 254
filterButtonId = 255


# ==============================================================================
class RecentRecordingsWindow(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.closed = False
        self.win = None
        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']
        self.mode = 0
        self.sortTitle = [True,True]
        self.sortDate = [False,False]
        if self.settings.XNEWA_SORT_RECORDING == 0:
            self.sortTitle[0] = True
            self.sortDate[0] = True
        elif self.settings.XNEWA_SORT_RECORDING  == 1:
            self.sortTitle[0] = False
            self.sortDate[0] = True
        elif self.settings.XNEWA_SORT_RECORDING  == 2:
            self.sortTitle[0] = False
            self.sortDate[0] = False

        if self.settings.XNEWA_SORT_EPISODE == 0 or self.settings.XNEWA_SORT_EPISODE == 3:
            self.sortTitle[1] = True
            self.sortDate[1] = True
        elif self.settings.XNEWA_SORT_EPISODE == 1:
            self.sortTitle[1] = False
            self.sortDate[1] = True
        elif self.settings.XNEWA_SORT_EPISODE == 2:
            self.sortTitle[1] = False
            self.sortDate[1] = False

        self.show = None
        self.showPosition = 0
        self.selections = 0
        self.recentData = None
        self.recDir = None
        self.filtered = False

    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.win.setProperty('archive', __language__(30020))
            self.programsListBox = self.getControl(600)
            self.refreshButton = self.getControl(251)
            self.importButton = self.getControl(252)
            self.importButton.setVisible(False)
            self.sortButton = self.getControl(253)
            self.actionButton = self.getControl(254)
            self.filterButton = self.getControl(255)
            self.render()
            self.win.setProperty('tagged', 'false')

    def onClick(self, controlId):
        if controlId == programsListBoxId:
            self.goEditSchedule()
        elif controlId == refreshButtonId:
            self.xnewa.cleanCache('recentRecordings*.p')
            self.xnewa.cleanCache('summary.List')
            self.render()
        elif controlId == importButtonId:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno(smartUTF8(__language__(30127)), '%s %s' % (smartUTF8(__language__(30121)), self.recentData[self.programsListBox.getSelectedPosition()]['title']))
        elif controlId == actionButtonId:
            order = [__language__(30038),__language__(30039),__language__(32003),__language__(30054),__language__(32004),__language__(30033)]
            ret = xbmcgui.Dialog().select(__language__(32005), order);
            if ret > 0:
                self.processFile(order[ret])
                if self.selections > 0:
                    self.win.setProperty('tagged', 'true')
                else:
                    self.win.setProperty('tagged', 'false')
                if self.mode ==0:
                    self.render()

        elif controlId == filterButtonId:
            choices = list(self.xnewa.RecDirs.keys())
            if self.filterButton.isSelected():
                archive =  xbmcgui.Dialog().select(smartUTF8(__language__(30115)), choices)
                if archive != -1:
                    self.filtered = True
                    self.win.setProperty('archive', choices[archive])
                    self.recDir = self.xnewa.RecDirs[choices[archive]]
            else:
                self.recDir = None
                archive = 0
                self.win.setProperty('archive', __language__(30020))

            if archive != -1:
                self.xnewa.cleanCache('recentRecordings*.p')
                self.xnewa.cleanCache('summary.List')
                self.render()
        elif controlId == sortButtonId:
            order = [smartUTF8(__language__(30011)),smartUTF8(__language__(30148)),smartUTF8(__language__(30149)),__language__(32006)]
            ret = xbmcgui.Dialog().select(smartUTF8(__language__(30122)), order);
            if ret != -1:
                if ret == 0:
                    self.sortTitle[self.mode] = True
                    self.sortDate[self.mode] = True
                elif ret == 1:
                    self.sortTitle[self.mode] = False
                    self.sortDate[self.mode] = True
                elif ret == 2:
                    self.sortTitle[self.mode] = False
                    self.sortDate[self.mode] = False
                if self.mode == 0:
                    if ret != self.settings.XNEWA_SORT_RECORDING:
                        addon = Addon()
                        addon.setSetting(id='recordingSort',value=str(ret))
                        self.settings.XNEWA_SORT_RECORDING = ret
                        self.xnewa.cleanCache('summary.List')
                else:
                    if ret != self.settings.XNEWA_SORT_EPISODE:
                        addon = Addon()
                        addon.setSetting(id='episodeSort',value=str(ret))
                        self.settings.XNEWA_SORT_EPISODE = ret
                        self.xnewa.cleanCache('recentRecordings*.p')
                self.render()


    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        #log.debug('Key got hit: %s   Current focus: %s' % (ui.toString(action), self.getFocusId()))
        if self.mode == 1 and (action.getId() == ACTION_PAUSE or action.getId() == 58):
            if self.programsListBox.getSelectedItem().isSelected():
                self.programsListBox.getSelectedItem().select(False)
                self.selections -= 1
            else:
                self.programsListBox.getSelectedItem().select(True)
                self.selections += 1
            if self.selections > 0:
                self.win.setProperty('tagged', 'true')
            else:
                self.win.setProperty('tagged', 'false')
        elif  action.getId() in CONTEXT_MENU or action.getButtonCode() in CONTEXT_MENU:
            if self.selections > 0:
                for i in range(self.programsListBox.size()):
                    if self.programsListBox.getListItem(i).isSelected():
                        print(self.programsListBox.getListItem(i).getProperty('oid'))
        elif action.getId() in (EXIT_SCRIPT) or action.getButtonCode()  in (EXIT_SCRIPT):
            if self.filtered:
                self.xnewa.cleanCache('recentRecordings*.p')
                self.xnewa.cleanCache('summary.List')
            if self.mode == 1:
                self.mode = 0;
                self.render()
            else:
                self.closed = True
                self.close()

    def goEditSchedule(self):

        from . import details

        if self.mode == 0:
            self.showPosition = self.programsListBox.getSelectedPosition()
            self.show = self.recentData[self.showPosition]['title']
            if self.recentData[self.showPosition]['count'] != 1:
                self.mode = 1
                self.render()
                return
            self.recentData1 = self.xnewa.getRecentRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW,showName=self.show,sortTitle=self.sortTitle[1],sortDateDown=self.sortDate[1])
            self.render
            oid = self.recentData1[0]['recording_oid']
        else:
            oid = self.recentData[self.programsListBox.getSelectedPosition()]['recording_oid']

        detailDialog = details.DetailDialog("nextpvr_recording_details.xml", WHERE_AM_I,self.settings.XNEWA_SKIN, xnewa=self.xnewa, settings=self.settings, oid=oid, type="R", offline=self.xnewa.offline)
        detailDialog.doModal()
        if detailDialog.returnvalue is not None:
            if detailDialog.returnvalue == 'DEL':
                self.xnewa.cleanCache('recentRecordings*.p')
                self.xnewa.cleanCache('summary.List')
                self.mode = 0
            self.render()

    def render(self):
        self.win.setProperty('busy', 'true')
        self.programsListBox.reset()
        listItems = []
        if self.xnewa.offline == True or self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
            try:
                if self.mode == 1:
                    self.win.setProperty('recordings', 'true')
                    self.recentData = self.xnewa.getRecentRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW,showName=self.show,sortTitle=self.sortTitle[1],sortDateDown=self.sortDate[1],recDir=self.recDir)
                    if len(self.recentData) > 0:
                        if self.settings.XNEWA_SORT_EPISODE == 3:
                            self.recentData = sorted(self.recentData, key = lambda x: (x['season'], x['episode']))
                        previous = None
                        for i, t in enumerate(self.recentData):
                            if t:
                                #print ( 'the airdate for %s is %s' % (t['title'], t['start'].strftime( xbmc.getRegion('datelong') )) )
                                listItem = xbmcgui.ListItem('Row %d' % i)
                                airdate, previous = self.formattedAirDate(previous, self.xnewa.formatDate(t['start']))
                                listItem.setProperty('airdate', airdate)
                                listItem.setProperty('airdate_long',  self.xnewa.formatDate(t['start'], withyear=True))
                                if ( t['significance'] == ''):
                                    listItem.setProperty('title', t['title'])
                                else:
                                    listItem.setProperty('title', '{0} : {1}'.format(t['title'],t['significance']))


                                listItem.setProperty('status', t['status'])
                                listItem.setProperty('start', self.xnewa.formatTime(t['start']))
                                listItem.setProperty('end', self.xnewa.formatTime(t['end']))
                                duration = ((t['end'] - t['start']).seconds) // 60
                                listItem.setProperty('duration', str(duration) )
                                listItem.setProperty('channel', t['channel'][0])
                                listItem.setProperty('description', t['desc'])
                                if t['season'] == 0:
                                    listItem.setProperty('episode', t['subtitle'])
                                else:
                                    listItem.setProperty('episode','({0}x{1}) {2}'.format(t['season'],t['episode'],t['subtitle']))
                                listItem.setProperty('oid', str(t['recording_oid']))
                                listItems.append(listItem)
                            else:
                                i = i - 1
                        if i==0:
                            self.sortButton.setVisible(False)
                        newPosition = 0
                else:
                    xbmc.log( 'calling summary for recDir ' + str(self.recDir))
                    self.recentData = self.xnewa.getRecordingsSummary(self.settings.NextPVR_USER, self.settings.NextPVR_PW,self.sortTitle[0],not self.sortDate[0],self.recDir)
                    self.win.setProperty('recordings', 'false')
                    previous = None
                    for i, t in enumerate(self.recentData):
                        if t:
                            listItem = xbmcgui.ListItem('Row %d' % i)
                            airdate, previous = self.formattedAirDate(previous, self.xnewa.formatDate(t['start'], gmtoffset=True))
                            listItem.setProperty('airdate', airdate)
                            listItem.setProperty('airdate_long',  self.xnewa.formatDate(t['start'], withyear=True))
                            listItem.setProperty('title', t['title'])
                            showIcon = self.xnewa.getShowIcon(t['title'])
                            listItem.setProperty('showicon',showIcon)
                            listItem.setProperty('count', str(t['count']) )
                            listItems.append(listItem)
                        else:
                            i = i - 1
                    newPosition = self.showPosition
                if len(listItems) > 0:
                    self.programsListBox.addItems(listItems)
                    self.programsListBox.selectItem(newPosition)
                    self.win.setFocusId(600)
                else:
                    self.win.setFocusId(999)
            except:
                self.win.setProperty('busy', 'false')
                xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), '%s!' % smartUTF8(__language__(30109)))
            self.sortButton.setVisible(True)
            self.win.setProperty('busy', 'false')
        else:
            xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), '%s!' % smartUTF8(__language__(30109)))
            self.close()

    def formattedAirDate(self, previous, current):
        result = ''
        if not previous or previous != current:
            today = self.xnewa.formatDate(datetime.date.today())
            if current == today:
                result = smartUTF8(__language__(30133))
            else:
                yesterday = self.xnewa.formatDate(datetime.date.today() + datetime.timedelta(days=-1))
                if current == yesterday:
                    result = smartUTF8(__language__(30150))
                else:
                    result = current
        return result, current


    def processFile(self, process_type):
        deleteAll = None
        archiveSetting = None
        refresh = False
        for i in range(self.programsListBox.size()):
            if self.programsListBox.getListItem(i).isSelected():
                oid = int(self.programsListBox.getListItem(i).getProperty('oid'))
                for j,progDetails in enumerate(self.recentData):
                    if progDetails:
                        if oid == progDetails['recording_oid']:
                            if process_type == __language__(30039):
                                if archiveSetting == None:
                                    choices = list(self.xnewa.RecDirs.keys())
                                    archiveSetting =  xbmcgui.Dialog().select(smartUTF8(__language__(30115)), choices)
                                    if archiveSetting != -1:
                                        dialog = xbmcgui.Dialog()
                                        ret = dialog.yesno(choices[archiveSetting], '%s %s?' % (smartUTF8(__language__(30116)), choices[archiveSetting]))
                                        if ret != 1:
                                            archiveSetting = -1

                                if archiveSetting != -1:
                                    if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                                        try:
                                            if self.xnewa.archiveRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW,progDetails['recording_oid'], choices[archiveSetting]  ):
                                                xbmc.log('file archived')
                                            else:
                                                xbmcgui.Dialog().ok(smartUTF8(__language__(30104)), smartUTF8(__language__(30105)))
                                        except:
                                            xbmcgui.Dialog().ok(smartUTF8(__language__(30104)), smartUTF8(__language__(30105)))


                            elif process_type == __language__(32003):
                                if progDetails['status'] == "Failed":
                                    ret = xbmcgui.Dialog().yesno('%s %s' % (smartUTF8(__language__(30135)), progDetails['title']), '%s\n%s?' % (smartUTF8(__language__(30112)), progDetails['title']))
                                elif progDetails['status'] != "In-Progress" and 'filename' in progDetails:
                                    ret = xbmcgui.Dialog().yesno('%s %s' % (smartUTF8(__language__(30054)), progDetails['title']), '%s\n%s?' % (smartUTF8(__language__(30111)), progDetails['filename']))
                                else:
                                    break
                                self.returnvalue = "DEL"
                                if ret == 1:
                                    if self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, progDetails):
                                        refresh = True

                            elif process_type == __language__(30054):
                                if deleteAll==None:
                                    ret = xbmcgui.Dialog().yesno('%s %s' % (__language__(30054), progDetails['title']), '%s %d %s?' % (__language__(30111), self.selections , 'marked recording(s)' ))
                                    if ret == 1 :
                                        deleteAll = True
                                    else:
                                        deleteAll = False
                                if deleteAll==True:
                                    if self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, progDetails):
                                        refresh = True
                                else:
                                    break
                            elif process_type == __language__(32004):
                                duration = progDetails['duration']
                                if duration == 0:
                                    duration = int(self.programsListBox.getListItem(i).getProperty('duration')) * 60
                                if duration > int(progDetails['resume']):
                                    retval = self.xnewa.setLibraryPlaybackPosition(progDetails['filename'], duration, duration )
                            elif process_type == __language__(30034):
                                if int(progDetails['resume']) !=0 :
                                    duration = progDetails['duration']
                                    if duration == 0:
                                        duration = int(self.programsListBox.getListItem(i).getProperty('duration')) * 60
                                    retval = self.xnewa.setLibraryPlaybackPosition(progDetails['filename'], 0, duration )
                            else:
                                xbmc.log('Unknown process type')

                            self.programsListBox.getListItem(i).select(False)
                            self.selections -= 1


        if refresh == True:
            self.xnewa.cleanCache('recentRecordings*.p')
            self.xnewa.cleanCache('summary.List')
            self.mode = 0
