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
            self.getScreen(True)
            self.ready = True
            xbmc.executebuiltin(XBMC_DIALOG_BUSY_CLOSE)
            t = Thread(target=self.render)
            t.start()


    def onClick(self, controlId):
        pass

    def exitCleanUp(self):
        if xbmc.Player().isPlayingVideo():
            xbmc.Player().stop()
            self.renderstop = False
            while self.state == videoState.playing:
                xbmc.sleep(100)
        import glob
        fileNames = glob.glob(xbmcvfs.translatePath('special://temp') + 'knew5/emulate*.png' )
        for file in fileNames:
            try:
                os.remove(file)
            except:
                xbmc.log('Error deleting ' + file)
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
        try:
            actionID = action.getId()
            buttonID = action.getButtonCode()
        except: return
        if buttonID & 0x1000000:
            #these are long presses
            if actionID not in CONTEXT_MENU and buttonID not in CONTEXT_MENU:
                return
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
        retval = self.onLiveAction(actionID,buttonID)
        xbmc.log(str(retval))
        if retval == True:
            return

        self.renderstop = True
        self.inControl = True
        screenFile = xbmcvfs.translatePath('special://temp') + 'knew5/emulate-'+ str(time.time()) + '.png'
        keyBase = self.base + '/control?time=' + str(now) + '&key='
        pauseActivity = True
        if actionID == ACTION_PLAYER_PLAY:
            url = keyBase + str(80|0x20000)
        elif actionID == ACTION_STOP:
            url = keyBase + str(83|0x20000)
            if self.state != videoState.inactive:
                self.state = videoState.stopped
        elif actionID == ACTION_NEXT_ITEM:
            if buttonID & 0xf046 == 0xf046 :
                # NextPVR Ctrl-F
                url = keyBase + str(70|0x20000)

            else:
                url = keyBase + str(39|0x20000)
        elif actionID == ACTION_PREV_ITEM:
            if xbmc.Player().isPlayingVideo():
                if '/live?channel=' not in xbmc.Player().getPlayingFile():
                    url = keyBase + str(37|0x20000)
            else:
                # send ctrl-b doesn't work
                url =  keyBase + str(37|0x20000)
        elif actionID == ACTION_PLAYER_FORWARD:
            url = keyBase + str(70|0x20000)
        elif actionID == ACTION_PLAYER_REWIND:
            url = keyBase + str(82|0x20000)
        elif actionID == ACTION_FIRST_PAGE or actionID == ACTION_INFO:
            #home
            if self.state == videoState.playing:
                # send ctrl-b
                url = keyBase + str(66|0x20000)
            else:
                url = keyBase + '36'
            pauseActivity = False
        elif buttonID >= 0x2f041 and buttonID <= 0x2f05a:
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
                pauseActivity = True

        elif buttonID & 0x10000:
            ctrl = buttonID&0xff
            if ctrl == 0x50:
                url = keyBase + str(ctrl|0x20000)
            elif ctrl == 0x53:
                url = keyBase + str(ctrl|0x20000)
                self.renderstop = False
                xbmc.Player().stop()
            elif ctrl == 0x4b:
                url = keyBase + str(ctrl|0x20000)
            elif ctrl == 0x52:
                url = keyBase + str(ctrl|0x20000)
            elif ctrl == 0x82:
                url = keyBase + str(37|0x20000)
            elif ctrl == 0x83:
                url = keyBase + str(39|0x20000)
            elif ctrl == 0x42:
                url = keyBase + str(80|0x20000)
            elif ctrl == 0x46:
                url = keyBase + str(70|0x20000)
            elif ctrl == 0x57:
                url =  keyBase + str(87|0x20000)
            elif ctrl == 0x47:
                url = keyBase + str(112)
            elif ctrl == 0x4d and buttonID & 0x30000:
                myKey = self.getContext()
                if myKey != None:
                    url = keyBase + myKey
            elif ctrl == 0x4f:
                url = keyBase + str(119)
            elif ctrl == 0x54:
                url = keyBase + str(113)
            else:
                pass
                #print actionID, buttonID, hex(ctrl), hex(actionID)
        elif actionID == ACTION_RECORD or actionID == ACTION_QUEUE_ITEM:
            url = keyBase + str(75|0x20000)
        elif actionID == ACTION_PAUSE:
            url = keyBase + '32'
        elif buttonID == 0xf02e:
            url = keyBase + '46'
        elif actionID in MOVEMENT_LEFT:
            url = keyBase + '37'
        elif actionID in MOVEMENT_UP:
            url = keyBase + '38'
            if xbmc.Player().isPlayingVideo():
                if '/live?channel=' not in xbmc.Player().getPlayingFile() and self.osdMode == False:
                    url = keyBase + str(70|0x20000)
            else:
                pauseActivity = False
        elif actionID in MOVEMENT_RIGHT:
            url = keyBase + '39'
        elif actionID in MOVEMENT_DOWN or buttonID == 0xf064:
            url = keyBase + '40'
            if xbmc.Player().isPlayingVideo():
                if '/live?channel=' not in xbmc.Player().getPlayingFile() and self.osdMode == False:
                    url = keyBase + str(82|0x20000)
            else:
                pauseActivity = False
        elif actionID in MOVEMENT_SCROLL_UP:
            url = keyBase + '33'
        elif actionID in MOVEMENT_SCROLL_DOWN:
            url = keyBase + '34'
        elif actionID >= 58 and actionID <= 67:
            url = keyBase + str(actionID-10)
        elif actionID >= 142 and actionID <= 149:
            url = keyBase + str(actionID-92)
        elif actionID == ACTION_SELECT_ITEM:
            url = keyBase + '13'
        elif actionID == KEYBOARD_BACK or buttonID == 61575:
            url = keyBase + '8'
        elif actionID in EXIT_SCRIPT:
            url = keyBase + '27'
        elif actionID in CONTEXT_MENU or buttonID in CONTEXT_MENU:
            myKey = self.getContext()
            if myKey != None:
                url = keyBase + myKey
        elif actionID == ACTION_TELETEXT_RED:
            url = keyBase + str(82|0x40000)
        elif actionID == ACTION_TELETEXT_GREEN:
            url = keyBase + str(71|0x40000)
        elif actionID == ACTION_TELETEXT_YELLOW:
            url = keyBase + str(89|0x40000)
        elif actionID == ACTION_TELETEXT_BLUE:
            url = keyBase + str(66|0x40000)
        elif buttonID >= 0xf030 and buttonID <= 0xf039:
            url = keyBase + str(buttonID-0xf030+48)
        elif buttonID >= 0xf041 and buttonID <= 0xf05a:
            if self.state == videoState.playing and buttonID == 0xf05a:
                buttonID = 118
            url = keyBase + str(buttonID&0xff)
        elif buttonID >= 0xf090 and buttonID <= 0xf098:
            url = keyBase + str((buttonID&0xff)-32)
        elif buttonID == 0xf09b:
            #F12 exit
            self.exitCleanUp()
        elif buttonID == 0x4f092:
            #alt-f4'
            url = keyBase + str(0x40073)
        elif buttonID & 0x40000 or buttonID & 0x20000:
            buttonID = buttonID | 0x40000
            url = keyBase + str(buttonID&0x400ff)
        elif actionID == 122 or actionID == 999 :
            if buttonID == 50:
                #guide
                url = keyBase + '112'
            elif buttonID == 49 or buttonID == 101:
                # recordings
                url = keyBase + '119'
            elif buttonID == 24:
                #live tv
                url = keyBase + '113'
            elif buttonID == 7:
                #my videos
                url = keyBase + '114'
            elif buttonID == 9:
                #my music
                url = keyBase + '115'
            elif buttonID == 6:
                #my pictures
                url = keyBase + '116'
            elif buttonID == 248:
                #my radio
                url = keyBase + '117'
            elif buttonID == 44:
                #subtitle
                xbmc.executebuiltin('Action( NextSubtitle )')
            elif buttonID == 196:
                # power off
                self.exitCleanUp()
                pass
            elif buttonID == 213:
                #display
                url = keyBase + '119'
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
            xbmc.log(url)
            try:
                jpgfile = urlopen(url)
                output = open(screenFile,'wb')
                output.write(jpgfile.read())
                output.close()
                jpgfile.close()
                self.setOSDMode(True)
                self.image.setImage(screenFile,False)
                xbmc.sleep(25)
            except HTTPError as err:
                xbmc.log(str(err.code))
                print(err)
            except URLError as err:
                print(err)
                self.exit = True
                self.close()
            except Exception as err:
                print (err)
                self.exit = True
                self.close()
            if pauseActivity:
                self.getActivity()
        self.renderstop = False
        self.inControl = False
        self.ready = True

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
                    if self.osdMode == False:
                        xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
                        self.wasFullScreen = True
                        self.setOSDMode(True)
                        retval = True
                elif actionID == ACTION_PLAYER_FORWARD:
                    xbmc.executebuiltin('PlayerControl(tempoup)')
                    retval = True
                elif actionID == ACTION_SHOW_OSD or actionID == ACTION_SELECT_ITEM:
                    if '/live?channel=' not in xbmc.Player().getPlayingFile() and self.osdMode == False:
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
                        if self.t1.isAlive() == False:
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
                                self.getScreen()
                                self.getActivity()

                    else:
                        fullRefresh = 0
                        import glob
                        fileNames = glob.glob(xbmcvfs.translatePath('special://temp') + 'knew5/emulate*.png' )
                        for file in fileNames:
                            try:
                                os.remove(file)
                            except:
                                xbmc.log('Error deleting ' + file)

                        if self.state == videoState.playing or self.state == videoState.error or self.state == videoState.stopped:
                            if self.sdlmode != SDL.disabled:
                                if self.skipStop == False:
                                    try:
                                        print("Stop state",self.state)
                                        url = self.base + '/control?media=stop'
                                        if self.state == videoState.error:
                                            url += '&message=Player%20error'
                                        url += self.xnewa.client
                                        screenFile1 = xbmcvfs.translatePath('special://temp') + 'knew5/emulate-'+ str(time.time()) + '.png'
                                        xbmc.log(url)
                                        pngfile = urlopen(url)
                                        pngfile.close()
                                    except Exception as err:
                                        print(err)
                                else:
                                    self.skipStop = False
                            else:
                                #url = self.base + '/control?key=131155' + self.xnewa.client
                                url = self.base + '/control?key=' + str(83|0x20000) + self.xnewa.client
                                xbmc.log(url)
                                try:
                                    jpgfile = urlopen(url)
                                    screenFile = xbmcvfs.translatePath('special://temp') + 'knew5/emulate-'+ str(time.time()) + '.png'
                                    output = open(screenFile,'wb')
                                    output.write(jpgfile.read())
                                    output.close()
                                    self.image.setImage(screenFile,False)
                                    self.getActivity()
                                except Exception as err:
                                    print(err)

                            self.setOSDMode(True)
                            self.sidUpdate()
                            self.state = videoState.inactive
                            self.xnewa.logMessage('Stopped playback')

                            url = self.base + '/control?key=131188' + self.xnewa.client
                            xbmc.log(url)
                            try:
                                jpgfile = urlopen(url)
                                screenFile = xbmcvfs.translatePath('special://temp') + 'knew5/emulate-'+ str(time.time()) + '.png'
                                output = open(screenFile,'wb')
                                output.write(jpgfile.read())
                                output.close()
                                self.image.setImage(screenFile,False)
                                self.getActivity()
                            except Exception as err:
                                print(err)

                xbmc.sleep(1000)

            else:
                self.state = videoState.playing
                if self.sdlmode == SDL.full:
                    if self.wasFullScreen:
                        if xbmc.getCondVisibility('videoplayer.isfullscreen') == 0:
                            self.wasFullScreen = False
                            url = self.base + '/control?move=49x57'  + self.xnewa.client
                            screenFile1 = xbmcvfs.translatePath('special://temp') + 'knew5/emulate-a'+ str(time.time()) + '.png'
                            xbmc.log(url)
                            try:
                                pngfile = urlopen(url)
                                if pngfile.code == 200:
                                    output = open(screenFile1,'wb')
                                    output.write(pngfile.read())
                                    output.close()
                                    pngfile.close()
                                    self.image.setImage(screenFile1,False)
                                print (pngfile.code)
                                self.setOSDMode(False)
                                self.getActivity()
                            except Exception as err:
                                print(err)

                    try:
                        url = self.base + '/control?media=' + str(xbmc.Player().getTime())  + self.xnewa.client
                        screenFile1 = xbmcvfs.translatePath('special://temp') + 'knew5/emulate-'+ str(time.time()) + '.png'
                        xbmc.log(url)
                        request = Request(url)
                        pngfile = urlopen(request)
                        if pngfile.code == 200 and xbmc.getCondVisibility('videoplayer.isfullscreen') == 0:
                            output = open(screenFile1,'wb')
                            output.write(pngfile.read())
                            output.close()
                            self.image.setImage(screenFile1,False)
                            # needs rendering always true so just
                            self.getActivity()
                        elif pngfile.code == 204:
                            self.setOSDMode(False)
                        else:
                            print(pngfile.code)
                        pngfile.close()
                        self.skipStop = False
                    except Exception as err:
                        print(err)
                        pass
                self.getActivity()

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
        value = dialog.select( 'Enter selection', [  'Remote Keys', 'Recordings',  'TV Guide',  'Main Menu', 'Exit UI Client', '0', '1', '2', '3', '4', '5','6', '7', '8', '9'])
        xbmc.log(str(value))

        if value == 4:
            self.exitCleanUp()
        elif value == 2:
            url = keyBase + '112'
        elif value == 1:
            url = keyBase + '119'
        elif value == 3:
            url = keyBase + '120'
        elif value == 0:
            value = dialog.select( 'Navigation Selection', [ 'Home', 'Page Up', 'Page Down', 'Fast Forward', 'Rewind', 'Skip Next', 'Skip Previous', 'Red', 'Green', 'Yellow', 'Blue'])
            xbmc.log(str(value))
            if value == 0:
                url = keyBase + '36'
            elif value == 1:
                url = keyBase + '33'
            elif value == 2:
                url = keyBase + '34'
            elif value == 3:
                url = keyBase + str(70|0x20000)
            elif value == 4:
                url = keyBase + str(82|0x20000)
            elif value == 5:
                url = keyBase + str(39|0x20000)
            elif value == 6:
                url = keyBase + str(37|0x20000)
            elif  value == 7:
                url = keyBase + str(82|0x40000)
            elif  value == 8:
                url = keyBase + str(71|0x40000)
            elif  value == 9:
                url = keyBase + str(89|0x40000)
            elif  value == 10:
                url = keyBase + str(66|0x40000)
        elif  value >=5 and value <= 14:
            url = keyBase + str(value + 43)
        return url

    def getScreen(self, force=False):
        self.rendering = True
        self.errors = 0
        retval = True
        try:
            if force:
                if self.xnewa.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST):
                    url = self.base + '/control?size=' + self.settings.XNEWA_CLIENT_SIZE
                    if self.settings.XNEWA_CLIENT_QUALITY == True:
                        url += '&quality=high'
                    url += self.xnewa.client
                    xbmc.log(url)
                    try:
                        jpgfile = urlopen(url)
                        jpgfile.close
                        if self.sdlmode != SDL.disabled:
                            try:
                                url = self.base + '/control?media=stop' + self.xnewa.client
                                xbmc.log(url)
                                pngfile = urlopen(url)
                                pngfile.close()
                            except Exception as err:
                                print(err)

                    except HTTPError as e:
                        print(e.code)
                        if e.code == 404:
                            xbmc.sleep(500)
                            url = self.base + '/control?media=stop' + self.xnewa.client
                            xbmc.log(url)
                            pngfile = urlopen(url)
                            pngfile.close()
                            self.errors = self.errors + 1
                        elif e.code == 403:
                            self.sidUpdate()
                            self.getSid()
                            self.errors = self.errors + 1
                        else:
                            print(e)
                            self.exit = True
                            self.close()
                            return False
                        if self.errors < 3:
                            self.getScreen(force)
                            return False
                    except URLError as err:
                        print(err)
                        self.exit = True
                        self.close()

                else:
                    self.exit = True
                    self.close()
                    return False


            screenFile = xbmcvfs.translatePath('special://temp') + 'knew5/emulate-'+ str(time.time()) + '.png'

            url = self.base + '/control?format=json' + self.xnewa.client
            #xbmc.log(url)
            try:
                self.setOSDMode(True)
                jpgfile = urlopen(url)
                output = open(screenFile,'wb')
                output.write(jpgfile.read())
                output.close()
                self.image.setImage(screenFile,False)
            except HTTPError as e:
                xbmc.log(url)
                xbmc.log(str(e.code))
                retval = False
            except URLError as err:
                xbmc.log(url)
                print(err)
                xbmc.log('Abort emulation')
                self.exit = True
                self.close()
                retval = False

        except Exception as err:
            print(err)
            retval = False

        self.rendering = False
        return retval


    def getActivity(self, update=False):
        if update:
            url = self.base + '/activity?format=json&updates=1'  + self.xnewa.client
        else:
            url = self.base + '/activity?format=json' + self.xnewa.client
        import json
        xbmc.log(url)
        try:
            json_file = urlopen(url)
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
                    self.exit = True
                    xbmc.sleep(250)
                    import glob
                    fileNames = glob.glob(xbmcvfs.translatePath('special://temp') + 'knew5/emulate*.png' )
                    for file in fileNames:
                        try:
                            os.remove(file)
                        except:
                            xbmc.log('Leaving ' + file)
                    self.close()
                    return
                elif jsonActivity['action'] == 'stop':
                    url = self.base + '/control?media=stop' + self.xnewa.client
                    xbmc.log(url)
                    try:
                        pngfile = urlopen(url)
                        pngfile.close()
                    except Exception as err:
                        print(err)
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
                dd['nextUrl'] = '/live?recording=' + dd['recording_oid']
                # if self.settings.NextPVR_ICON_DL == 'Yes' and self.xnewa.getShowIcon(dd['title']) is None:
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