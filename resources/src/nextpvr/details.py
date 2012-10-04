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

from XNEWAGlobals import *
from fanart import fanart
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
        self.fanart = fanart()
        
        self.win = None        
        self.shouldRefresh = False
        print repr(self)
        
    def onInit(self):
        self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        print self.oid_type
        if self.oid_type !="R" and self.oid_type !="E":
            self.genre1Image = self.getControl(306)
            self.genre2Image = self.getControl(307)
            self.genre3Image = self.getControl(308)
            self.statusLabel = self.getControl(309)
        else:
            self.genre1Image = None
            self.genre2Image = None
            self.genre3Image = None
            self.statusLabel = None       

        
        self.showImage = self.getControl(302)
        self.title = self.getControl(303)
        self.channel = self.getControl(304)
        self.channelImage = self.getControl(305)            

        self.subtitleLabel = self.getControl(310)
        self.timeLabel = self.getControl(311)
        self.descLabel = self.getControl(312)
        
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
            self.priority.setVisible(False)
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
            self.saveButton = self.getControl(250)
            self.resumeButton = None
            if self.oid_type !="F":
                self.recordButton = self.getControl(252)
                self.quickrecordButton = None
            else:
                self.recordButton = self.getControl(252)
                self.quickrecordButton = None
        else:
            self.saveButton = None
            self.recordButton =  self.getControl(260)
            self.scheduleType = None
            self.resumeButton = self.getControl(258)
            self.unwatchButton = self.getControl(259)
            self.archiveButton = self.getControl(257)
            self.archiveButton.setVisible(False)
            if self.oid_type == "E":
                self.recordButton = self.getControl(260)
                self.quickrecordButton = self.getControl(252)
            else:
                self.quickrecordButton = self.getControl(252)
        
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
        
    def onAction(self, action):
        if action.getId() in (EXIT_SCRIPT):
            self.close() 

    def goRecord(self):
        if self.oid_type =="E":        
            self.returnvalue = "PICK"
            self.close("PICK")
        else:
            self.detailData['status'] = "Pending"
            self.detailData['recquality'] = "High"
            self.detailData['prepadding'] = "2"
            self.detailData['postpadding'] = "1"
            self.detailData['rectype'] = "Record Once"
            self.detailData['maxrecs'] = "0"
            self.detailData['recording_oid'] = 0
            self.detailData['directory'] = "Default"
            self._updateView()

    def error_message(self):
        dialog = xbmcgui.Dialog()
        dialog.ok("Sorry", "An error occurred!")

    def onClick(self, controlId):
        source = self.getControl(controlId)
        if self.closeButton == source:
            self.close()
        elif self.recordButton == source:
            self.goRecord()
            self.close()
        elif self.saveButton == source or self.quickrecordButton == source:
            if self.quickrecordButton == source:
                self.detailData['status'] = "Pending"
                self.detailData['recquality'] = "High"
                self.detailData['prepadding'] = "2"
                self.detailData['postpadding'] = "1"
                self.detailData['rectype'] = "Record Once"
                self.detailData['maxrecs'] = "0"
                self.detailData['recording_oid'] = 0
                self.detailData['directory'] = "Default"

            if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                try:
                    if self.detailData['recording_oid'] == 0:
                        if self.xnewa.scheduleRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData):
                            self.returnvalue = "REC"
                            self.close("REC")
                        else:
                            self.error_message()
                    else:
                        if self.xnewa.updateRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData):
                            self.returnvalue = "REC"
                            self.close("REC")
                        else:
                            self.error_message()
                            
                except:
                    xbmcgui.Dialog().ok('Sorry', 'An error occurred!')
        elif self.deleteButton == source:
            if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                    try:
                            if self.xnewa.cancelRecording(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData):
                                    self.returnvalue = "DEL"
                                    self.close("DEL")
                            else:
                                    self.error_message()
                    except:
                            xbmcgui.Dialog().ok('Sorry', 'An error occurred!')
            else:
                    xbmcgui.Dialog().ok('Sorry', 'Something went wrong!!')
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
            self.detailData['recquality'] = self._pickFromList("Select recording quality", ["Best", "Better", "Best", "Default"], self.detailData['recquality'])
            self._updateView()
        elif self.prePadding == source:
            self.detailData['prepadding'] = str(self._getNumber("Select prepadding minutes", self.detailData['prepadding'], 0, 30))
            self._updateView()
        elif self.postPadding == source:
            self.detailData['postpadding'] = str(self._getNumber("Select postpadding minutes", self.detailData['postpadding'], 0, 30))
            self._updateView()
        elif self.extendTime == source:
            self.detailData['extendend'] = str(self._getNumber("Select time extenstion (minutes)", 0, 0, 30))
            self._updateView()
        elif self.keepRecs == source:
            self.detailData['maxrecs'] = str(self._getNumber("Select recordings to keep (0 means all)", self.detailData['maxrecs'], 0, 30))
            self._updateView()
        elif self.recDirId == source:
            self.detailData['directory'] = self._pickFromList("Recording Directory", self.xnewa.RecDirs, self.detailData['directory'])
            self._updateView()
        elif self.playButton == source or self.resumeButton == source:
            from threading import Thread
            t = Thread(target=self._myPlayer, args=(None,source,))
            t.start()
    
    def _myPlayer(self, detail=None, button=None):
        import xbmcgui,xbmc
        if detail is not None:
            self.detailData = detail

        self.urly = self.xnewa.getURL()
        isVlc = False
        if self.detailData.has_key('filename') == False:
            self.channelIcon = self.fanart.getChannelIcon(self.detailData['channel'][0])
            if self.channelIcon is not None:
                listitem = xbmcgui.ListItem(self.detailData["title"],  thumbnailImage=self.channelIcon)
                infolabels={ "Title": self.detailData['title']  }
                listitem.setInfo( type="Video", infoLabels=infolabels )
            else:
                listitem = xbmcgui.ListItem(self.detailData['title'])
            
            url = self.urly + "/live?channel=" + self.detailData['channel'][1]
            if self.settings.NextPVR_STREAM == 'VLC':
                # vlc streaming test
                print self.detailData['program_oid']
                if self.xnewa.startVlcObjectByEPGEventOID(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData['program_oid']):
                    url = self.xnewa.getVlcURL()
                    isVlc = True
                
        else:
            self.showIcon = self.fanart.getCachedIcon(self.detailData['title'])
            if self.showIcon is not None:
                listitem = xbmcgui.ListItem(self.detailData['title'],  thumbnailImage=self.showIcon)
            else:
                listitem = xbmcgui.ListItem(self.detailData['title'],"")
            
            infolabels={ "Title": self.detailData['title'] , 'plot': self.detailData['desc'] }
            listitem.setInfo( type="Video", infoLabels=infolabels )
            if self.resumeButton == button:
                bookmarkSecs = self.detailData['resume']
                #import datetime
                #formatSeconds = str(datetime.timedelta(seconds=bookmarkSecs))
                #question = 'Resume from %s?' % formatSeconds
                #resume = xbmcgui.Dialog().yesno(self.detailData['title'],'', question,'','Resume','Beginning')
                #print resume
                #if resume== 0:
                listitem.setProperty('startoffset',str(bookmarkSecs))
            if os.name != 'nt':
                url = self.detailData['filename'].replace("\\","/")
            else:
                url = self.detailData['filename']

            import xbmcvfs
            print url
            if xbmcvfs.exists(url) == False:
                if self.xnewa.offline == True:
                    xbmcgui.Dialog().ok('Offline', 'Cannot play this file offline')
                    return
                if self.settings.NextPVR_STREAM == 'Native':
                    from uuid import getnode as get_mac
                    mac = get_mac()
                    url = self.urly + "/live?recording=" +str(self.detailData['recording_oid'])+"&client=XNEWA"+hex(mac)
                    #print self.xnewa.urlHEAD(url)
                elif self.settings.NextPVR_STREAM == 'Direct':
                    import urllib
                    #url = your url here
                    f1 = urllib.quote(url)
                elif self.settings.NextPVR_STREAM == 'VLC':
                    # vlc streaming test
                    if self.xnewa.startVlcObjectByScheduleOID(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData['recording_oid']):
                        url = self.xnewa.getVlcURL()
                        isVlc = True

        print "Playing " + url
        

        self.close();
        player = XBMCPlayer(xbmc.PLAYER_CORE_AUTO)
        if player.isPlaying():
            player.stop()
        player.play( url, listitem )
#        ...        
        self._lastPos = 0
        self._duration = 0
        while player.is_active:
            if player.is_started:
                try:
                    self._lastPos = player.getTime()
                    self._duration = player.getTotalTime()
                except:
                    print "could net get last"

            player.sleep(100)


        if self.detailData.has_key('filename') == True:
            if self.xnewa.offline == False:
                if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                    retval = self.xnewa.setPlaybackPositiontObject(self.settings.NextPVR_USER, self.settings.NextPVR_PW, self.detailData, self._lastPos, self._duration )
            else:
                #todo cache playback
                pass
        if isVlc == True:
            if self.xnewa.stopVlcStreamObject(self.settings.NextPVR_USER, self.settings.NextPVR_PW):
                print "vlc stopped"

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
                    if t ['recording_oid'] == self.oid:
                        self.detailData = t
                        break

        else:
            self.win.setProperty('busy', 'false')
            xbmcgui.Dialog().ok('Sorry', 'Unable to contact NextPVR server!!')
            self.close()
        self.win.setProperty('busy', 'false')

    def _updateView(self):  
        
        self.win.setProperty('busy', 'true')
        self.title.setLabel(self.detailData['title'])        
        self.channel.setLabel(self.detailData['channel'][0])

        #self.win.setProperty('title', self.detailData['title'])
        #self.win.setProperty('channel', self.detailData['channel'][0])        
        #if self.heading is not None:
        #    self.channel.setLabel(self.detailData['channel'][0])

        if self.oid_type!="R" and self.oid_type !="E":        
            self.win.setProperty('genre', str(self.detailData['genres']))
        
        
        self.channelIcon = self.fanart.getChannelIcon(self.detailData['channel'][0])
        if self.channelIcon is not None:
            self.channelImage.setImage(self.channelIcon)
        
        if self.epg == True:
            from datetime import datetime
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


        self.fanart = fanart()

        self.showIcon = self.fanart.getCachedIcon(self.detailData['title'])
        if self.showIcon is not None:
            self.showImage.setImage(self.showIcon)
            
        if self.oid_type=="NOT USED":
            if len(self.detailData['genres']) > 0:
                self.genreIcon = self.fanart.getGenreIcon(self.detailData['genres'][0])
                if self.genreIcon is not None:
                    self.genre1Image.setImage(self.genreIcon)
            
            if len(self.detailData['genres']) > 1:
                self.genreIcon = self.fanart.getGenreIcon(self.detailData['genres'][1])
                if self.genreIcon is not None:
                    self.genre2Image.setImage(self.genreIcon)
            
            if len(self.detailData['genres']) > 2:
                self.genreIcon = self.fanart.getGenreIcon(self.detailData['genres'][2])
                if self.genreIcon is not None:
                    self.genre3Image.setImage(self.genreIcon)
            
        if self.statusLabel is not None:
            self.statusLabel.setVisible(True)
            self.statusLabel.setLabel(self.detailData['status'])
        
        print self.detailData['status']
        print self.detailData['rectype']
        
        if self.detailData['rectype'] !="" and self.detailData['rectype'] != 'Record Once' and self.detailData['rectype'] != "Single"  and self.detailData['status'] != "Completed" and self.detailData['status'] != "In-Progress":
            self.win.setProperty('heading', 'Recurring Recording Properties')
            self.subtitleLabel.setVisible(True)
            self.subtitleLabel.setLabel(self.detailData['subtitle'])
            self.timeLabel.setVisible(True)
            ctmp = self.detailData['start'].strftime('%a, %b %d %H:%M') + " - " + self.detailData['end'].strftime('%H:%M')
            ctmp = ctmp + " (" + str(int((self.detailData['end'] - self.detailData['start']).seconds / 60)) + " min.)"
            self.timeLabel.setLabel(ctmp)
            self.descLabel.setHeight(220)
            self.descLabel.setVisible(True)
            self.descLabel.setText(self.detailData['desc'])

            if self.oid_type!="R"  and self.oid_type !="E":
                self.subtitleLabel.setVisible(False)
                self.timeLabel.setVisible(False)
                self.descLabel.setVisible(False)

                self.showSeperator.setVisible(False)
                self.extendTime.setVisible(False)
            
                self.qualityControl.setLabel( "Quality:", label2=self.detailData['recquality'] )
                self.qualityControl.setVisible(True)
                self.prePadding.setLabel( "Pre-Padding (min.):", label2=self.detailData['prepadding'] )
                self.prePadding.setVisible(True)
                self.postPadding.setLabel( "Post-Padding (min.):", label2=self.detailData['postpadding'] )
                self.postPadding.setVisible(True)
                self.scheduleType.setLabel( "Schedule Type:", label2=self.detailData['rectype'] )
                self.scheduleType.setVisible(True)
                #self.timeSlot.setLabel( "Timeslot:", label2=str(self.detailData['recdate']) )
                self.timeSlot.setVisible(False)
                self.keepRecs.setLabel( "Recordings to Keep:", label2=str(self.detailData['maxrecs']) )
                self.keepRecs.setVisible(True)
                self.recDirId.setLabel( "Directory:", label2=str(self.detailData['directory']) )
                self.recDirId.setVisible(True)
                
                self.placeFiller.setVisible(False)
                self.saveButton.setVisible(True)

            else:                
                #self.placeFiller.setVisible(True)
                self.quickrecordButton.setVisible(False)
            
                print self.detailData['resume']
                if self.oid_type !="E" and self.detailData['resume'] > 0:
                    if (self.detailData['duration'] - self.detailData['resume']) < 10:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(True)
                    else:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(Truee)
                else:
                    self.unwatchButton.setVisible(False)
                    self.resumeButton.setVisible(False)
            
            self.recordButton.setVisible(False)
            self.deleteButton.setVisible(True)

            self.closeButton.setVisible(True)      
            xbmcgui.WindowXML.setFocus(self, self.closeButton)
        
        elif (self.detailData['rectype'] == 'Record Once' or self.detailData['rectype'] == 'Single')  and self.detailData['status'] != "Completed" and self.detailData['status'] != "In-Progress" and self.detailData['status'] != "Failed":
            self.win.setProperty('heading', 'Recording Properties')
            
            self.subtitleLabel.setVisible(True)
            self.subtitleLabel.setLabel(self.detailData['subtitle'])
            self.timeLabel.setVisible(True)
            ctmp = self.detailData['start'].strftime('%a, %b %d %H:%M') + " - " + self.detailData['end'].strftime('%H:%M')
            ctmp = ctmp + " (" + str(int((self.detailData['end'] - self.detailData['start']).seconds / 60)) + " min.)"
            self.timeLabel.setLabel(ctmp)
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
                self.quickrecordButton.setVisible(False)
            
                print self.detailData['resume']
                if self.oid_type !="E" and self.detailData['resume'] > 0:
                    if (self.detailData['duration'] - self.detailData['resume']) < 60:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(Truee)
                    else:
                        self.unwatchButton.setVisible(False)
                        self.resumeButton.setVisible(True)
                else:
                    self.unwatchButton.setVisible(False)
                    self.resumeButton.setVisible(False)

            self.recordButton.setVisible(False)
            self.deleteButton.setVisible(True)
            
            self.closeButton.setVisible(True)

            if self.detailData['recording_oid'] > 0:
                xbmcgui.WindowXML.setFocus(self, self.closeButton)
            else:
                xbmcgui.WindowXML.setFocus(self, self.scheduleType)
        else:
            self.win.setProperty('heading', 'Program Details')
            self.subtitleLabel.setVisible(True)
            self.subtitleLabel.setLabel(self.detailData['subtitle'])
            self.timeLabel.setVisible(True)
            ctmp = self.detailData['start'].strftime('%a, %b %d %H:%M') + " - " + self.detailData['end'].strftime('%H:%M')
            ctmp = ctmp + " (" + str(int((self.detailData['end'] - self.detailData['start']).seconds / 60)) + " min.)"
            self.timeLabel.setLabel(ctmp)
            self.descLabel.setHeight(220)
            self.descLabel.setVisible(True)
            detText = self.detailData['desc']  
            if self.detailData['status'] == "Failed":
                detText = detText + '[CR][COLOR red]Failed[/COLOR]'


            self.descLabel.setText(detText)

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
                print self.detailData['resume']
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
                self.recordButton.setVisible(True)
                self.quickrecordButton.setVisible(True)
                self.deleteButton.setVisible(False)
            else:
                if self.detailData['status'] == "Completed" or self.detailData['status'] == "Failed":
                    self.deleteButton.setLabel('Delete')
                self.deleteButton.setVisible(True)
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
            xbmcgui.Dialog().ok('Error', 'Value must be between %d and %d' % (min, max))
            result = current
            
        if max is not None and result > max:
            xbmcgui.Dialog().ok('Error', 'Value must be between %d and %d' % (min, max))
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
        self.is_started = False
        self.is_active = True
        print "#XBMCPlayer#"
    
    def onPlayBackPaused( self ):
        xbmc.log("#Im paused#")
        
    def onPlayBackResumed( self ):
        xbmc.log("#Im Resumed #")
        
    def onPlayBackStarted( self ):
        print "#Playback Started#"
        try:
            print "#Im playing :: " + self.getPlayingFile()
        except:
            print "#I failed get what Im playing#"
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
