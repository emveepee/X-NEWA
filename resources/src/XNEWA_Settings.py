from __future__ import division
######################################################################################################
# Class for storing specific settings
#
# Usage: Instantiate a new class and use properties to retrieve global settings...
#          I.e. mysettings= xnewa_settings()
#        Then, use properties
#          I.e. print (mysettings.NextPVR_HOST)
#               print (mysettings.NextPVR_PORT)
######################################################################################################

from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import hex
from builtins import object
import os
from XNEWAGlobals import *
import traceback
import sys
import xbmcaddon
import xbmcvfs
import xbmc
# Core defines

class XNEWA_Settings(object):

    # Instantiation
    def __init__(self):

        xbmc.log("Reading Settings.xml")
        if  int(xbmc.getInfoLabel('System.BuildVersion')[:2]) < 18:
            XBMC_DIALOG_BUSY_OPEN = "ActivateWindow(busydialog)"
            XBMC_DIALOG_BUSY_CLOSE = "Dialog.Close(busydialog)"

        from uuid import getnode as get_mac

        if hasattr(os, 'uname'):
            system = os.uname()[4]
        else:
            import platform
            system = platform.uname()[5]
        if system == 'armv6l':
            try:
                mac = open('/sys/class/net/eth0/address').readline()
                self.XNEWA_MAC = hex(int('0x'+ mac.replace(':',''),16))
            except:
                self.XNEWA_MAC = str(hex(get_mac()))
        else:
            self.XNEWA_MAC = str(hex(get_mac()))

        self.loadFromSettingsXML()
        return

    def usewol(self):
          return self.NextPVR_USEWOL


    def loadFromSettingsXML(self):
        addon = xbmcaddon.Addon()
        self.NextPVR_HOST = addon.getSetting("host")
        self.NextPVR_PORT = int(addon.getSetting("port"))
        self.NextPVR_USER = addon.getSetting("userid")
        self.NextPVR_PW = addon.getSetting("password")
        self.NextPVR_PIN = addon.getSetting("pin")
        self.NextPVR_USEWOL = addon.getSetting("usewol") == 'true'
        self.LOCAL_NEWA = True
        self.NextPVR_MAC = addon.getSetting("mac")
        self.NextPVR_BROADCAST = addon.getSetting("broadcast")
        self.NextPVR_CONTACTS = addon.getSetting("wol_attempts")
        self.XNEWA_EPISODE = addon.getSetting("syncXBMC") == 'true'
        self.NextPVR_ICON_DL = addon.getSetting("fetchFanart") == 'true'
        self.XNEWA_CACHE_PERM = addon.getSetting("userdataCache") == 'true'
        self.XNEWA_SORT_RECURRING = addon.getSetting("recurringSort")
        self.XNEWA_SORT_RECORDING = int(addon.getSetting("recordingSort"))
        self.XNEWA_SORT_EPISODE = int(addon.getSetting("episodeSort"))
        self.NextPVR_STREAM = addon.getSetting("stream")

        self.XNEWA_PREBUFFER = int(addon.getSetting("prebuffer")) // 4
        self.XNEWA_POSTBUFFER = int(addon.getSetting("postbuffer")) // 4
        self.EPG_SCROLL_INT = int(addon.getSetting("scrollInterval"))
        self.EPG_DISP_INT = int(addon.getSetting("displayInterval"))
        self.EPG_RETR_INT = int(addon.getSetting("epgCache"))
        self.EPG_ROW_HEIGHT = int(addon.getSetting("epgRowHeight"))

        self.EPG_GROUP = addon.getSetting("group")

        self.XNEWA_INTERFACE = addon.getSetting('interface')
        if addon.getSetting('skin') != 'Classic':
            try:
                if xbmc.getSkinDir() == 'skin.estuary':
                        self.XNEWA_SKIN = 'Estuary'
                elif xbmc.getSkinDir() == 'skin.confluence':
                    self.XNEWA_SKIN = 'Confluence'
                else:
                    xbmc.log(xbmc.getSkinDir())
                    self.XNEWA_SKIN = addon.getSetting('skin')
            except:
                xbmc.log('Could not auto-detect skin')
                xbmc.log(xbmc.getSkinDir())
        else:
            self.XNEWA_SKIN = 'Default'
        self.XNEWA_WEBCLIENT = addon.getSetting('webclient') == 'true'
        self.XNEWA_CLIENT_SIZE = addon.getSetting('client_size')
        self.XNEWA_CLIENT_QUALITY = addon.getSetting('client_quality') == 'true'
        self.XNEWA_CLIENT = addon.getSetting("client")
        if  self.XNEWA_CLIENT ==  '':
            addon.setSetting("client",self.XNEWA_MAC)
        elif  self.XNEWA_CLIENT ==  'multi-kodis':
            import random
            self.XNEWA_CLIENT = str(int(round(random.random()*1000)))

        self.XNEWA_LIVE_SKIN = addon.getSetting('liveSkin') == 'true'
        self.XNEWA_CONTEXT_STOP = addon.getSetting('stopContext') == 'true'
        self.XNEWA_CONTEXT_POP = addon.getSetting('popContext') == 'true'

        self.VLC_VIDEO_SIZE = int(addon.getSetting("strmVideoSize"))
        self.VLC_VIDEO_BITRATE = addon.getSetting("strmBitRate")
        self.VLC_AUDIO_BITRATE = int(addon.getSetting("strmAudioBitrate"))
        self.TRANSCODE_PROFILE = addon.getSetting("resTranscode") + 'p-' + addon.getSetting("bitrateTranscode")+'kbps'
        self.XNEWA_READONLY = False
        self.XNEWA_COLOURS = None
        xbmc.log("config loaded from setting")
        return
