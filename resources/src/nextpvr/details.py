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
import xbmcvfs
import xbmcplugin
from datetime import datetime
from datetime import timedelta
from time import sleep
import math
from XNEWAGlobals import *
from XBMCJSON import *
from xbmcaddon import Addon
from fix_utf8 import smartUTF8

__language__ = Addon('script.xbmc.x-newa').getLocalizedString

# =============================================================================
class DetailDialog(xbmcgui.WindowXMLDialog):
    """
    Show details of show, recording and recurring recording
    """

    def __init__(self, *args, **kwargs):
        # Need to get: oid and xnewa....
        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']

        self.oid = kwargs['oid']
        self.oid_type = kwargs['type']
        if kwargs.has_key('epg') == True:
            self.epg = True
        else:
            self.epg = False
        self.returnvalue = None

        self.win = None
        self.shouldRefresh = False
        self.player = None
        self.xbmcResume = -1
        self.xbmcId = -1
        self.movie = False
        self.cancelOID = 0
        self.playlist = None
        print repr(self)

    def onInit(self):
        self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())

        print self.oid_type
        if self.oid_type !="R" and self.oid_type !="E":
            self.genre1Image = self.getControl(306)
            self.genre2Image = self.getControl(307)
            self.genre3Image = self.getControl(308)
        else:
            self.genre1Image = None
            self.genre2Image = None
            self.genre3Image = None
            self.statusLabel = None

        self.showImage = self.getControl(302)
        self.title = self.getControl(303)
        self.channel = self.getControl(304)
        self.channelImage = self.getControl(305)

        self.statusLabel = self.getControl(309)
        self.subtitleLabel = self.getControl(310)
        self.descLabel = self.getControl(311)
        self.recordingTypeLabel = self.getControl(312)
        self.recordingTypeDetails = self.getControl(313)
        self.timeStartLabel = self.getControl(314)
        self.timeEndLabel = self.getControl(315)
        self.dateLabel = self.getControl(316)
        self.dateLongLabel = self.getControl(317)
        self.durationLabel = self.getControl(318)

        if self.oid_type !="R" and self.oid_type !="E":
            self.showSeperator = self.getControl(4)
            self.placeFiller = self.getControl(7777)
            self.prePadding = self.getControl(202)
            self.postPadding = self.getControl(203)
            self.recDirId = self.getControl(204)
            self.extendTime = self.getControl(205)
            self.timeSlot = self.getControl(206)
            self.keepRecs = self.getControl(207)
            self.priority = self.getControl(208)
            self.qualityControl = self.getControl(205)
            self.scheduleType = self.getControl(201)
        else:
            self.scheduleType = None
            self.qualityControl = None
            self.prePadding = None
            self.postPadding = None
            self.recDirId = None
            self.extendTime = None
            self.timeSlot = None
            self.keepRecs = None
            self.priority = None
        if self.oid_type !="R"  and self.oid_type !="E":
            self.archiveButton = None
            self.saveButton = self.getControl(250)
            self.resumeButton = None
            if self.oid_type !="F":
                self.recordButton = self.getControl(252)
                self.quickrecordButton = None
            else:
                self.recordButton = self.getControl(252)
                self.quickrecordButton = None
        else:
            self.archiveButton = self.getControl(257)
            self.saveButton = None
            self.recordButton =  self.getControl(260)
            self.scheduleType = None
            self.resumeButton = self.getControl(258)
            self.unwatchButton = self.getControl(259)
            if self.oid_type == "E":
                self.recordButton = self.getControl(260)
                self.quickrecordButton = self.getControl(252)
                self.archiveButton.setVisible(False)
            else:
                self.quickrecordButton = self.getControl(252)
                #self.archiveButton.setLabel(self.oid_type)


        self.deleteButton = self.getControl(251)
        self.closeButton = self.getControl(253)
        self.playButton = self.getControl(254)
        self.playButton.setVisible(False)

        self._getDetails()
        if self.oid_type =="P":
            self.goRecord()
        else:
            self._updateView()

    def onFocus(self, controlId):
        pass

    def getPlayer(self):
        while self.player == None:
            pass
        while self.player.is_active == False:
            print 'still waiting'
        while True:
            if self.player.is_started and self.player.isPlayingVideo():
                break;
            else:
                self.player.sleep(100)
        return self.player

    def onAction(self, action):
        #f actionID in MOVEMENT_RIGHT or buttonID in MOVEMENT_RIGHT:
        #    if self.player != None:
        #        self.player.seekTime(50)
        if action.getId() in (EXIT_SCRIPT) or action.getButtonCode()  in (EXIT_SCRIPT):
            self.close()

    def goRecord(self):
        if self.oid_type =="E":
            self.returnvalue = "PICK"
            self.close("PICK")
        else:
            if self.xnewa.defaultSchedule == None:
                self.xnewa.getDefaultSchedule()
            self.detailData['status'] = "Pending"
            self.detailData['recquality'] = "High"
            self.detailData['prepadding'] = str(self.xnewa.defaultSchedule['pre_padding_min'])
            self.detailData['postpadding'] = str(self.xnewa.defaultSchedule['post_padding_min'])
            self.detailData['rectype'] = "Record Once"
            self.detailData['maxrecs'] = str(self.xnewa.defaultSchedule['days_to_keep'])
            self.detailData['recording_oid'] = 0
            self.detailData['directory'] = "Default"
            self._updateView()

    def error_message(self):
        dialog = xbmcgui.Dialog()
        dialog.ok(smartUTF8(__language__(30104)), smartUTF8(__language__(30105)))

    def onClick(self, controlId):
        source = self.getControl(controlId)
        if self.closeButton == source:
            self.close()
        elif self.recordButton == source:
            self.goRecord()
            self.close()
        elif self.saveButton == source or self.quickrecordButton == source:
            if self.quickrecordButton == source:
                if self.xnewa.defaultSchedule == None:
                    self.xnewa.getDefaultSchedule()
                self.detailData['status'] = "Pending"
                self.detailData['recquality'] = "High"
                self.detailData['prepadding'] = str(self.xnewa.defaultSchedule['pre_padding_min'])
                self.detailData['postpadding'] = str(self.xnewa.defaultSchedule['post_padding_min'])
                self.detailData['rectype'] = "Record Once"
                self.detailData['maxrecs'] = str(self.xnewa.defaultSchedule['days_to_keep'])
                self.detailData['recording_oid'] = 0
                self.detailData['directory'] = "Default"

            if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                try:
                    if self.detailData['recording_oid'] == 0:
                        responseCode = self.xnewa.scheduleRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData)
                        if responseCode == 200:
                            self.returnvalue = "REC"
                            self.close("REC")
                        elif responseCode == 500:
                            print self.xnewa.Last_Error
                            dialog = xbmcgui.Dialog()
                            ok = dialog.ok(smartUTF8(__language__(30110)), self.xnewa.Last_Error)
                        else:
                            self.error_message()
                    else:
                        if self.detailData['priority'] == __language__(32001) or self.detailData['priority'] == __language__(32002):
                            scheduleData = self.xnewa.getScheduledRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW)
                            import operator
                            scheduleData.sort(key=operator.itemgetter('priority'))
                            found = -1
                            for i, t in enumerate(scheduleData):
                                if t['recording_oid'] == self.detailData['recording_oid']:
                                    found = i
                                    break
                            #print scheduleData[found]
                            if self.detailData['priority'] == __language__(32001):
                                if found == len(scheduleData) -1:
                                    found = -1
                                else:
                                    updatePriority = found -1
                            elif self.detailData['priority'] == __language__(32002):
                                if found == 0:
                                    found = -1
                                else:
                                    updatePriority = found + 1
                            if found != -1:
                                detailDataSwap = self.xnewa.getDetails(self.settings.NextPVR_USER, self.settings.NextPVR_PW, scheduleData[updatePriority]['recording_oid'], 'F', self.settings.NextPVR_ICON_DL )
                                self.detailData['priority'] = detailDataSwap['priority']
                                detailDataSwap['priority'] = scheduleData[found]['priority']
                                self.xnewa.updateRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, detailDataSwap )

                        if self.xnewa.updateRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData):
                            self.returnvalue = "REC"
                            self.close("REC")
                        else:
                            self.error_message()

                except:
                    xbmcgui.Dialog().ok(smartUTF8(__language__(30104)), smartUTF8(__language__(30105)))
        elif self.deleteButton == source:
            #print self.detailData
            if self.detailData['status'] != "In-Progress" and self.detailData.has_key('filename'):
                ret = xbmcgui.Dialog().yesno('%s %s' % (smartUTF8(__language__(30054)), self.detailData['title']), '%s\n%s?' % (smartUTF8(__language__(30111)), self.detailData['filename']))
                self.returnvalue = "DEL"
            elif self.detailData['status'] == "Failed":
                ret = xbmcgui.Dialog().yesno('%s %s' % (smartUTF8(__language__(30135)), self.detailData['title']), '%s\n%s?' % (smartUTF8(__language__(30112)), self.detailData['title']))
                self.returnvalue = "DEL"
            else:
                ret = xbmcgui.Dialog().yesno( '%s %s' % (smartUTF8(__language__(30038)), smartUTF8(__language__(30048))), '%s\n%s' % (smartUTF8(__language__(30113)), self.detailData['title']) )
                self.returnvalue = "CAN"
            if ret == 1:
                if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                    try:
                        if self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData):
                            if self.settings.XNEWA_EPISODE == True and self.xbmcId > 0 and self.detailData['status'] != "In-Progress":
                                myJSON = XBMCJSON()
                                param = {}
                                if self.detailData['movie'] == True:
                                    param['movieid'] = self.xbmcId
                                    response = myJSON.VideoLibrary.RemoveMovie(param)
                                else:
                                    param['tvshowid'] = self.xbmcId
                                    response = myJSON.VideoLibrary.RemoveTVShow(param)

                                print type(response)
                                try:
                                    print response['result']
                                except:
                                    print response['error']

                            self.shouldRefresh = True
                            self.close("DEL")

                        else:
                            self.error_message()
                    except:
                        xbmcgui.Dialog().ok(smartUTF8(__language__(30104)), smartUTF8(__language__(30105)))
                else:
                    xbmcgui.Dialog().ok(smartUTF8(__language__(30104)), smartUTF8(__language__(30114)))
        elif self.archiveButton != None and self.archiveButton == source:
            choices = self.xnewa.RecDirs.keys()
            setting =  xbmcgui.Dialog().select(smartUTF8(__language__(30115)), choices)
            print setting
            if setting != -1:
                dialog = xbmcgui.Dialog()
                ret = dialog.yesno(choices[setting], '%s %s?' % (smartUTF8(__language__(30116)), choices[setting]))
                if ret == 1:
                    print self.detailData['recording_oid']
                    print choices[setting]
                    if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                        try:
                            if self.xnewa.archiveRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData['recording_oid'], choices[setting]  ):
                                print 'file archived'
                            else:
                                xbmcgui.Dialog().ok(smartUTF8(__language__(30104)), smartUTF8(__language__(30105)))
                        except:
                            xbmcgui.Dialog().ok(smartUTF8(__language__(30104)), smartUTF8(__language__(30105)))
            xbmcgui.WindowXML.setFocus(self, self.archiveButton)
        elif self.scheduleType == source:
            self.detailData['rectype']
            if self.detailData['recording_oid'] == 0: # Only for new recording
                    self.detailData['rectype'] = self._pickFromList("Select recording type", ["Record Once",
                    "Record Season (NEW episodes on this channel)",
                    "Record Season (All episodes on this channel)",
                    "Record Season (Daily, this timeslot)",
                    "Record Season (Weekly, this timeslot)",
                    "Record Season (Monday-Friday, this timeslot)",
                    "Record Season (Weekends, this timeslot)",
                    "Record All Episodes, All Channels"], self.detailData['rectype'])
                    self._updateView()
        elif self.qualityControl == source:
            self.detailData['recquality'] = self._pickFromList("Select recording quality", ["Best", "Better", "Good", "Default"], self.detailData['recquality'])
            self._updateView()
        elif self.prePadding == source:
            self.detailData['prepadding'] = str(self._getNumber("Select prepadding minutes", self.detailData['prepadding'], -5, 30))
            self._updateView()
        elif self.postPadding == source:
            self.detailData['postpadding'] = str(self._getNumber("Select postpadding minutes", self.detailData['postpadding'], 0, 120))
            self._updateView()
        elif self.extendTime == source:
            self.detailData['extendend'] = str(self._getNumber("Select time extenstion (minutes)", 0, 0, 30))
            self._updateView()
        elif self.keepRecs == source:
            self.detailData['maxrecs'] = str(self._getNumber("Select recordings to keep (0 means all)", self.detailData['maxrecs'], 0, 30))
            self._updateView()
        elif self.recDirId == source:
            self.detailData['directory'] = self._pickFromList("Recording Directory", self.xnewa.RecDirs.keys(), self.detailData['directory'])
            self._updateView()
        elif self.priority == source:
            if self.detailData['priority'] != 0:
                choices = []
                choices.append(__language__(30038))
                choices.append(__language__(32001))
                choices.append(__language__(32002))
                newPriority = self._pickFromList(__language__(30042), choices, __language__(30038))
                if newPriority != __language__(30038):
                    self.detailData['priority'] = newPriority
                self._updateView()
        elif self.playButton == source or self.resumeButton == source:
            from threading import Thread
            t = Thread(target=self._myPlayer, args=(None,source,))
            t.start()

    def _myPlayer(self, detail=None, button=None, isMin = False, Audio = False):
        import xbmcgui,xbmc
        if detail is not None:
            self.detailData = detail

        isTimeShifted = False
        self.urly = self.xnewa.getURL()
        isVlc = False
        myDlg = None
        from uuid import getnode as get_mac
        mac = get_mac()
        #self.player = XBMCPlayer(xbmc.PLAYER_CORE_AUTO,settings=self.settings, xnewa=self.xnewa)
        self.player = XBMCPlayer(settings=self.settings, xnewa=self.xnewa)
        if self.player.isPlaying():
            isMin = True
            self.player.stop()
            print "vlc stopped"
            self.player = XBMCPlayer(settings=self.settings, xnewa=self.xnewa)
        print "started player"
        if self.detailData.has_key('playlist') == True:
            Audio = True
            url = self.detailData['playlist']
            print url
        elif self.detailData.has_key('filename') == False:
            self.channelIcon = self.xnewa.getShowIcon(self.detailData['title'])
            if self.channelIcon == None:
                self.channelIcon = self.xnewa.getChannelIcon(self.detailData['channel'][0])
            print self.detailData

            if self.channelIcon is not None:
                listitem = xbmcgui.ListItem(self.detailData["title"], thumbnailImage=self.channelIcon)
            else:
                listitem = xbmcgui.ListItem(self.detailData['title'])

            if self.detailData['season'] !=0:
                infolabels={ "Title": self.detailData['title'], 'tvshowtitle':self.detailData['subtitle'], 'season': self.detailData['season'], 'episode': self.detailData['episode'],'mediatype': 'episode','plot': self.detailData['desc'] }
            elif self.detailData['subtitle'] != '':
                infolabels={ "Title": self.detailData['title'], 'tvshowtitle':self.detailData['subtitle'],'mediatype': 'episode','plot': self.detailData['desc'] }
            else:
                infolabels={ "Title": self.detailData['title'],'plot': self.detailData['desc']}
            listitem.setInfo( type="video", infoLabels=infolabels )


            if len(self.detailData['channel']) == 2:
                url = self.urly + "/live?channel=" + self.detailData['channel'][1]
            elif self.detailData['channel'][2] == '0':
                url = self.urly + "/live?channel=" + self.detailData['channel'][1]
            else:
                url = self.urly + "/live?channel=" + self.detailData['channel'][1]+'.'+ self.detailData['channel'][2]
            url += self.xnewa.client
            if self.settings.NextPVR_STREAM == 'VLC':
                # vlc streaming test
                print self.detailData['program_oid']
                if self.xnewa.startVlcFileByEPGEventOID(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData['program_oid']):
                    url = self.xnewa.getVlcURL()
                    xbmc.sleep(self.settings.XNEWA_PREBUFFER)
                    isVlc = True
            elif self.settings.NextPVR_STREAM == 'Direct':
                import direct
                durl = direct.LiveTV(self.detailData['channel'])
                if durl != None:
                    url = durl
            elif self.settings.NextPVR_STREAM == 'HDHR':
                from  hdhr.pyhdhr import PyHDHR
                mypy = PyHDHR();
                try:
                    if self.detailData['channel'][2] == '0':
                        strChannel = self.detailData['channel'][1]
                    else:
                        strChannel = self.detailData['channel'][1]+'.'+ self.detailData['channel'][2]
                    durls = mypy.getLiveTVURLList(strChannel)
                    print durls
                    if durls:
                        xbmc.PlayList(0).clear()
                        for durl in durls:
                            if self.channelIcon is not None:
                                newlistitem = xbmcgui.ListItem(self.detailData["title"], thumbnailImage=self.channelIcon)
                            else:
                                newlistitem = xbmcgui.ListItem(self.detailData['title'])
                            newlistitem.setInfo( type="video", infoLabels=infolabels )
                            xbmc.PlayList(0).add(durl,newlistitem)
                        print xbmc.PlayList(0).size()
                        self.playlist = xbmc.PlayList(0)
                except:
                    print 'HDHR problem'
            elif self.settings.NextPVR_STREAM == 'Timeshift':

                if self.xnewa.defaultSchedule == None:
                    self.xnewa.getDefaultSchedule()
                self.detailData['status'] = "Pending"
                self.detailData['recquality'] = "High"
                self.detailData['prepadding'] = 0
                self.detailData['postpadding'] = 60
                self.detailData['rectype'] = "Record Once"
                self.detailData['maxrecs'] = str(self.xnewa.defaultSchedule['days_to_keep'])
                self.detailData['recording_oid'] = 0
                self.detailData['directory'] = "Default"
                if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                    if self.detailData['recording_oid'] == 0:
                        responseCode = self.xnewa.scheduleRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData)

                xbmc.executebuiltin("ActivateWindow(busydialog)")
                xbmc.sleep(1200)

                print 'Timeshift: buffered'
                self.player.setTimeShift(False)


                print self.settings.XNEWA_PREBUFFER
                for x in range(0, 4):
                    xbmc.sleep(self.settings.XNEWA_PREBUFFER)

                self.detailData = self.xnewa.getDetails(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData['program_oid'], 'E', False )
                print self.detailData
                durl = self.detailData['filename']
                if durl[0:2]=='\\\\':
                    durl = 'smb:'+self.detailData['filename'].replace('\\','/')
                elif os.name != 'nt':
                    durl = durl.replace('\\','/')
                try:
                    durl = durl.encode('utf-8')
                except:
                    pass
                print durl
                if not xbmcvfs.exists(durl):
                    print 'shifting not found'
                    isTimeShifted = False
                    try:
                        self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData)
                        self.detailData['status'] = 'completed'
                        xbmc.sleep(500)
                        self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData)
                    except:
                        print 'cancel'
                    xbmc.executebuiltin("Dialog.Close(busydialog)")
                else:
                    isTimeShifted = True
                    self.cancelOID =  self.detailData['recording_oid']
                    url = durl

            elif self.settings.NextPVR_STREAM == 'Timeshift1':

                # vlc streaming test
                if self.player.isPlaying():
                #                    if self.xnewa.stopVlcStreamProcessObject(self.settings.NextPVR_USER, self.settings.NextPVR_PW):
                    print "vlc timeshift stopped"
                print "vlc timeshift started"
                print self.detailData['program_oid']
                print self.detailData['channel'][1]
                print self.settings.XNEWA_PREBUFFER
                myDlg = xbmcgui.DialogProgress()
                myDlg.create("Timeshifting", "")
                myDlg.update(5, "Starting NextPVR playback")
                if self.detailData['channel'][2] == '0':
                    vlc_channel = self.detailData['channel'][1]
                else:
                    vlc_channel = self.detailData['channel'][1]+'.'+ self.detailData['channel'][2]
                if self.xnewa.startVlcLiveStreamByChannelNumberObject(self.settings.NextPVR_USER, self.settings.NextPVR_PW, vlc_channel):
                    url = self.xnewa.getVlcURL()
                    if url.startswith('\\'):
                        url = 'smb:' + url.replace("\\","/")
                    isVlc = True
                    for x in range(0, 3):
                        myDlg.update(10+x*10, "Pre-buffering")
                        xbmc.sleep(self.settings.XNEWA_PREBUFFER)
                    print 'Timeshift: post sleep'
                    if xbmcvfs.exists(url) == False:
                        myDlg.update(45, "Second chance buffering ...")
                        print 'Timeshift: Not found sleep'
                        xbmc.sleep(4000)
                    print 'Timeshift: buffered'
                    myDlg.update(50, "Starting player")
                    isTimeShifted = True
                    self.player.setTimeShift(True)
                else:
                    print "Fall back to default"
                    myDlg.close()
            elif self.settings.NextPVR_STREAM == 'PVR' and xbmc.getCondVisibility('System.HasPVRAddon') :
                channels = self.xnewa.getPVRChannels()
                if channels != None:
                    print self.detailData
                    #num = str(self.detailData['channel'][0]))
                    chnum = str(self.detailData['channel_oid'])
                    url = 'pvr://channels/tv/All channels/pvr.nextpvr_' + chnum + '.pvr'
                    print url
            elif self.settings.NextPVR_STREAM == 'Transcode':
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                self.xnewa.startTranscodeLiveStreamByChannelNumber( self.detailData['channel'][1])
                url = self.urly + '/services/service?method=channel.transcode.m3u8' + self.xnewa.client
                isTimeShifted = True
                self.player.setTimeShift(True)
                xbmc.sleep(500)
                for x in range(0, 20):
                    xbmc.sleep(500)
                    if self.xnewa.getTranscodeStatus()==100:
                        break
                xbmc.executebuiltin("Dialog.Close(busydialog)")

        else:
            try:
                self.showIcon = self.xnewa.getShowIcon(self.detailData['title'])
            except:
				self.showIcon = None
            if self.showIcon is not None:
                listitem = xbmcgui.ListItem(self.detailData['title'], thumbnailImage=self.showIcon)
            else:
                listitem = xbmcgui.ListItem(self.detailData['title'])

            if self.detailData['season'] !=0:
                infolabels={"Title": self.detailData['title'], 'tvshowtitle':self.detailData['subtitle'], 'season': self.detailData['season'], 'episode': self.detailData['episode'],'mediatype': 'episode','plot': self.detailData['desc']}
            elif self.detailData['subtitle'] != '':
                infolabels={"Title": self.detailData['title'], 'tvshowtitle':self.detailData['subtitle'],'mediatype': 'episode','plot': self.detailData['desc']}
            else:
                infolabels={"Title": self.detailData['title'],'plot': self.detailData['desc']}
            print infolabels
            listitem.setInfo( type="Video", infoLabels=infolabels )
            #listitem.setInfo('video',{'Genre':'Comedy','title':'ttvvv','tagline':'dddmedy'})
            if self.settings.NextPVR_STREAM != 'Transcode':
                bookmarkSecs = 0
                if self.detailData.has_key('nextUrl') == False:
                    if self.resumeButton == button:
                        bookmarkSecs = self.detailData['resume']
                        #import datetime
                        #formatSeconds = str(datetime.timedelta(seconds=bookmarkSecs))
                        #question = 'Resume from %s?' % formatSeconds
                        #resume = xbmcgui.Dialog().yesno(self.detailData['title'],'', question,'','Resume','Beginning')
                        #print resume
                        #if resume== 0:
                        listitem.setProperty('startoffset',str(bookmarkSecs))
                else:
                    bookmarkSecs = self.detailData['bookmarkSecs']
                    listitem.setProperty('startoffset',str(bookmarkSecs))

            #listitem.setProperty('startoffset',str(bookmarkSecs))
            url = self.detailData['filename']
            url = url.replace('\\bdmv\\','\\BDMV\\')
            if url[0:2]=='\\\\':
                url = 'smb:'+self.detailData['filename'].replace('\\','/')
            elif os.name != 'nt':
                url = url.replace('\\','/')
            try:
                url = url.encode('utf-8')
            except:
                pass
            print url
            if url.startswith('plugin') == False and url.startswith('http') == False and url.startswith('rtmp') == False and url.startswith('mms') == False and (not xbmcvfs.exists(url)  or self.settings.NextPVR_STREAM == 'VLC') :
                print "not found"

                if self.xnewa.offline == True:
                    xbmcgui.Dialog().ok(smartUTF8(__language__(30136)), smartUTF8(__language__(30117)))
                    return

                if self.detailData.has_key('nextUrl') == False:
                    url = self.urly + "/live?recording=" +str(self.detailData['recording_oid']) + self.xnewa.client
                else:
                    import urllib
                    myFile = urllib.quote(self.detailData['nextUrl'].encode('utf-8'),'\\/:%.?=;')

                    if myFile.startswith('/stream?f='):
                        myFile = myFile + '&mode=http'
                    myFile += self.xnewa.client
                    print myFile
                    url = self.urly + myFile
                if self.settings.NextPVR_STREAM == 'Direct':
                    import urllib
                    #url = your url here
                    f1 = urllib.quote(url)
                elif self.settings.NextPVR_STREAM == 'VLC':
                    # vlc streaming test
                    print self.detailData
                    if self.xnewa.startVlcFileByScheduleOID(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData['recording_oid']):
                        url = self.xnewa.getVlcURL()
                        isVlc = True
            if self.settings.NextPVR_STREAM == 'Transcode' and self.detailData['recording_oid'] != 0:
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                self.xnewa.startTranscodeRecording( str(self.detailData['recording_oid']))
                url = self.urly + '/services/service?method=recording.transcode.m3u8' + self.xnewa.client
                isTimeShifted = True
                self.player.setTimeShift(True)
                xbmc.sleep(500)
                for x in range(0, 20):
                    if self.xnewa.getTranscodeStatus()==100:
                        xbmc.sleep(500)
                        break
                    xbmc.sleep(500)
                xbmc.executebuiltin("Dialog.Close(busydialog)")

        self.close()
        if self.detailData['movie'] == True and self.xbmcId > 0:
            myJSON = XBMCJSON()
            param = {}
            subparam = {}
            subparam['movieid'] = self.xbmcId
            param['item'] = subparam
            if bookmarkSecs > 0:
                #resume = {}
                #resume['item'] = param
                m, s = divmod(bookmarkSecs, 60)
                h, m = divmod(m, 60)
                #resume['Player.Position.Time'] =
                param['options'] = {'resume' : {'hours': h, 'minutes': m, 'seconds' : s, 'milliseconds':0} }
            response = myJSON.Player.Open(param)
            print response
        else:
            if Audio == False:
                print "Playing " + url
                if self.playlist != None:
                    self.player.play( self.playlist, listitem, windowed=isMin )
                else:
                    self.player.play( url, listitem, windowed=isMin )
            else:
                self.player.play( url )
            print 'player started'
#        ...
        self._lastPos = 0
        self._duration = -2
        print 'entering loop'
        while self.player.is_active:
            if self.player.is_started and self.player.isPlayingVideo():
                if self.player.getTotalTime() > 10:
                    if self._duration < 0:
                        if myDlg != None:
                            myDlg.close()
                            myDlg = None
                        self._duration = 0
                    else:
                        self.player.sendHeartbeat()
                        try:
                            self._lastPos = self.player.getTime()
                            self._duration = self.player.getTotalTime()
                        except:
                            print "could net get last"
                elif self._duration == -2:
                    if isTimeShifted:
                        if self.settings.NextPVR_STREAM == 'Timeshift':
                            self.player.pause()
                            for x in range(0, 4):
                                xbmc.sleep(self.settings.XNEWA_POSTBUFFER)
                            self.player.seekTime(0)
                            xbmc.sleep(200)
                            self.player.pause()
                            xbmc.executebuiltin("Dialog.Close(busydialog)")
                            print self.player.getTotalTime()
                    self._duration = -1

            self.player.sleep(250)

        self.player = None
        if self.detailData.has_key('filename') == True and self.xnewa.offline == False:
            if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                print self._duration
                print self.cancelOID
                if self.cancelOID != 0:
                    try:
                        self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData)
                        self.detailData['status'] = 'completed'
                        xbmc.sleep(500)
                        self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData)
                    except:
                        print 'cancel'
                else:
                    if self.detailData.has_key('library_duration'):
                        self._duration =  self.detailData['library_duration']
                    print self._duration
                    if self.detailData.has_key('recording_oid') == True:
                        retval = self.xnewa.setPlaybackPositionObject(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData, self._lastPos, self._duration )
                    else:
                        retval = self.xnewa.setLibraryPlaybackPosition(self.detailData['filename'], self._lastPos, self._duration )
            else:
                #todo cache playback
                pass
        if isVlc == True:
            if self.xnewa.stopVlcStreamProcess(self.settings.NextPVR_USER, self.settings.NextPVR_PW):
                print "vlc stopped"

        if self.settings.NextPVR_STREAM == 'Transcode' and self.detailData['recording_oid'] != 0:
            self.xnewa.sendTranscodeStop()
            print 'Stopping transcoding'


        print "ended"
    def _getDetails(self):
        self.win.setProperty('busy', 'true')
        if self.xnewa.offline == False and self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
            self.detailData = self.xnewa.getDetails(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.oid, self.oid_type, self.settings.NextPVR_ICON_DL )
        elif self.xnewa.offline == True:
            self.recentData = self.xnewa.getRecentRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW)
            self.detailData = None
            for i, t in enumerate(self.recentData):
                if t:
                    if t['recording_oid'] == self.oid:
                        self.detailData = t
                        break

        else:
            self.win.setProperty('busy', 'false')
            xbmcgui.Dialog().ok(smartUTF8(__language__(30104)), smartUTF8(__language__(30109)))
            self.close()
        self.win.setProperty('busy', 'false')

    def _updateView(self):
        self.win.setProperty('busy', 'true')
        self.title.setLabel(self.detailData['title'])
        if self.detailData['channel_oid']!=0:
            self.channel.setLabel(self.detailData['channel'][0])
        else:
            self.channel.setLabel('All Channels')
        #self.win.setProperty('title', self.detailData['title'])
        #self.win.setProperty('channel', self.detailData['channel'][0])
        #if self.heading is not None:
        #    self.channel.setLabel(self.detailData['channel'][0])

        if self.oid_type!="R" and self.oid_type !="E":
            self.win.setProperty('genre', str(self.detailData['genres']))


        self.channelIcon = self.xnewa.getChannelIcon(self.detailData['channel'][0])
        if self.channelIcon is not None:
            import sys
            #y = unicode(self.channelIcon,self.xnewa.getfilesystemencoding)
            #z = y.encode('utf-8')
            self.channelImage.setImage(self.channelIcon)

        if self.epg == True:
            if datetime.now() >= self.detailData['start'] and datetime.now() < self.detailData['end']:
                self.playButton.setVisible(True)
                if self.detailData['status'] != "In-Progress":
                    self.playButton.setLabel("Watch")

        elif self.detailData.has_key('filename') == False:
            self.playButton.setVisible(False)
        elif self.detailData['filename'] !=  '':
            self.playButton.setVisible(True)
        else:
            self.playButton.setVisible(False)

        self.showIcon = self.xnewa.getShowIcon(self.detailData['title'])
        if self.showIcon is not None:
            self.showImage.setImage(self.showIcon)

        if self.oid_type=="NOT USED":
            if len(self.detailData['genres']) > 0:
                self.genreIcon = self.xnewa.getGenreIcon(self.detailData['genres'][0])
                if self.genreIcon is not None:
                    self.genre1Image.setImage(self.genreIcon)

            if len(self.detailData['genres']) > 1:
                self.genreIcon = self.xnewa.getGenreIcon(self.detailData['genres'][1])
                if self.genreIcon is not None:
                    self.genre2Image.setImage(self.genreIcon)

            if len(self.detailData['genres']) > 2:
                self.genreIcon = self.xnewa.getGenreIcon(self.detailData['genres'][2])
                if self.genreIcon is not None:
                    self.genre3Image.setImage(self.genreIcon)

        if self.statusLabel is not None:
            self.statusLabel.setVisible(True)
            self.statusLabel.setLabel(self.detailData['status'])

        print self.detailData['status']
        print self.detailData['rectype']

        if self.detailData['rectype'] !="" and self.detailData['rectype'] != 'Record Once' and self.detailData['rectype'] != "Single"  and self.detailData['status'] != "Completed" and self.detailData['status'] != "In-Progress" and self.detailData['status'] != "Failed" and self.detailData['status'] != "Conflict" and self.detailData['rectype'] != "Multiple":
            print 'recurring'
            self.win.setProperty('heading', 'Recurring Recording Properties')
            self.recordingTypeLabel.setVisible(True)
            self.recordingTypeLabel.setLabel(smartUTF8(__language__(30007)))
            self.timeStartLabel.setLabel(self.xnewa.formatTime(self.detailData['start']))
            self.timeEndLabel.setLabel(self.xnewa.formatTime(self.detailData['end']))
            self.dateLabel.setLabel(self.xnewa.formatDate(self.detailData['start']))
            self.dateLongLabel.setLabel(self.xnewa.formatDate(self.detailData['start'], withyear=True))
            self.durationLabel.setLabel(str(int((self.detailData['end'] - self.detailData['start']).seconds / 60)))
            self.descLabel.setVisible(True)
            import re
            print self.detailData['desc']
            m = re.search('AdvancedRules\': u"(.+?)"', self.detailData['desc'])
            if m:
                found = '\nAdvanced Rule: ' + m.group(1)
                print found
            elif self.detailData['desc'].startswith('KEYWORD:'):
                found = '\n' + self.detailData['desc']
            else:
                found = ''
            try:
                if len(self.detailData['day'])==7:
                    self.recordingTypeDetails.setText('Daily' + found)
                else:
                    self.recordingTypeDetails.setText( "".join(self.detailData['day']) + found)
            except:
                self.descLabel.setText(self.detailData['desc'])

            if self.oid_type!="R"  and self.oid_type !="E":
                self.showSeperator.setVisible(True)

                #self.subtitleLabel.setVisible(False)
                #self.timeLabel.setVisible(True)
                #self.descLabel.setVisible(False)


                self.extendTime.setVisible(False)

                self.qualityControl.setLabel( "Quality:", label2=self.detailData['recquality'] )
                self.qualityControl.setVisible(False)
                self.prePadding.setLabel( "Pre-Padding (min.):", label2=self.detailData['prepadding'] )
                self.prePadding.setVisible(True)
                self.postPadding.setLabel( "Post-Padding (min.):", label2=self.detailData['postpadding'] )
                self.postPadding.setVisible(True)
                if self.detailData['priority'] != 0:
                    self.priority.setLabel( "Priority:", label2=str(self.detailData['priority']) )
                self.priority.setVisible(True)
                self.scheduleType.setLabel( "Schedule Type:", label2=self.detailData['rectype'] )
                self.scheduleType.setVisible(True)
                #self.timeSlot.setLabel( "Timeslot:", label2=str(self.detailData['recdate']) )
                self.timeSlot.setVisible(False)
                self.keepRecs.setLabel( "Recordings to Keep:", label2=str(self.detailData['maxrecs']) )
                self.keepRecs.setVisible(True)
                self.recDirId.setLabel( "Directory:", label2=str(self.detailData['directory']) )
                self.recDirId.setVisible(True)

                self.placeFiller.setVisible(True)
                self.saveButton.setVisible(True)

            else:
                #self.placeFiller.setVisible(True)
                self.quickrecordButton.setVisible(False)

                if self.oid_type !="E" and self.detailData['resume'] > 0:
                    if (self.detailData['duration'] - self.detailData['resume']) < 10:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(True)
                    else:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(True)
                else:
                    self.unwatchButton.setVisible(False)
                    self.resumeButton.setVisible(False)

            self.recordButton.setVisible(False)
            if self.settings.XNEWA_READONLY == False:
                #self.gzButton.setVisible(True)
                pass

            self.closeButton.setVisible(True)
            xbmcgui.WindowXML.setFocus(self, self.closeButton)

        elif (self.detailData['rectype'] == 'Record Once' or self.detailData['rectype'] == 'Single' or self.detailData['rectype'] == 'Multiple')  and self.detailData['status'] != "Completed" and self.detailData['status'] != "In-Progress" and self.detailData['status'] != "Failed"and self.detailData['status'] != "Conflict":
            self.win.setProperty('heading', 'Recording Properties')

            self.subtitleLabel.setVisible(True)
            if self.detailData['season'] == 0:
                self.subtitleLabel.setLabel(self.detailData['subtitle'])
            else:
                self.subtitleLabel.setLabel('({0}x{1}) {2} {3}'.format(self.detailData['season'],self.detailData['episode'],self.detailData['subtitle'],self.detailData['significance']))
            #self.subtitleLabel.setLabel(self.detailData['subtitle'])
            self.timeStartLabel.setLabel(self.xnewa.formatTime(self.detailData['start']))
            self.timeEndLabel.setLabel(self.xnewa.formatTime(self.detailData['end']))
            self.dateLabel.setLabel(self.xnewa.formatDate(self.detailData['start']))
            self.dateLongLabel.setLabel(self.xnewa.formatDate(self.detailData['start'], withyear=True))
            self.durationLabel.setLabel(str(int((self.detailData['end'] - self.detailData['start']).seconds / 60)))
            self.descLabel.setVisible(True)
            self.descLabel.setText(self.detailData['desc'])

            if self.oid_type!="R"  and self.oid_type !="E":
                self.showSeperator.setVisible(True)
                if (self.detailData['status'] == "Pending"):
                    if self.detailData['status'] == "In-Progress":
                        self.extendTime.setLabel( "Extend End-Time:", label2='Unknown' )
                        self.extendTime.setVisible(True)
                    else:
                        self.extendTime.setVisible(False)
                        self.scheduleType.setLabel( "Schedule Type:", label2=self.detailData['rectype'] )
                        self.scheduleType.setVisible(True)
                        self.prePadding.setLabel( "Pre-Padding (min.):", label2=self.detailData['prepadding'] )
                        self.prePadding.setVisible(True)
                        self.postPadding.setLabel( "Post-Padding (min.):", label2=self.detailData['postpadding'] )
                        self.postPadding.setVisible(True)
                        self.recDirId.setLabel( "Directory:", label2=str(self.detailData['directory']) )
                        self.recDirId.setVisible(True)
                        self.qualityControl.setLabel( "Quality:", label2=self.detailData['recquality'] )
                        self.qualityControl.setVisible(True)
                        self.saveButton.setVisible(True)
                else:
                    self.extendTime.setVisible(False)
                    self.qualityControl.setVisible(False)
                    self.prePadding.setVisible(False)
                    self.postPadding.setVisible(False)
                    self.saveButton.setVisible(False)
                    self.scheduleType.setVisible(False)

                self.timeSlot.setVisible(False)
                self.keepRecs.setVisible(False)
            else:
                #self.placeFiller.setVisible(True)

                self.archiveButton.setVisible(False)
                self.quickrecordButton.setVisible(False)

                if self.oid_type !="E" and self.detailData['resume'] > 0:
                    if (self.detailData['duration'] - self.detailData['resume']) < 60:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(True)
                    else:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(True)
                else:
                    self.unwatchButton.setVisible(False)
                    self.resumeButton.setVisible(False)

            self.recordButton.setVisible(False)
            if self.settings.XNEWA_READONLY == True:
                self.deleteButton.setVisible(False)

            self.closeButton.setVisible(True)

            if self.detailData['recording_oid'] > 0:
                xbmcgui.WindowXML.setFocus(self, self.closeButton)
            else:
                xbmcgui.WindowXML.setFocus(self, self.scheduleType)
        else:
            self.win.setProperty('heading', 'Program Details')
            if self.settings.XNEWA_EPISODE == True and self.detailData.has_key('filename') == True:
                if os.path.isdir(os.path.dirname(self.detailData['filename'])):
                    self.update = False;
                    myFilename = self.detailData['filename']
                    if myFilename[0:2]=='\\\\':
                        myFilename = 'smb:'+self.detailData['filename'].replace('\\','/')

                    myJSON = XBMCJSON()
                    param = {}
                    param['filter'] = {"field": "filename", "operator": "is", "value": os.path.basename(myFilename)}
                    print param['filter']
                    if self.detailData['movie'] == True:
                        param['properties'] = ["setid", "title", "file", "lastplayed", "resume",]
                        response =  myJSON.VideoLibrary.GetMovies(param)
                    else:
                        param['properties'] = ["tvshowid", "showtitle", "file", "lastplayed", "resume",]
                        response =  myJSON.VideoLibrary.GetEpisodes(param)
                    print response
                    try:
                        print response['result']
                        if response['result']['limits']['total'] == 1:
                            if self.detailData['movie'] == True:
                                self.xbmcId =  response['result']['movies'][0]['movieid']
                                print response['result']['movies'][0]['resume']
                                self.xbmcResume = response['result']['movies'][0]['resume']['position']
                            else:
                                print response['result']['episodes'][0]['tvshowid']
                                self.xbmcId =  response['result']['episodes'][0]['tvshowid']
                                print response['result']['episodes'][0]['resume']
                                self.xbmcResume = response['result']['episodes'][0]['resume']['position']
                                if self.detailData['filename'] != response['result']['episodes'][0]['file']:
                                    self.detailData['filename'] = response['result']['episodes'][0]['file']
                                    print "Playing Library File " + self.detailData['filename']
                        else:
                            param = {}
                            if os.name != 'nt' or myFilename[0:3] == 'smb':
                                param['directory']=os.path.dirname(myFilename)+'/'
                            else:
                                param['directory']=os.path.dirname(myFilename)+'\\'
                            response = myJSON.VideoLibrary.Scan(param)
                            print response
                            try:
                                print response['result']
                                sleep(2)
                                param = {}
                                param['filter'] = {"field": "filename", "operator": "is", "value": os.path.basename(myFilename)}
                                if self.detailData['movie'] == True:
                                    param['properties'] = ["setid", "title", "file"]
                                    response =  myJSON.VideoLibrary.GetMovies(param)
                                else:
                                    param['properties'] = ["tvshowid", "showtitle", "file"]
                                    response =  myJSON.VideoLibrary.GetEpisodes(param)

                                print response
                                try:
                                    if response['result']['limits']['total'] == 1:
                                        if self.detailData['movie'] == True:
                                            self.xbmcId =  response['result']['movies'][0]['movieid']
                                            self.xbmcResume = response['result']['movies'][0]['resume']['position']
                                        else:
                                            print response['result']['episodes'][0]['tvshowid']
                                            self.xbmcId =  response['result']['episodes'][0]['tvshowid']
                                            self.xbmcResume = response['result']['episodes'][0]['resume']['position']
                                except:
                                    print response['result']
                            except:
                                print response['error']
                    except:
                        print response['error']
            self.subtitleLabel.setVisible(True)
            if self.detailData['season'] == 0:
                self.subtitleLabel.setLabel(self.detailData['subtitle'])
            else:
                self.subtitleLabel.setLabel('({0}x{1}) {2} {3}'.format(self.detailData['season'],self.detailData['episode'],self.detailData['subtitle'],self.detailData['significance']))
            self.timeStartLabel.setLabel(self.xnewa.formatTime(self.detailData['start']))
            self.timeEndLabel.setLabel(self.xnewa.formatTime(self.detailData['end']))
            self.dateLabel.setLabel(self.xnewa.formatDate(self.detailData['start']))
            self.dateLongLabel.setLabel(self.xnewa.formatDate(self.detailData['start'], withyear=True))
            self.durationLabel.setLabel(str(int((self.detailData['end'] - self.detailData['start']).seconds / 60)))
            self.descLabel.setVisible(True)
            self.descLabel.setText(self.detailData['desc'])
            if self.detailData['status'] == "Failed":
                self.win.setProperty('recordingfailed', 'true')
            else:
                self.win.setProperty('recordingfailed', '')

            if self.oid_type!="R"  and self.oid_type !="E":
                x, y = self.showSeperator.getPosition()
                self.showSeperator.setPosition(x, y+220)
                self.showSeperator.setVisible(True)

                self.qualityControl.setVisible(False)
                self.prePadding.setVisible(False)
                self.postPadding.setVisible(False)
                self.extendTime.setVisible(False)
                self.scheduleType.setVisible(False)
                self.timeSlot.setVisible(False)
                self.keepRecs.setVisible(False)
                self.recDirId.setVisible(False)
                self.placeFiller.setVisible(True)
            else:
                print 'NextPVR Resume is ' + `self.detailData['resume']` + ' Library ' + `self.xbmcResume`
                if self.xbmcResume > self.detailData['resume']:
                    self.detailData['resume'] = self.xbmcResume
                if self.oid_type !="E" and self.detailData['resume'] > 0:
                    if (self.detailData['duration'] - self.detailData['resume']) < 60:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(True)
                    else:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(True)
                else:
                    self.unwatchButton.setVisible(False)
                    self.resumeButton.setVisible(False)

            if self.detailData['status'] != "Completed" and self.detailData['status'] != "In-Progress"  and self.detailData['status'] != "Failed":
                print datetime.now(),self.detailData['end']
                if datetime.now() < self.detailData['end'] and self.settings.XNEWA_READONLY == False:
                    self.recordButton.setVisible(True)
                    self.quickrecordButton.setVisible(True)
                else:
                    self.recordButton.setVisible(False)
                    self.quickrecordButton.setVisible(False)
                if self.detailData['status'] != "Conflict":
                    self.deleteButton.setVisible(False)
                else:
                    self.deleteButton.setLabel('Delete Conflict')
                    if self.oid_type=="R":
                        self.archiveButton.setVisible(False)
            else:
                if self.detailData['status'] == "Completed":
                    self.deleteButton.setLabel('Delete')
                elif self.detailData['status'] == "Failed":
                    self.deleteButton.setLabel('Delete')
                    self.archiveButton.setVisible(False)
                elif self.detailData['status'] == "In-Progress":
                    self.archiveButton.setVisible(False)
                if self.settings.XNEWA_READONLY == True:
                    self.deleteButton.setVisible(False)
                self.recordButton.setVisible(False)
                self.quickrecordButton.setVisible(False)

            if self.oid_type!="R"  and self.oid_type !="E":
                self.saveButton.setVisible(False)
            self.closeButton.setVisible(True)

            xbmcgui.WindowXML.setFocus(self, self.closeButton)
        self.win.setProperty('busy', 'false')

    def _pickFromList(self, title, choices, current):
        selected = xbmcgui.Dialog().select(title, choices)
        if selected >= 0:
            return choices[selected]
        else:
            return current;

    def _getNumber(self, heading, current, min=None, max=None):
        value = xbmcgui.Dialog().numeric(0, heading, str(current))
        if value == str(current):
            return current

        result = int(value)

        if min is not None and result < min:
            xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), '%d %d and %d' % (smartUTF8(__language__(30118)), min, max))
            result = current

        if max is not None and result > max:
            xbmcgui.Dialog().ok(smartUTF8(__language__(30108)), '%d %d and %d' % (smartUTF8(__language__(30118)), min, max))
            result = current

        return result

#player = XBMCPlayer(xbmc.PLAYER_CORE_DVDPLAYER)
#        player.play( url, item )
#        ...
#        while player.is_active:
#            player.sleep(100)
#            ...

class XBMCPlayer(xbmc.Player):
    def __init__( self, *args, **kwargs ):
        xbmc.Player.__init__(self, *args, **kwargs)
        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']

        self.is_started = False
        self.is_active = True
        self.isTimeShifted = False
        print "#XBMCPlayer#"
        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']
        self.heartbeat = datetime.now() + timedelta(seconds=10)


    def onPlayBackPaused( self ):
        xbmc.log("#Im paused#")

    def onPlayBackResumed( self ):
        xbmc.log("#Im Resumed #")

    def onPlayBackStarted( self ):
        print "#Playback Started#"
        try:
            print "#Im playing :: " + self.getPlayingFile()
        except:
            print "#I failed get to what Im playing#"
        self.is_started = True
        print self.getTotalTime()

    def onPlayBackEnded( self ):
        self.is_active = False
        print "#Playback Ended#"

    def onPlayBackStopped( self ):
        self.is_active = False
        print "## Playback Stopped ##"

    def sleep(self, s):
        xbmc.sleep(s)

    def setTimeShift( self, isTimeShifted ):
        xbmc.log("# TimeShift #")
        self.isTimeShifted = isTimeShifted

    def sendHeartbeat(self):
        if self.isTimeShifted and datetime.now() > self.heartbeat:
            print "## Heartbeat"
            if self.settings.NextPVR_STREAM == 'Transcode':
                self.heartbeat = datetime.now() + timedelta(seconds=3)
                self.xnewa.sendTranscodeHeartbeat()
            else:
                self.xnewa.sendVlcHeartbeat(self.settings.NextPVR_USER, self.settings.NextPVR_PW)
                self.heartbeat = datetime.now() + timedelta(seconds=10)
            print self.heartbeat
