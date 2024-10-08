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

from __future__ import absolute_import, division, unicode_literals
from future import standard_library
from future.builtins import *
standard_library.install_aliases()
from builtins import hex
from builtins import str
from builtins import range
from builtins import object

import os
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs

import sys
if sys.version_info[0] >=  3:
    pseudovfs = xbmcvfs
else:
    pseudovfs = xbmc
from kodi_six.utils import py2_encode, py2_decode
import operator
import datetime
import time
from threading import Thread
try:
    from urllib.parse import urlparse, quote, unquote
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError, URLError
    from urllib import quote, unquote, urlretrieve

from fix_utf8 import smartUTF8
from xbmcaddon import Addon
__language__ = Addon('script.kodi.knewc').getLocalizedString

from XNEWAGlobals import *
from enum_keys import *

import socket
import json

class videoState(object):
    started, stopped, playing, error, inactive = list(range(5))

class SDL(object):
    disabled, inactive, lite, full = list(range(4))

try :
    if os.name == 'nt':
        from ctypes import windll, Structure, c_long, byref  # wintypes
        class POINT(Structure):
            _fields_ = [("x", c_long), ("y", c_long)]

        class RECT(Structure):
            _fields_ = [("left", c_long),
                ("top", c_long),
                ("right", c_long),
                ("bottom", c_long)]
    else:
        from xdo import Xdo
        xdo = Xdo()
except Exception as err:
    windll = None
    xdo = None
    print (err)

# ==============================================================================
class EmulateWindow(xbmcgui.WindowXML):


    def __init__(self, *args, **kwargs):
        self.closed = False
        self.win = None
        self.ready = False
        self.renderstop = False
        self.rendering = False
        self.exit = False
        self.settings = kwargs['settings']
        self.xnewa = kwargs['xnewa']
        if 'sdl-' in self.xnewa.client:
            self.sdlmode = SDL.full
        else:
            self.sdlmode = SDL.disabled
        self.errors = 0

        self.listings = None
        self.prev_channel = None
        self.channel_number = None
        self.recent = [0,0]
        self.skipStop = False
        self.inControl = False
        self.wasFullScreen = True
        self.t1 = None
        self.state = videoState.inactive
        self.osdMode = False
        self.lastMouseMove = 0
        self.timeout = 0
        self.keyTimeout = time.time()
        self.pauseActivity = False

    def onInit(self):
        if not self.win:
            xbmc.executebuiltin(XBMC_DIALOG_BUSY_OPEN)
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.sidUpdate()

            self.base = self.xnewa.getURL()
            self.setOSDMode(True)
            self.image = self.getControl(100)
            self.debugBack = self.getControl(110)
            self.debug = self.getControl(120)
            if self.sdlmode != SDL.disabled and self.settings.XNEWA_LIVE_SKIN:
                self.win.setProperty('sdlmode', 'true')
            else:
                self.win.setProperty('sdlmode', 'false')

            #self.status = self.getControl(120)
            #self.status.setImage('NextPVR.png')
            self.getForcedScreen()
            self.ready = True
            xbmc.executebuiltin(XBMC_DIALOG_BUSY_CLOSE)
            t = Thread(target=self.render)
            t.start()


    def onClick(self, controlId):
        pass

    def exitCleanUp(self, sidDelete=False):
        if xbmc.Player().isPlayingVideo():
            xbmc.Player().stop()
            self.renderstop = False
            while self.state == videoState.playing:
                xbmc.sleep(100)
        import glob
        fileNames = glob.glob(pseudovfs.translatePath('special://temp') + 'knew5/emulate*.[pj][pn]g' )
        for file in fileNames:
            try:
                os.remove(file)
            except:
                xbmc.log('Error deleting ' + file)
        if sidDelete:
            self.xnewa.cleanCache('sid.p')
        self.exit = True
        self.close()

    def onFocus(self, controlId):
        pass

    def setOSDMode(self,action):
        if action != self.osdMode:
            if action == True:
                self.osdMode = True
                self.win.setProperty('showosd', 'true')
            else:
                self.osdMode = False
                self.win.setProperty('showosd', 'false')

    def callback(self,hwnd, extra):
        return

    def queryMousePosition(self):
        r = RECT()
        pt = POINT()
        windll.user32.GetCursorPos(byref(pt))
        hwnd = windll.user32.GetForegroundWindow()
        windll.user32.GetClientRect(hwnd, byref(r))
        windll.user32.ScreenToClient(hwnd, byref(pt))
        print ('{0} {1} {2} {3} click {4} {5}'.format(r.left, r.right, r.top,r.bottom, pt.x, pt.y))
        x = int( ((pt.x - r.left) / (r.right-r.left)) * 100.0 )
        y = int( ((pt.y - r.top ) / (r.bottom-r.top)) * 100.0 )
        return { "x": x, "y": y}

    def xdoqueryMousePosition(self):
        kodi =  xdo.get_active_window()
        wl = xdo.get_window_location(kodi)
        ws = xdo.get_window_size(kodi)
        mouse = xdo.get_mouse_location()
        left = wl.x
        right = left + ws.width
        if wl.y == 0:
            top = 0
        else:
            top = wl.y - self.XNEWA_TITLE_BAR_SIZE
        bottom = top + ws.height
        print ('{0} {1} {2} {3} click {4} {5}'.format(left, right, top,bottom, mouse.x, mouse.y))
        x = int( ((mouse.x - left) / (right-left)) * 100.0 )
        y = int( ((mouse.y - top ) / (bottom-top)) * 100.0 )
        return { "x": x, "y": y}


    def onAction(self, action):
        self.keyTimeout = time.time()
        try:
            actionID = action.getId()
            buttonID = action.getButtonCode()
        except: return
        url = None
        if actionID == ACTION_MOUSE_MOVE:
            ms = datetime.datetime.now().microsecond
            ms = int(round(time.time() * 1000))

            if self.lastMouseMove + 250 < ms:
                url = self.base + '/control?move=49x57'  + self.xnewa.client
                self.lastMouseMove = ms + 2000
            else:
                self.lastMouseMove = ms
                return
        ignoreKeys = ( 61650, 61651, 127184, 127185, 323749, 323796 )
        if buttonID in ignoreKeys:
            return
        if not self.ready or self.renderstop:
            return
        dt = datetime.datetime.now()
        now = int(time.mktime(dt.timetuple()))
        if now == self.recent[0]:
            if self.recent[1] == 2:
                xbmc.log('too fast')
                return
            self.recent[1] = self.recent[1] + 1
        else:
            self.recent[0] = now
            self.recent[1] = 0

        if self.onLiveAction(actionID,buttonID) == True:
            return

        longPress = False
        if buttonID & 0x1000000:
            if buttonID & 0xff0000:
                return
            #these are long presses
            longPress = True
            # if actionID not in CONTEXT_MENU and buttonID not in CONTEXT_MENU and buttonID != MOVEMENT_UP:
            #     return
            if actionID in MOVEMENT_UP:
                actionID = ACTION_FIRST_PAGE
                buttonID = 0
            else:
                return

        self.renderstop = True
        self.inControl = True
        keyBase = self.base + '/control?time=' + str(now) + '&key='
        self.pauseActivity = True
        if actionID == ACTION_PLAYER_PLAY:
            url = keyBase + str(ENUM_KEY_P | ENUM_KEY_CONTROL)
        elif actionID == ACTION_STOP:
            url = keyBase + str(ENUM_KEY_S | ENUM_KEY_CONTROL)
            if self.state != videoState.inactive:
                self.state = videoState.stopped
        elif actionID == ACTION_NEXT_ITEM:
            if buttonID & 0xf046 == 0xf046 :
                url = keyBase + str(ENUM_KEY_F | ENUM_KEY_CONTROL)
            else:
                url = keyBase + str(ENUM_KEY_RIGHT | ENUM_KEY_CONTROL)
        elif actionID == ACTION_PREV_ITEM:
            if xbmc.Player().isPlayingVideo():
                if '/live?channel' not in xbmc.Player().getPlayingFile():
                    url = keyBase + str(ENUM_KEY_LEFT | ENUM_KEY_CONTROL)
            else:
                # send ctrl-b doesn't work
                url =  keyBase + str(ENUM_KEY_LEFT | ENUM_KEY_CONTROL)
        elif actionID == ACTION_PLAYER_FORWARD:
            url = keyBase + str(ENUM_KEY_F| ENUM_KEY_CONTROL)
        elif actionID == ACTION_PLAYER_REWIND:
            url = keyBase + str(ENUM_KEY_R | ENUM_KEY_CONTROL)
        elif actionID == ACTION_FIRST_PAGE or actionID == ACTION_INFO:
            #home
            if self.state == videoState.playing:
                # send ctrl-b
                url = keyBase + str(ENUM_KEY_B | ENUM_KEY_CONTROL)
            else:
                url = keyBase + ENUM_KEY_HOME
            self.pauseActivity = False
        elif buttonID >= 0x2f041 and buttonID <= 0x2f05a:
            # shifted letters
            url = keyBase + str(buttonID&0xff)
        elif actionID == ACTION_MOUSE_LEFT_CLICK or actionID == ACTION_MOUSE_DOUBLE_CLICK:
            pos = None
            if os.name == 'nt' and windll != None:
                try:
                    pos = self.queryMousePosition()
                except Exception as e:
                    print (e)
            elif os.name != 'nt' and xdo != None:
                try:
                    pos = self.xdoqueryMousePosition()
                except Exception as e:
                    print (e)
            if pos is not None:
                if actionID == ACTION_MOUSE_DOUBLE_CLICK:
                    action = '&dbl'
                else:
                    action = '&'
                action += 'click='
                url = self.base + '/control?time=' + str(now) +  action + str(pos['x']) + 'x' + str(pos['y'])
                self.pauseActivity = True

        elif buttonID & 0x10000:
            ctrl = buttonID&0xff
            if ctrl == 0x50:
                url = keyBase + str(ENUM_KEY_P | ENUM_KEY_CONTROL)
            elif ctrl == 0x53:
                url = keyBase + str(ENUM_KEY_S | ENUM_KEY_CONTROL)
                self.renderstop = False
                xbmc.Player().stop()
            elif ctrl == 0x4b:
                url = keyBase + str(ENUM_KEY_K | ENUM_KEY_CONTROL)
            elif ctrl == 0x52:
                url = keyBase + str(ENUM_KEY_R | ENUM_KEY_CONTROL)
            elif ctrl == 0x82:
                url = keyBase + str(ENUM_KEY_LEFT | ENUM_KEY_CONTROL)
            elif ctrl == 0x83:
                url = keyBase + str(ENUM_KEY_RIGHT | ENUM_KEY_CONTROL)
            elif ctrl == 0x42:
                url = keyBase + str(ENUM_KEY_P | ENUM_KEY_CONTROL)
            elif ctrl == 0x46:
                url = keyBase + str(ENUM_KEY_F | ENUM_KEY_CONTROL)
            elif ctrl == 0x57:
                url =  keyBase + str(ENUM_KEY_W | ENUM_KEY_CONTROL)
            elif ctrl == 0x47:
                url = keyBase + ENUM_KEY_F1
            elif ctrl == 0x4d and buttonID & 0x30000:
                myKey = self.getContext()
                if myKey != None:
                    url = keyBase + myKey
            elif ctrl == 0x4f:
                url = keyBase + ENUM_KEY_F8
            elif ctrl == 0x54:
                url = keyBase + ENUM_KEY_F2
            else:
                pass
                #print actionID, buttonID, hex(ctrl), hex(actionID)
        elif actionID == ACTION_RECORD or actionID == ACTION_QUEUE_ITEM:
            url = keyBase + str(ENUM_KEY_K | ENUM_KEY_CONTROL)
        elif actionID == ACTION_PAUSE:
            url = keyBase + ENUM_KEY_SPACE
        elif buttonID == 0xf02e:
            url = keyBase + '46'
        elif actionID in MOVEMENT_LEFT:
            url = keyBase + str(ENUM_KEY_LEFT)
        elif actionID in MOVEMENT_UP:
            url = keyBase + ENUM_KEY_UP
            if xbmc.Player().isPlayingVideo():
                if '/live?channel' not in xbmc.Player().getPlayingFile() and self.osdMode == False:
                    url = keyBase + str(ENUM_KEY_F | ENUM_KEY_CONTROL)
            else:
                self.pauseActivity = False
        elif actionID in MOVEMENT_RIGHT:
            url = keyBase + str(ENUM_KEY_RIGHT)
        elif actionID in MOVEMENT_DOWN or buttonID == 0xf064:
            url = keyBase + ENUM_KEY_DOWN
            if xbmc.Player().isPlayingVideo():
                if '/live?channel' not in xbmc.Player().getPlayingFile() and self.osdMode == False:
                    url = keyBase + str(ENUM_KEY_R | ENUM_KEY_CONTROL)
            else:
                self.pauseActivity = False
        elif actionID in MOVEMENT_SCROLL_UP:
            url = keyBase +  ENUM_KEY_PAGEUP
        elif actionID in MOVEMENT_SCROLL_DOWN:
            url = keyBase + ENUM_KEY_PAGEDOWN
        elif actionID >= 58 and actionID <= 67:
            # numbers maybe numpad
            url = keyBase + str(actionID-10)
        elif actionID >= 142 and actionID <= 149:
            url = keyBase + str(actionID-92)
        elif actionID == ACTION_SELECT_ITEM:
            url = keyBase + ENUM_KEY_ENTER
        elif actionID == KEYBOARD_BACK or buttonID == 61575:
            url = keyBase + ENUM_KEY_BACKSPACE
        elif actionID in EXIT_SCRIPT:
            url = keyBase + ENUM_KEY_BACK
        elif actionID in CONTEXT_MENU or buttonID in CONTEXT_MENU:
            myKey = self.getContext()
            if myKey != None:
                url = keyBase + myKey
        elif actionID == ACTION_TELETEXT_RED:
            url = keyBase + str(ENUM_KEY_R | ENUM_KEY_ALT)
        elif actionID == ACTION_TELETEXT_GREEN:
            url = keyBase + str(ENUM_KEY_G | ENUM_KEY_ALT)
        elif actionID == ACTION_TELETEXT_YELLOW:
            url = keyBase + str(ENUM_KEY_Y | ENUM_KEY_ALT)
        elif actionID == ACTION_TELETEXT_BLUE:
            url = keyBase + str(ENUM_KEY_B | ENUM_KEY_ALT)
        elif buttonID >= 0xf030 and buttonID <= 0xf039:
            #remote numbers and numpad
            url = keyBase + str(buttonID-0xf030+48)
        elif buttonID >= 0xf041 and buttonID <= 0x5a:
            # letters
            if self.state == videoState.playing and buttonID == 0x5a:
                buttonID = int(ENUM_KEY_F7)
            url = keyBase + str(buttonID & 0xff)
        elif buttonID >= 0xf090 and buttonID <= 0xf09b:
            #fn keys
            button = buttonID & 0xff
            fn = 'F' + str(button - 143)
            url = keyBase + self.userKey(fn, fn, button - 32)
        elif buttonID == 0xf09b:
            #F12 exit
            self.exitCleanUp(True)
        elif buttonID == 0x4f092:
            #alt-f4'
            url = keyBase + str(0x40073)
        elif buttonID & 0x40000 or buttonID & ENUM_KEY_CONTROL:
            buttonID = buttonID | 0x40000
            url = keyBase + str(buttonID & 0x400ff)
        elif actionID == 122 or actionID == 999 :
            if buttonID == 50:
                #guide
                url = keyBase + self.userKey('guide', 'F1', ENUM_KEY_F1)
            elif buttonID == 49:
                # TV
                url = keyBase + self.userKey('mytv', 'F8', ENUM_KEY_F8)
            elif buttonID == 101:
                # recordedtv
                url = keyBase + self.userKey('recordedtv', 'HOME', ENUM_KEY_HOME)
            elif buttonID == 24:
                #live tv
                url = keyBase + self.userKey('livetv', 'F2', ENUM_KEY_F2)
            elif buttonID == 7:
                #my videos
                url = keyBase + self.userKey('myvideos', 'F3', ENUM_KEY_F3)
            elif buttonID == 9:
                #my music
                url = keyBase + self.userKey('mymusic', 'F4', ENUM_KEY_F4)
            elif buttonID == 6:
                #my pictures
                url = keyBase + self.userKey('mypictures', 'F9', ENUM_KEY_F9)
            elif buttonID == 248:
                #my radio
                url = keyBase + self.userKey('liveradio', 'F10', ENUM_KEY_F10)
            elif buttonID == 44:
                #subtitle
                xbmc.executebuiltin('Action( NextSubtitle )')
            elif buttonID == 196:
                # power off
                self.exitCleanUp()
                pass
            elif buttonID == 213:
                #display
                url = keyBase + ENUM_KEY_F8
            else:
                xbmc.log('remote action unsupported {0} {1}'.format(actionID, buttonID))
                pass
        else:
            xbmc.log('action unsupported {0} {1}'.format(actionID, buttonID))
            pass
        if url :
            url = url + self.xnewa.client
            #while self.rendering:
            #    time.sleep(0.1)
            if self.getControlEx(url, True) == 200:
                xbmc.sleep(25)

        self.renderstop = False
        self.inControl = False
        self.ready = True

    def userKey(self, hash, enum, keyValue) :
        key = self.xnewa.tryKeyEnum(hash, enum )
        if key == None:
            skey = str(keyValue)
        else:
            skey = str(key)
        return skey

    def onLiveAction(self,actionID,buttonID):
        retval = False
        if xbmc.Player().isPlayingVideo():
            if self.sdlmode != SDL.disabled:
                #xbmc.log('video {0} {1}'.format(actionID, buttonID))
                if buttonID == 0xf049 or buttonID == 0x1f042 or buttonID == 0x4f042:
                    # toggle OSD
                    if self.win.getProperty('showosd') == 'true':
                        self.setOSDMode(False)
                    else:
                        self.setOSDMode(True)
                elif (actionID == 26 and buttonID != 0) or buttonID == 0xf023  or buttonID == 0xf054:
                    #subtitle from remote or #
                    xbmc.executebuiltin('Action( NextSubtitle )')
                    retval = True
                elif actionID == REMOTE_BACK or actionID == ACTION_BACK or actionID == ACTION_SHOW_GUI:
                    if xbmcgui.getCurrentWindowId() == 12005:
                        xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
                        self.wasFullScreen = True
                        self.setOSDMode(True)
                    else:
                        xbmc.Player().stop()
                    retval = True
                elif actionID == ACTION_PLAYER_FORWARD:
                    xbmc.executebuiltin('PlayerControl(tempoup)')
                    retval = True
                elif actionID == ACTION_SHOW_OSD or actionID == ACTION_SELECT_ITEM:
                    if '/live?channel' not in xbmc.Player().getPlayingFile() and self.osdMode == False:
                        xbmc.executebuiltin('Action(OSD,fullscreenvideo)')
                        retval = True
                elif actionID == ACTION_PLAYER_REWIND:
                    xbmc.executebuiltin('PlayerControl(tempodown)')
                    retval = True
                elif actionID == ACTION_BUILT_IN_FUNCTION:
                    if buttonID == 0xf04d:
                        #xbmc.executebuiltin('Action(OSD,fullscreenvideo)')
                        pass
                    retval = True
                elif buttonID == 0xf027 or actionID == ACTION_SMALL_STEP_BACK:
                    # 'small step'
                    xbmc.executebuiltin('Seek(-7))')
                    retval = True
                elif buttonID == 0x4f059:
                    #alt y
                    xbmc.executebuiltin('ActivateWindow(osdvideosettings)')
                    retval = True
                elif buttonID == 0x4f047 or actionID == 25:
                    #alt g
                    xbmc.executebuiltin('ActivateWindow(osdaudiosettings)')
                    retval = True
                elif buttonID == 0xf04f:
                    xbmc.executebuiltin('ActivateWindow(PlayerProcessInfo)')
                    retval = True
                elif buttonID == 0xf05a or buttonID == 0xf096 or actionID == ACTION_ASPECT_RATIO:
                    xbmc.executebuiltin('Action(AspectRatio,fullscreenvideo)')
                    retval = True
                elif actionID == ACTION_CONTEXT_MENU and self.settings.XNEWA_CONTEXT_STOP == True:
                    xbmc.Player().stop()
                    retval = True
                #print 'video pass', actionID, buttonID, retval
            else:
                xbmc.log('video {0} {1}'.format(actionID, buttonID))
                if self.settings.XNEWA_LIVE_SKIN:
                    self.debug.setLabel('actionID: ' + str(actionID) + ' buttonID: ' + str(hex(buttonID)))
                if actionID == REMOTE_BACK:
                    xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
                    self.wasFullScreen = True
                    self.setOSDMode(True)
                retval = True
        return retval
    def render(self):
        fullRefresh = 0
        monitor = xbmc.Monitor()
        while monitor.abortRequested() == False and self.exit == False:
            if not xbmc.Player().isPlayingVideo():
                if self.state == videoState.started:
                    if isinstance(self.t1, Thread):
                        #print self.t1.is_alive(), self.renderstop, self.state, xbmc.Player().isPlayingVideo()
                        if self.t1.is_alive() == False:
                            self.state = videoState.error
                        elif xbmc.Player().isPlayingAudio():
                            self.state = videoState.inactive

                if self.renderstop == False:
                    fullRefresh += 1
                    if fullRefresh < 30 and self.state == videoState.inactive:
                        if self.inControl == False and self.xnewa.sid != None:
                            self.getActivity(True)
                            if self.renderstop == True:
                                self.renderstop = False
                                self.getControlEx(showImage=True)

                    else:
                        fullRefresh = 0
                        import glob
                        fileNames = glob.glob(pseudovfs.translatePath('special://temp') + 'knew5/emulate*.[pj][pn]g' )
                        for file in fileNames:
                            try:
                                os.remove(file)
                            except:
                                xbmc.log('Error deleting ' + file)

                        if self.state == videoState.playing or self.state == videoState.error or self.state == videoState.stopped:
                            if self.sdlmode != SDL.disabled:
                                if self.skipStop == False:
                                    xbmc.log('Stop state : {}'.format(self.state))
                                    url = self.base + '/control?media=stop'
                                    if self.state == videoState.error:
                                        url += '&message=Player%20error'
                                    url += self.xnewa.client
                                    self.getControlEx(url, False)
                                else:
                                    self.skipStop = False
                            else:
                                #url = self.base + '/control?key=131155' + self.xnewa.client
                                url = self.base + '/control?key=' + str(83|ENUM_KEY_CONTROL) + self.xnewa.client
                                self.getControlEx(url, True)

                            self.setOSDMode(True)
                            self.sidUpdate()
                            self.state = videoState.inactive
                            self.xnewa.logMessage('Stopped playback')

                            url = self.base + '/control?key=131188' + self.xnewa.client
                            self.getControlEx(url, True)
            else:
                self.state = videoState.playing
                if self.sdlmode == SDL.full:
                    if self.wasFullScreen:
                        if xbmc.getCondVisibility('videoplayer.isfullscreen') == False:
                            self.wasFullScreen = False
                            url = self.base + '/control?move=49x57'  + self.xnewa.client
                            self.setOSDMode(False)
                            self.getControlEx(url, True)

                    try:
                        url = self.base + '/control?media=' + str(xbmc.Player().getTime())  + self.xnewa.client
                        code = self.getControlEx(url, xbmc.getCondVisibility('videoplayer.isfullscreen') == False)
                        if code == 204:
                            self.setOSDMode(False)
                        else:
                            xbmc.log('OSD video render {}'.format(code))
                        self.skipStop = False
                    except Exception as err:
                        print(err)
                        pass
                self.getActivity()

            current = time.time()
            if xbmc.Player().isPlaying():
                self.keyTimeout = current
            elif current > self.keyTimeout + 600:
                xbmc.log('No activity timeout. Exit knewc')
                self.exit = True
                self.close()
                if self.settings.XNEWA_WEBCLIENT == True:
                    xbmc.executebuiltin('ActivateWindow(favourites)')
                return

            xbmc.sleep(1000)
        return

    def sidUpdate(self,):
        if self.xnewa.sid != None:
            self.xnewa.getRecordingUpdate()
        if self.xnewa.sid == None:
            self.xnewa.sidLogin()

    def getContext(self):
        if self.settings.XNEWA_CONTEXT_POP == False:
            self.exitCleanUp()
            return
        url = None
        keyBase = ''
        dialog = xbmcgui.Dialog()
        value = dialog.select( 'Enter selection', [  'Remote Keys', 'Recordings',  'TV Guide',  "What's New", 'Scheduler' , 'Exit UI Client', '0', '1', '2', '3', '4', '5','6', '7', '8', '9'])
        xbmc.log(str(value))

        if value == 5:
            self.exitCleanUp()
        elif value == 2:
            url = keyBase + ENUM_KEY_F1
        elif value == 1:
            url = keyBase + ENUM_KEY_F8
        elif value == 3:
            url = keyBase + ENUM_KEY_F10
        elif value == 4:
            url = keyBase + ENUM_KEY_F9
        elif value == 0:
            value = dialog.select( 'Navigation Selection', [ 'Home', 'Page Up', 'Page Down', 'Fast Forward', 'Rewind', 'Skip Next', 'Skip Previous', 'Red', 'Green', 'Yellow', 'Blue'])
            xbmc.log(str(value))
            if value == 0:
                url = keyBase + ENUM_KEY_HOME
            elif value == 1:
                url = keyBase + ENUM_KEY_PAGEUP
            elif value == 2:
                url = keyBase + ENUM_KEY_PAGEDOWN
            elif value == 3:
                url = keyBase + str(ENUM_KEY_F | ENUM_KEY_CONTROL)
            elif value == 4:
                url = keyBase + str(ENUM_KEY_R| ENUM_KEY_CONTROL)
            elif value == 5:
                url = keyBase + str(ENUM_KEY_RIGHT | ENUM_KEY_CONTROL)
            elif value == 6:
                url = keyBase + str(ENUM_KEY_LEFT | ENUM_KEY_CONTROL)
            elif  value == 7:
                url = keyBase + str(ENUM_KEY_R | ENUM_KEY_ALT)
            elif  value == 8:
                url = keyBase + str(ENUM_KEY_G | ENUM_KEY_ALT)
            elif  value == 9:
                url = keyBase + str(ENUM_KEY_Y | ENUM_KEY_ALT)
            elif  value == 10:
                url = keyBase + str(ENUM_KEY_B | ENUM_KEY_ALT)
        elif  value >=6 and value <= 15:
            # numbers
            url = keyBase + str(value + 42)
        return url

    def getForcedScreen(self):
        self.rendering = True
        self.errors = 0
        retval = True
        try:
            if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                url = self.base + '/control?res=' + self.settings.XNEWA_CLIENT_SIZE
                if self.settings.XNEWA_CLIENT_QUALITY == True:
                    url += '&quality=high'
                url += self.xnewa.client
                self.getControlEx(url, False)
                if self.sdlmode != SDL.disabled:
                    url = self.base + '/control?media=stop' + self.xnewa.client
                    if self.getControlEx(url, False) != 200:
                        self.getControlEx(url, False)
            else:
                self.exit = True
                self.close()
                return False

            self.getControlEx(None, True)

        except Exception as err:
            print(err)
            retval = False

        self.rendering = False
        return retval


    def getControlEx(self, url=None, showImage=True):
        code = 0
        if url == None:
            url = self.base + '/control?format=json' + self.xnewa.client
            if self.settings.XNEWA_CLIENT_QUALITY == True:
                url += '&quality=high'

        xbmc.log(url)
        try:
            jpgfile = urlopen(url, timeout=10)
            if showImage and jpgfile.code == 200:
                screenFile = pseudovfs.translatePath('special://temp') + 'knew5/emulate-'+ str(time.time())
                if xbmc.Player().isPlayingVideo():
                    screenFile += ".png"
                else:
                    screenFile += ".jpg"
                output = open(screenFile,'wb')
                output.write(jpgfile.read())
                output.close()
                self.setOSDMode(True)
                self.image.setImage(screenFile,False)
                if self.pauseActivity:
                    self.getActivity()
            code = jpgfile.code
            if code == 204 and self.pauseActivity:
                self.getActivity()
        except HTTPError as e:
            code = e.code
            xbmc.log(str(e.code))
            if e.code == 404:
                xbmc.sleep(500)
                self.errors = self.errors + 1
            elif e.code == 403:
                self.sidUpdate()
                self.getSid()
                self.errors = self.errors + 1
        except URLError as err:
            code = err.errno
            leave = True
            if isinstance(err.reason, socket.timeout):
                self.timeout += 1
                leave = xbmcgui.Dialog().yesno('NextPVR timeout', 'Do you want to exit UI client?', autoclose=10000)
                xbmc.sleep(250)
            if leave == True:
                self.exit = True
                self.close()
        except Exception as err:
            print (err)
            code = -1
            leave = True
            if str(err) == 'timed out':
                self.timeout += 1
                leave = xbmcgui.Dialog().yesno('NextPVR timeout', 'Do you want to exit UI client?', autoclose=10000)
                xbmc.sleep(250)
            if leave == True:
                self.exit = True
                self.close()
        return code


    def getActivity(self, update=False):
        if update:
            url = self.base + '/activity?format=json&updates=1'  + self.xnewa.client
        else:
            url = self.base + '/activity?format=json' + self.xnewa.client
        xbmc.log(url)
        try:
            json_file = urlopen(url, timeout=30)
            jsonActivity = json.load(json_file)
            json_file.close()
            xbmc.log(str(jsonActivity))
            if 'url' in jsonActivity:
                import re
                if jsonActivity['url'] != '':
                    self.nextUrl = re.sub('[^?&]*client[^&]+&*','',jsonActivity['url'],re.UNICODE)
                    m = re.search(r'seek=(\d+)&', self.nextUrl)
                    if m:
                        seek  = int(m.group(1))
                        self.nextUrl = re.sub(r'seek=(\d+)&','',self.nextUrl)
                        if 'recording_resume' not in jsonActivity:
                            if self.state == videoState.playing:
                                xbmc.Player().seekTime(seek)
                                return
                            else:
                                jsonActivity['recording_resume'] = seek
                    self.nextUrl = unquote(self.nextUrl)
                    if self.state == videoState.playing:
                        self.skipStop = True
                    self.quickPlayer(jsonActivity)
            elif 'playlist' in jsonActivity:
                self.quickPlayer(jsonActivity)
            elif 'action' in jsonActivity:
                if jsonActivity['action'] == 'exit':
                    xbmc.sleep(250)
                    self.exitCleanUp(True)
                    return
                elif jsonActivity['action'] == 'stop':
                    if xbmc.Player().isPlayingVideo():
                        xbmc.Player().stop()
                    self.setOSDMode(True)
                    url = self.base + '/control?media=stop' + self.xnewa.client
                    self.getControlEx(url, False)
            elif 'needsRendering' in jsonActivity:
                if jsonActivity['needsRendering'] ==  True:
                    if isinstance(self.t1, Thread):
                        if self.t1.is_alive()  and self.state == videoState.playing:
                            xbmc.log('player no render')
                            self.renderstop = False
                        else:
                            self.renderstop = True
                    else:
                        self.renderstop = True
            self.InControl = False
        except URLError as err:
            print(err)
            self.exit = True
            self.close()
        except Exception as err:
            print(err)


#################################################################################################################
    def quickPlayer (self,activity):
        from . import details
        #print self.nextUrl
        Audio = False
        self.wasFullScreen = True
        windowed = self.settings.XNEWA_LIVE_SKIN
        if 'playlist' in activity:
            import os
            import re
            dd = {}
            xbmc.PlayList(0).clear()
            for playlist in activity['playlist']:
                nextUrl = re.sub('[^?&]*client[^&]+&*','',playlist['url'].encode('utf-8'))
                xbmc.log(nextUrl)
                url = nextUrl.split('=',1)[1]
                if url[0:2]=='\\\\':
                    url = 'smb:'+ url.replace('\\','/')
                if xbmcvfs.exists(url) == False:
                    s = self.base + playlist['url'].replace(' ','+').replace('&f=','&mode=http&f=')
                    xbmc.log(s)
                    xbmc.PlayList(0).add(s)
                else:
                    xbmc.PlayList(0).add(url)
            dd['movie'] = False
            dd['playlist'] = xbmc.PlayList(0)
            windowed = False
        elif self.nextUrl.startswith('/live?channel'):
            try:
                #v5
                if self.settings.XNEWA_INTERFACE == 'XML' or self.settings.XNEWA_INTERFACE == 'Version5':
                    url = self.base + '/service?method=channel.listings.current' + self.xnewa.client + '&channel_id=' + str (activity['channel_id'])
                    xbmc.log(url)
                    dd1 = self.xnewa._progs2array_xml(url)
                else:
                    url = self.base + '/public/GuideService/Listing' + self.xnewa.jsid + '&channelId=' + str (activity['channel_id'])
                    xbmc.log(url)
                    dd1 = self.xnewa._progs2array_json(url)
                dd = dd1[0]['progs'][0]
                dd['program_oid'] = dd['oid']
                #dd['season'] = 0
            except Exception as err:
                print(err)
                dd = {}
                dd['program_oid'] = 12346
                dd['title'] = activity['channel_name']
                dd['subtitle'] = str(activity['channel_number'])
                dd['end'] = ''
                dd['season'] = 0
                dd['desc'] = ''

            dd['channel_oid'] = activity['channel_id']
            channel = {}
            channel[0] = activity['channel_name']
            channel[1] = activity['channel_number']
            channel[2] = '0'
            self.prev_channel = self.channel_number
            self.channel_number = activity['channel_number']
            dd['channel'] = channel
            dd['bookmarkSecs'] = 0
            dd['movie'] = False
        elif self.nextUrl.startswith('/stream?'):
            dd = {}
            dd['title'] = 'title'
            dd['movie'] = False
            dd['filename'] = py2_decode(self.nextUrl.split('=',1)[1]).replace('http://plugin','plugin')
            dd['season'] = 0
            if 'duration' in activity:
                dd['library_duration'] = activity['duration']
            else:
                import re
                m = re.search('.*_(\d{2})(\d{2})(\d{2})(\d{2})(-\d)\.ts', dd['filename'])
                if m:
                    start = int(m.group(1)) * 60 + int(m.group(2))
                    end = int(m.group(3)) * 60 + int(m.group(4))
                    #print start
                    #print end
                    if start > end:
                        dd['library_duration'] = (start + end - 1440) * 60
                    else:
                        dd['library_duration'] = (end - start) * 60
            dd['filename'] = dd['filename'].replace('127.0.0.1',self.xnewa.ip)


            #self.getPlaybackPosition(dd['filename'])
            dd['nextUrl'] = self.nextUrl
            if 'recording_description' in activity:
                dd['desc'] = activity['recording_description']
            elif 'description' in activity:
                dd['desc'] = activity['description']
            else:
                dd['desc'] = ''

            if 'recording_title' in activity:
                dd['title'] = activity['recording_title']
            elif dd['filename'].startswith('http:'):
                if '.m3u8' not in  dd['filename']:
                    Audio = True
            elif 'title' in activity:
                dd['title'] = activity['title']

            if 'recording_subtitle' in activity:
                dd['subtitle'] = activity['recording_subtitle']
            elif 'subtitle' in activity:
                dd['subtitle'] = activity['subtitle']
            else:
                dd['subtitle'] = None

            if 'recording_resume' in activity:
                dd['bookmarkSecs'] = activity['recording_resume']
                dd['resume'] = activity['recording_resume']
            else:
                dd['bookmarkSecs'] = 0

            if 'album' in activity:
                Audio = True

            if 'recording_id' in activity:
                dd['recording_oid'] = activity['recording_id']
                dd['nextUrl'] = '/live?recording_id=' + dd['recording_oid']
                #if self.settings.NextPVR_ICON_DL == 'Yes' and self.xnewa.getShowIcon(dd['title']) is None:
                recdata = self.xnewa.getDetails(self.settings.NextPVR_USER,self.settings.NextPVR_PW,dd['recording_oid'],'R','Yes')
                dd['season'] = recdata['season']
                dd['episode'] = recdata['episode']
                dd['channel'] = recdata['channel']
                dd['start'] = recdata['start']
                dd['end'] = recdata['end']
            else:
                dd['recording_oid'] = 0

            if 'Genres' in activity:
                dd['genres'] = activity['Genres']
                for  genre in dd['Genres']:
                    if genre == "Movie" or genre == "Movies" or genre == "Film":
                        dd['movie'] = True
                        break
        detailDialog = details.DetailDialog("nextpvr_recording_details.xml",  WHERE_AM_I,self.settings.XNEWA_SKIN, xnewa=self.xnewa, settings=self.settings, oid=123, epg=True, type="R")
        xbmc.log(str(windowed))
        if self.sdlmode == SDL.disabled:
            self.setOSDMode(False)
            windowed = False
        if isinstance(self.t1, Thread):
            xbmc.Player().stop()
            while self.t1.is_alive():
                xbmc.sleep(100)
            self.renderstop = False


        self.t1 = Thread(target=detailDialog._myPlayer, args=(dd,None,windowed,Audio, self.sdlmode == SDL.disabled))
        self.t1.start()
        self.state = videoState.started
        return
