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

from XNEWAGlobals import *

# =============================================================================
class settingsDialog(xbmcgui.WindowXMLDialog):
    """
    Show details of show, recording and recurring recording
    """

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        # Get settings from arguments...
        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']
        self.win = None
        self.shouldRefresh = False
        self.update = False
        self.changeGroup = False

    def onInit(self):
        self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        self.saveButton = self.getControl(250)
        self.cancelButton = self.getControl(253)

        self.nextpvr_ip = self.getControl(201)
        self.nextpvr_port = self.getControl(202)
        self.nextpvr_user = self.getControl(203)
        self.nextpvr_pw = self.getControl(204)
        self.nextpvr_pin = self.getControl(205)

        self.xnewa_interface = self.getControl(220)
        self.xnewa_client_size = self.getControl(221)
        self.xnewa_client_quality = self.getControl(222)

        self.nextpvr_stream = self.getControl(215)
        self.xnewa_prebuffer = self.getControl(217)
        self.xnewa_postbuffer = self.getControl(218)
        self.xnewa_update_episodes = self.getControl(219)
        self.nextpvr_icon_dl = self.getControl(216)
        self.nextpvr_usewol  = self.getControl(305)
        self.nextpvr_mac = self.getControl(306)
        self.nextpvr_broadcast = self.getControl(307)

        self.epgscrollint = self.getControl(210)
        self.epgdispint = self.getControl(211)
        self.epgretrint = self.getControl(212)
        self.epgrowh = self.getControl(213)
        self.epgGroup = self.getControl(214)


        self.vlc_video_size = self.getControl(401)
        self.vlc_video_bitrate = self.getControl(402)
        self.vlc_audio_bitrate = self.getControl(403)

        self._updateView()


    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        if action.getId() in (EXIT_SCRIPT) or action.getButtonCode()  in (EXIT_SCRIPT):
            self.close()

    def onClick(self, controlId):
        source = self.getControl(controlId)

        if self.cancelButton == source:
            self.close()
        elif self.saveButton == source:
            self.settings.save()
            if self.changeGroup:
                self.xnewa.cleanCache('guideListing-*.p')
                import xbmcaddon
                addon = xbmcaddon.Addon()
                addon.setSetting("group",self.settings.EPG_GROUP)
            self.close()
        elif self.nextpvr_ip == source:
            self._getText(self.nextpvr_ip, "NextPVR_HOST")
        elif self.nextpvr_port == source:
           self._getText(self.nextpvr_port, "NextPVR_PORT")
        elif self.nextpvr_user == source:
            self._getText(self.nextpvr_user, "NextPVR_USER")
        elif self.nextpvr_pw == source:
            self._getText(self.nextpvr_pw, "NextPVR_PW")
        elif self.nextpvr_pin == source:
            self._getText(self.nextpvr_pin, "NextPVR_PIN")
        elif self.nextpvr_usewol == source:
            self._getYN(self.nextpvr_usewol, "NextPVR_USEWOL")
        elif self.nextpvr_mac == source:
            self._getText(self.nextpvr_mac, "NextPVR_MAC")
        elif self.nextpvr_broadcast == source:
            self._getText(self.nextpvr_broadcast, "NextPVR_BROADCAST")
        elif self.nextpvr_icon_dl == source:
            self._getYN(self.nextpvr_icon_dl, "NextPVR_ICON_DL")
        elif self.xnewa_update_episodes == source:
            self._getYN(self.xnewa_update_episodes, "XNEWA_EPISODE")
        elif self.nextpvr_stream == source:
            choices = ['Native', 'Timeshift', 'PVR', 'VLC',  'Direct' ]
            setting =  xbmcgui.Dialog().select("Streaming Option", choices)
            self.settings.set("NextPVR_STREAM", choices[setting])
            self.nextpvr_stream.setLabel(self.nextpvr_stream.getLabel(), label2=choices[setting])
        elif self.xnewa_prebuffer == source:
            self._getText(self.xnewa_prebuffer, "XNEWA_PREBUFFER")
        elif self.xnewa_postbuffer == source:
            self._getText(self.xnewa_postbuffer, "XNEWA_POSTBUFFER")
        elif self.xnewa_interface == source:
            choices = ['NextPVR', 'XML', 'JSON',  'Short' ]
            setting =  xbmcgui.Dialog().select("Interface Option", choices)
            self.settings.set("XNEWA_INTERFACE", choices[setting])
            self.xnewa_interface.setLabel(self.xnewa_interface.getLabel(), label2=choices[setting])
            self.changeGroup = True
        elif self.xnewa_client_size == source:
            choices = ['1920x1080','1600x900','1366x768','1280x720','1024x576', '960x540','854x480','720x480', '800x600']
            setting =  xbmcgui.Dialog().select("Size Option", choices)
            if setting > -1:
                self.settings.set("XNEWA_CLIENT_SIZE", choices[setting])
                self.xnewa_client_size.setLabel(self.xnewa_client_size.getLabel(), label2=choices[setting])
        elif self.xnewa_client_quality == source:
            choices = ['Normal','High']
            setting =  xbmcgui.Dialog().select("Quality Option", choices)
            if setting > -1:
                self.settings.set("XNEWA_CLIENT_QUALITY", choices[setting])
                self.xnewa_client_quality.setLabel(self.xnewa_client_quality.getLabel(), label2=choices[setting])

        elif self.vlc_video_size == source:
            choices = ['320', '480', '720' ]
            setting =  xbmcgui.Dialog().select("Video Size Option", choices)
            if setting > -1:
                self.settings.set("VLC_VIDEO_SIZE", choices[setting])
                self.vlc_video_size.setLabel(self.vlc_video_size.getLabel(), label2=choices[setting])
        elif self.vlc_video_bitrate == source:
            choices = ['128', '256', '512', 'LAN', 'HD-2K', 'HD-4K', 'HD-8K' ]
            setting =  xbmcgui.Dialog().select("Video Bitrate Option", choices)
            self.settings.set("VLC_VIDEO_BITRATE", choices[setting])
            self.vlc_video_bitrate.setLabel(self.vlc_video_bitrate.getLabel(), label2=choices[setting])
        elif self.vlc_audio_bitrate == source:
            choices = ['8', '16', '32', '64', '96', '128', '256' ]
            setting =  xbmcgui.Dialog().select("Audio Bitrate Option", choices)
            self.settings.set("VLC_AUDIO_BITRATE", choices[setting])
            self.vlc_audio_bitrate.setLabel(self.vlc_audio_bitrate.getLabel(), label2=choices[setting])

        elif self.epgscrollint == source:
            self._getText(self.epgscrollint, "EPG_SCROLL_INT")
        elif self.epgdispint == source:
            self._getText(self.epgdispint, "EPG_DISP_INT")
        elif self.epgretrint == source:
            self._getText(self.epgretrint, "EPG_RETR_INT")
        elif self.epgrowh == source:
            self._getText(self.epgrowh, "EPG_ROW_HEIGHT")
        elif self.epgGroup == source:
            choices = self.xnewa.channelGroups
            setting =  xbmcgui.Dialog().select("Channel Group", choices)
            if choices[setting] != self.settings.EPG_GROUP:
                self.settings.set("EPG_GROUP", choices[setting])
                self.epgGroup.setLabel(self.epgGroup.getLabel(), label2=choices[setting])
                self.changeGroup = True

    def _getText(self, ctrl, key):
        cTitle = ctrl.getLabel()
        cText = ctrl.getLabel2()
        kbd = xbmc.Keyboard(cText, cTitle)

        kbd.doModal()

        if kbd.isConfirmed():
            txt = kbd.getText()
            self.settings.set(key, txt)
            ctrl.setLabel(cTitle, label2=txt)

    def _getYN(self, ctrl, key):
        cTitle = ctrl.getLabel()
        theList = ["No", "Yes"]
        selected = xbmcgui.Dialog().select(cTitle, theList)
        if selected < 0:
                return
        self.settings.set(key, theList[selected])
        ctrl.setLabel(cTitle, label2=theList[selected])

    def _updateView(self):

        self.win.setProperty('busy', 'true')
        try:
            self.nextpvr_ip.setLabel( "NextPVR IP Address:", label2=self.settings.NextPVR_HOST )
            self.nextpvr_port.setLabel( "NextPVR Port Number:", label2=str(self.settings.NextPVR_PORT) )
            self.nextpvr_user.setLabel( "NextPVR Userid:", label2=self.settings.NextPVR_USER )
            self.nextpvr_pw.setLabel( "NextPVR Password:", label2=self.settings.NextPVR_PW )
            self.nextpvr_pin.setLabel( "NextPVR PIN:", label2=self.settings.NextPVR_PIN )
            if self.settings.NextPVR_USEWOL == True:
                self.nextpvr_usewol.setLabel( "Use Wake-On-Lan:", label2='Yes' )
            else:
                self.nextpvr_usewol.setLabel( "Use Wake-On-Lan:", label2='No' )
            self.nextpvr_mac.setLabel( "NextPVR MAC Address:", label2=self.settings.NextPVR_MAC )
            self.nextpvr_broadcast.setLabel( "Wake-On-Lan Broadcast Address:", label2=self.settings.NextPVR_BROADCAST )
            if self.settings.XNEWA_EPISODE == True:
                self.xnewa_update_episodes.setLabel( "Update Kodi Episode:", label2='Yes' )
            else:
                self.xnewa_update_episodes.setLabel( "Update Kodi Episode:", label2='No' )
            if self.settings.NextPVR_ICON_DL == True:
                self.nextpvr_icon_dl.setLabel( "Fetch Covers:", label2='Yes' )
            else:
                self.nextpvr_icon_dl.setLabel( "Fetch Covers:", label2='No' )
            self.nextpvr_stream.setLabel( "Streaming Format:", label2=self.settings.NextPVR_STREAM )
            self.xnewa_prebuffer.setLabel( "Timeshift Pre-buffer:", label2=str(self.settings.XNEWA_PREBUFFER*4) )
            self.xnewa_postbuffer.setLabel( "Timeshift Post-buffer:", label2=str(self.settings.XNEWA_POSTBUFFER*4) )
            self.xnewa_interface.setLabel( "Interface", label2=str(self.settings.XNEWA_INTERFACE) )
            self.xnewa_client_size.setLabel( "Web Client Size:", label2=str(self.settings.XNEWA_CLIENT_SIZE) )

            if self.settings.XNEWA_CLIENT_QUALITY == True:
                self.xnewa_client_quality.setLabel( "Web Client Quality:", label2='High' )
            else:
                self.xnewa_client_quality.setLabel( "Web Client Quality:", label2='Normal')

            self.epgscrollint.setLabel( "Scroll Interval (min.):", label2=str(self.settings.EPG_SCROLL_INT) )
            self.epgdispint.setLabel( "Display Interval (min.):", label2=str(self.settings.EPG_DISP_INT) )
            self.epgretrint.setLabel( "Retrieve Interval (hrs.):", label2=str(self.settings.EPG_RETR_INT) )
            self.epgrowh.setLabel( "Row Height (px):", label2=str(self.settings.EPG_ROW_HEIGHT) )
            self.epgGroup.setLabel( "Channel Group", label2=str(self.settings.EPG_GROUP) )

            self.vlc_video_size.setLabel( "VLC Video Size;", label2=str(self.settings.VLC_VIDEO_SIZE) )
            self.vlc_video_bitrate.setLabel( "VLC Video Bitrate;", label2=str(self.settings.VLC_VIDEO_BITRATE) )
            self.vlc_audio_bitrate.setLabel( "VLC Audio Bitrate;", label2=str(self.settings.VLC_AUDIO_BITRATE) )
        except:
            handleException()
        try:
            xbmcgui.WindowXML.setFocus(self, self.nextpvr_ip)
        except:
            handleException()

        self.win.setProperty('busy', 'false')

    def _chooseFromList(self, translations, title, property, setter):
        """                                 user with a dialog box to select a value from a list.
        Once selected, the setter method on the Schedule is called to reflect the selection.

        """
        pickList = self.translator.toList(translations)
        selected = xbmcgui.Dialog().select(title, pickList)
        if selected >= 0:
            self.setWindowProperty(property, pickList[selected])
            setter(list(translations.keys())[selected])

    def _enterNumber(self, heading, current, min=None, max=None):
        """
        Prompt user to enter a valid number with optional min/max bounds.

        """
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
