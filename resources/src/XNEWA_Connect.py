from __future__ import print_function
from __future__ import division

from future import standard_library
standard_library.install_aliases()
from builtins import chr
from builtins import str
from builtins import hex
from builtins import range
from builtins import object

from  KNEW_Client import *

######################################################################################################
# Class for connecting to a NextPVR instance
#
# Usage: Instantiate a new class with ip and portnumber
#  I.e. xnewa = new XNEWA_Connect('127.0.0.1', 80)
# Then, call methods on the new class
#  I.e. xnewa.AreYouThere()
#       xnewa.ChannelList('admin', 'password')
######################################################################################################
DEBUG = True
# Core defines
NEWA_XMLINFO_PATH = "/public/services/InfoXML.aspx"

FANART_PATH = 'fanart'
CHANNEL_PATH = 'Channels'
SHOW_PATH = 'Shows'
GENRE_PATH = 'Genres'

Last_Error = ""
# For WS Search functions, sort and filters....
# Sort fields

import time
from datetime import timedelta, datetime
import dateutil.parser
import tempfile
import os.path
import pickle as pickle
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from kodi_six.utils import py2_encode, py2_decode
import sys
from fix_utf8 import smartUTF8
from XNEWAGlobals import *
import http.client

if sys.version_info[0] >=  3:
    pseudovfs = xbmcvfs
else:
    pseudovfs = xbmc

if sys.version_info >=  (2, 7):
    import json as _json
else:
    try:
        import simplejson as _json
    except:
        import json as _json

try:
    from urllib.parse import urlparse, quote, unquote
    from urllib.request import urlopen, Request, urlretrieve
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError, URLError
    from urlparse import urlparse
    from urllib import quote, unquote, urlretrieve


__language__ = xbmcaddon.Addon().getLocalizedString
DATAROOT = pseudovfs.translatePath( 'special://profile/addon_data/%s' % xbmcaddon.Addon().getAddonInfo('id') )
CACHEROOT = os.path.join(pseudovfs.translatePath('special://temp'), 'knew5')

class XNEWA_Connect(object):

    SCHEDULE_ONCE = 'Single'

    # Instantiation
    def __init__(self, *args, **kwargs):
        self.settings = kwargs['settings']
        self.port = self.settings.NextPVR_PORT
        self.ip = unquote(self.settings.NextPVR_HOST)
        import re
        m = re.search(r'(^127\.)|(^10\.)|(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|(^192\.168\.)', self.ip )
        if m == None:
            m = re.search(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', self.ip )
            if m != None:
                xbmc.log ('Using Internet IPv4 restrictions on non-local IP')
                self.LOCAL_NEWA = False
                self.NextPVR_USEWOL = False
            else:
                try:
                    from socket import getaddrinfo
                    temp = getaddrinfo(self.ip, self.port)
                    ipv6 = temp[0][4][0]
                    m = re.search(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', ipv6 )
                    if m != None:
                        #IPv4
                        m = re.search(r'(^127\.)|(^10\.)|(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|(^192\.168\.)', ipv6 )
                        if m == None:
                            xbmc.log ('Using Internet IPv4 restrictions')
                            self.LOCAL_NEWA = False
                            self.NextPVR_USEWOL = False
                    else:
                        if ipv6 == self.ip:
                            self.ip = '[' + self.ip + ']'
                        xbmc.log (self.ip)
                        if ipv6.startswith ('fd') or ipv6.startswith ('fe80') or ipv6.replace(':','') == '1':
                            xbmc.log ('Local IPv6')
                        else:
                            xbmc.log ('Using Internet IPv6 restrictions')
                            self.LOCAL_NEWA = False
                            self.NextPVR_USEWOL = False
                    #self.ip = temp
                except:
                    self.offline = True
                    debug("Error instantiating (cannot resolve host-name)")
                    raise Exception("cannot resolve host-name.")

        self.vlc_url = None
        self.vlc_process = -1
        self.miniEPG = datetime.max
        self.interface = self.settings.XNEWA_INTERFACE
        self.channels = None
        self.update_time = 9223372036854775807
        self.isdst = time.localtime(time.time()).tm_isdst
        self.PVRRecordings = {}
        self.keycodes = {}

        if self.isdst == 1:
            xbmc.log ('atz ' + str(time.altzone))
            self.my_offset = timedelta(seconds=time.altzone)
        else:
            xbmc.log ('tz ' + str(time.timezone))
            self.my_offset = timedelta(seconds=time.timezone)

        if 'offline' in kwargs:
            self.offline = kwargs['offline']
        else:
            self.offline = False
        self.changedRecordings = False
        if not os.path.exists(CACHEROOT):
            os.makedirs(CACHEROOT)

        self.getfilesystemencoding = sys.getfilesystemencoding()
        if self.getfilesystemencoding is None:
            self.getfilesystemencoding = 'utf-8'
        xbmc.log (self.getfilesystemencoding)
        if  time.localtime(time.time()).tm_isdst != 0:
            self.dst_offset = timedelta(seconds=time.timezone) - timedelta(seconds=time.altzone)
            xbmc.log ('DST on')
        else:
            self.dst_offset = timedelta(0)
            xbmc.log ('DST off')


        self.defaultSchedule = None
        self.methodTranscode = None
        self.sid = None
        self.client = None
        self.strClient = None
        self.mycache = CACHEROOT

    ######################################################################################################
    # checking to see if NEWA is responding
    ######################################################################################################
        self.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST)

        if self.sid == None:
            self.sidLogin()
            if self.sid == None:
                self.offline = True

    ######################################################################################################
    # Setting up fanart defaults
    ######################################################################################################
        if self.settings.XNEWA_CACHE_PERM == True:
            self.channelPath = os.path.join( DATAROOT, FANART_PATH, CHANNEL_PATH)
            self.showPath = os.path.join( DATAROOT, FANART_PATH, SHOW_PATH)
            self.genrePath = os.path.join( DATAROOT, FANART_PATH, GENRE_PATH)
        else:
            self.channelPath = os.path.join( WHERE_AM_I, FANART_PATH, CHANNEL_PATH)
            self.showPath = os.path.join( WHERE_AM_I, FANART_PATH, SHOW_PATH)
            self.genrePath = os.path.join( WHERE_AM_I, FANART_PATH, GENRE_PATH)

        self.cached_channelPath = os.path.join( CACHEROOT, FANART_PATH, CHANNEL_PATH)
        self.cached_showPath = os.path.join( CACHEROOT, FANART_PATH, SHOW_PATH)
        self.cached_genrePath = os.path.join( CACHEROOT, FANART_PATH, GENRE_PATH)
        for folder in (self.channelPath, self.showPath, self.genrePath, self.cached_channelPath, self.cached_showPath, self.cached_genrePath):
            if not xbmcvfs.exists( folder ):
                xbmcvfs.mkdirs( folder )
        self.Last_Error = None

    #Core Functions

    ######################################################################################################
    # Checking to see if the NextPVR server is awake...
    ######################################################################################################
    def AreYouThere(self, usewol=False, mac=None, broadcast=None, _retry=0):
        import socket
        # check if computer is on
        #debug( "--> AreYouThere() socket on port " + str(self.port) + " using ip=" + str(self.ip))
        #debug( "                  mac:" + str(mac) + "broadcast: " + str(broadcast))
        #debug( "This got: " + str(usewol) + " / " + mac)
        ret = False
        if self.settings.LOCAL_NEWA == True:
            res = socket.getaddrinfo(self.ip, self.port)
            af, socktype, proto, canonname,sa  = res[0]
            for count in range (_retry, int(self.settings.NextPVR_CONTACTS)):
                try:
                    # try and connect to host on supplied port
                    s = socket.socket(af, socktype, proto)
                    s.settimeout ( 0.750 )
                    s.connect ( (self.ip, int(self.port ) ) )
                    s.close()
                    ret = True
                    break
                except:
                    if self.ip == '127.0.0.1':
                        zeroConf(self)
                    elif usewol and mac != None:
                        if count == 0:
                            WolProgress = xbmcgui.DialogProgress()
                            WolProgress.create("%s WOL" % smartUTF8(__language__(30152)), '%s %s %s' % (smartUTF8(__language__(30153)), self.ip, smartUTF8(__language__(30139))))
                        completed = 100 * count // int(self.settings.NextPVR_CONTACTS)
                        WolProgress.update(completed)
                        xbmc.log ('sending wol ' + mac + ' ' + str(count))
                        #xbmc.executebuiltin('WakeOnLan('+ mac + ')')
                        _WakeOnLan(mac,broadcast)
                        xbmc.sleep(5000)
                        if WolProgress.iscanceled():
                            WolProgress.close()
                            break

                    else:
                        break
            self.offline = not ret
        if self.sid == None:
            self.sidLogin()
            self.getRecordingUpdate()

        ret = not self.sid == None

        debug("AreYouThere() returns: " + str(ret))
        return ret

#################################################################################################################
    def getURL(self):
        address = "http://" + self.ip + ":" + str(self.port)
        return address

#################################################################################################################
    def getVlcURL(self):
        return self.vlc_url

#################################################################################################################
    def getPVRChannels(self):
        from nextpvr.XBMCJSON import XBMCJSON
        myJSON = XBMCJSON()
        param = {}
        param['channelgroupid'] = 'alltv'
        param['properties'] = [ "channel" ]
        #param['limits'] = { 'end' : 500, 'start' : 0  }
        response = myJSON.PVR.GetChannels(param)
        if 'result' in response:
            channels = [x['channel'] for x in response['result']['channels']]
        else:
             channels = None
        return channels

#################################################################################################################
    def GetPVRRecordings(self):
        self.PVRRecordings = {}
        from nextpvr.XBMCJSON import XBMCJSON
        myJSON = XBMCJSON()
        param = {}
        param['properties'] = [ 'file' ]
        param['limits'] = {'start': 0}
        response = myJSON.PVR.GetRecordings(param)
        if 'result' in response:
            for recording in response['result']['recordings']:
                m = re.search('.+ (.+?).pvr', recording['file'])
                if m != None:
                    self.PVRRecordings[m.group(1)] = recording['file']
        xbmc.log('Number of recordings: {}'.format(len(self.PVRRecordings)))

#################################################################################################################
    def GetPVRRecording(self, recid):
        pvr = self.PVRRecordings.get(recid)
        if pvr == None:
            self.GetPVRRecordings()
            pvr = self.PVRRecordings.get(recid)
        return pvr

######################################################################################################
# Starting streaming by vlc schedule oid
######################################################################################################
    def startVlcFileByScheduleOID(self, userid, password, scheduleOID):

        bitrate = ['128', '256', '512', 'LAN', 'HD-2K', 'HD-4K', 'HD-8K' ]
        size = [320,480, 720]

        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/StreamByScheduleOID/' + str(scheduleOID) + self.jsid  + '&strmVideoSize=' + str(size.index(self.settings.VLC_VIDEO_SIZE)) + '&strmBitRate=' + str(bitrate.index(self.settings.VLC_VIDEO_BITRATE)) + '&strmAudioBitrate=' + str(self.settings.VLC_AUDIO_BITRATE)
        xbmc.log(url)
        json_file = urlopen(url)
        JSONVlcObject = _json.load(json_file)
        json_file.close()

        if JSONVlcObject['JSONVlcObject']['rtn']['Error'] == False:
            vlcObject = JSONVlcObject['JSONVlcObject']['VLC_Obj']
            self.vlc_url = vlcObject['StreamLocation']
            self.vlc_process = vlcObject['ProcessId']
            return True
        else:
            return False



######################################################################################################
# Starting streaming by vlc event oid
######################################################################################################
    def startVlcFileByEPGEventOID(self, userid, password, eventOID):

        bitrate = ['128', '256', '512', 'LAN', 'HD-2K', 'HD-4K', 'HD-8K' ]
        size = [320,480, 720]
        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/StreamByEPGOID/' + str(eventOID) + self.jsid  + '&strmVideoSize=' + str(size.index(self.settings.VLC_VIDEO_SIZE)) + '&strmBitRate=' + str(bitrate.index(self.settings.VLC_VIDEO_BITRATE)) + '&strmAudioBitrate=' + str(self.settings.VLC_AUDIO_BITRATE)

        xbmc.log(url)

        json_file = urlopen(url)
        JSONVlcObject = _json.load(json_file)
        json_file.close()

        if JSONVlcObject['JSONVlcObject']['rtn']['Error'] == False:
            vlcObject = JSONVlcObject['JSONVlcObject']['VLC_Obj']
            self.vlc_url = vlcObject['StreamLocation']
            self.vlc_process = vlcObject['ProcessId']
            return True
        else:
            return False

######################################################################################################
# Starting streaming by vlc
######################################################################################################
    def startVlcLiveStreamByChannelNumberObject(self, userid, password, channelNum):

        bitrate = ['128', '256', '512', 'LAN', 'HD-2K', 'HD-4K', 'HD-8K' ]
        size = [320,480, 720]
        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/Dump/StreamByChannel/Number/' + str(channelNum) + self.jsid
        xbmc.log(url)

        json_file = urlopen(url)
        JSONVlcObject = _json.load(json_file)
        json_file.close()

        if JSONVlcObject['JSONVlcObject']['rtn']['Error'] == False:
            vlcObject = JSONVlcObject['JSONVlcObject']['VLC_Obj']
            self.vlc_url = vlcObject['StreamLocation']
            self.vlc_process = vlcObject['ProcessId']
            return True
        else:
            return False



######################################################################################################
# Stop streaming by vlc
######################################################################################################
    def stopVlcStreamProcess(self, userid, password):

        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/KillVLC/' + str(self.vlc_process) + self.jsid
        xbmc.log(url)
        json_file = urlopen(url)
        JSONVlcObject = _json.load(json_file)
        json_file.close()
        self.vlc_process = -1
        return True


######################################################################################################
# Send vlc heartbeat
######################################################################################################
    def sendVlcHeartbeat(self, userid, password):
        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/sendHeartBeat/' + str(self.vlc_process)
        xbmc.log(url)
        json_file = urlopen(url)
        json_file.close()
        return True


######################################################################################################
# transcoding
######################################################################################################

    def startTranscodeLiveStreamByChannelNumber(self, channelNum):
        self.methodTranscode = 'channel'
        self.getTranscodeStatus()
        url = "http://" + self.ip + ":" + str(self.port) + '/services/service?method=channel.transcode.initiate&format=json&profile=' + self.settings.TRANSCODE_PROFILE + '&channel=' + str(channelNum) + '&sid=' + self.sid
        xbmc.log(url)
        try:
            xml_file = urlopen(url)
            xml_return = xml_file.read()
            if 'stat="ok"' not in xml_return:
                xbmc.log(xml_return)
        except Exception as err:
            xbmc.log(str(err))

    def startTranscodeRecording(self, recording_oid):
        self.methodTranscode = 'recording'
        self.getTranscodeStatus()
        url = "http://" + self.ip + ":" + str(self.port) + '/services/service?method=recording.transcode.initiate&profile=' + self.settings.TRANSCODE_PROFILE + '&recording_id=' + str(recording_oid) + '&sid=' + self.sid
        xbmc.log(url)
        try:
            xml_file = urlopen(url)
            xml_return = xml_file.read()
            if 'stat="ok"' not in xml_return:
                xbmc.log(xml_return)
        except Exception as err:
            xbmc.log(str(err))


    def sendTranscodeHeartbeat(self):
        url = "http://" + self.ip + ":" + str(self.port) + '/services/service?method=' + self.methodTranscode + '.transcode.lease&sid=' + self.sid
        xbmc.log(url)
        try:
            request = Request(url)
            xml_file = urlopen(request, timeout=4)
            xml_return = xml_file.read()
            if 'stat="ok"' not in xml_return:
                xbmc.Player.stop()
                xbmc.log(xml_return)
        except Exception as err:
            xbmc.log(str(err))


    def sendTranscodeStop(self):
        url = "http://" + self.ip + ":" + str(self.port) + '/services/service?method=' + self.methodTranscode + '.transcode.stop&sid=' + self.sid
        xbmc.log(url)
        try:
            xml_file = urlopen(url)
            xml_return = xml_file.read()
            if 'stat="ok"' not in xml_return:
                xbmc.log(xml_return)
        except Exception as err:
            xbmc.log(str(err))


    def getTranscodeStatus(self):
        url = "http://" + self.ip + ":" + str(self.port) + '/services/service?method=' + self.methodTranscode + '.transcode.status&format=json&sid=' + self.sid
        xbmc.log(url)
        retval = 0
        try:
            request = Request(url)
            json_file = urlopen(request,timeout=.25)
            JSONTranscodeObject = _json.load(json_file)
            json_file.close()
            if  'percentage' in JSONTranscodeObject:
                retval = JSONTranscodeObject['percentage']
            else:
                print(JSONTranscodeObject)
        except Exception as err:
            xbmc.log(str(err))
        xbmc.log(str(retval))
        return retval





######################################################################################################
# Retrieving XMLInfo information and returning in dictionary
######################################################################################################
    def GetNextPVRInfo(self, userid, password,channels=True):
        dic = {}
        if self.settings.XNEWA_WEBCLIENT != True:
            if self.settings.XNEWA_INTERFACE == 'JSON':
                #v5 change
                from xml.dom import minidom
                xbmc.log('XML info')
                address = "http://" + self.ip + ":" + str(self.port) + NEWA_XMLINFO_PATH
                xbmc.log(address)
                website = urlopen(address)
                website_html = website.read()

                dom = minidom.parseString(website_html)
                #dom = None
                if dom != None:
                    ret = self._getdictfromdom(dom, "Directory")
                    dic['directory'] = ret
                    ret = self._getdictfromdom(dom, "Schedule")
                    for dict in ret:
                        dic['schedule'] = dict
                    ret = self._getdictfromdom(dom, "Tuner")
                    dic['tuner'] = ret
                    ret = self._getdictfromdom(dom, "Epg")
                    for dict in ret:
                        dic['epg'] = dict
                    ret = self._getdictfromdom(dom, "Log")
                    for dict in ret:
                        dic['log'] = dict
            else:
                dic = GetNextPVRInfo_v5 (self)
        else:
            self.channels = self.getChannelList()

        if channels == True:
            # We also get, and cache, the channel data
            self.channels = self.getChannelList()
            self.channelGroups = self.getChannelGroupList(userid, password)
            self.setChannelGroups()
            self.RecDirs = self.getRecDirList(userid, password)
            self.genresColours = self.getEPGGenres(userid, password)
        return dic

######################################################################################################
# Retrieving last update time 3.4.x
######################################################################################################
    def getRecordingUpdate(self):
        url  = "http://" + self.ip + ":" + str(self.port) + '/service?method=recording.lastupdated&sid=' + self.sid
        xbmc.log(url)
        try:
            import xml.etree.ElementTree as ET
            request = Request(url, headers={"Accept" : "application/xml"})
            u = urlopen(request, timeout=10)
            tree = ET.parse(u)
            root = tree.getroot()
            if root.attrib['stat'] == 'ok':
                self.update_time =  int(root.find('last_update').text)
                xbmc.log(datetime.fromtimestamp(self.update_time).strftime('%Y-%m-%d %H:%M:%S'))
            elif root.attrib['stat'] == 'fail':
                err = root.find('err')
                if err.attrib['code'] == '8':
                    xbmc.log(err.attrib['msg'])
                    self.sid = None
                    self.sidLogin()
        except Exception as err:
            xbmc.log(str(err))
        return self.update_time

    def checkCache(self,cached):
        if os.path.isfile(os.path.join(self.mycache,cached)) == True:
            if not cached.endswith('sid.p'):
                if self.offline == True:
                    return True
                if self.update_time != 9223372036854775807:
                    update_time = self.update_time
                    self.getRecordingUpdate()
                    if update_time == self.update_time:
                        if self.update_time <= int(os.path.getmtime(os.path.join(self.mycache,cached))):
                            return True
                    return False

            ft =  datetime.fromtimestamp(os.path.getmtime(os.path.join(self.mycache,cached)))
            if ft + timedelta(hours=2) > datetime.now():
                return True

        return False

    def cleanCache(self,spec):
        import glob
        xbmc.log("clean cache for " + spec)
        fileNames = glob.glob(os.path.join(self.mycache,spec))
        for file in fileNames:
            os.remove(file)
        return True

    def cleanCoverCache(self):
        import glob
        xbmc.log("clean covers")
        fileNames = glob.glob(os.path.join(self.cached_showPath,'*.jpg'))
        for file in fileNames:
            os.remove(file)
        return True

    def cleanOldCache(self,spec):
        if self.offline == True:
            return True
        import glob
        import os
        xbmc.log("clean old files for " + spec)
        cnt = 0
        fileNames = glob.glob(os.path.join(self.mycache,spec))
        for file in fileNames:
            ft =  datetime.fromtimestamp(os.path.getmtime(file))
            if ft + timedelta(hours=2) < datetime.now():
                os.remove(file)
            else:
                cnt = cnt + 1
        return cnt

    def myCachedPickle(self,pObject,cached):
        pickle.dump(pObject, open(os.path.join(self.mycache,cached),'wb'),pickle.HIGHEST_PROTOCOL)

    def myCachedPickleLoad(self,cached):
        return pickle.load(open(os.path.join(self.mycache,cached),'rb'))

######################################################################################################
# Retrieves a summary List
######################################################################################################
    def getRecordingsSummary(self, userid, password, sortTitle, sortDate, recDir):

        cached = 'summary.List'
        if self.checkCache(cached):
            retArr = self.myCachedPickleLoad(cached)
            return retArr

        if self.settings.XNEWA_INTERFACE == 'JSON':
            if sortTitle:
                sortDate = True

            xbmc.log("getRecordingsSummary json start")

            try:

                if self.defaultSchedule == None:
                    self.getDefaultSchedule()

                import copy
                recObj = copy.deepcopy(self.defaultSchedule)
                if self.settings.XNEWA_COLOURS != None:
                    if 'red' in self.settings.XNEWA_COLOURS :
                        recObj['recColorRed'] = True
                    else:
                        recObj['recColorRed'] = False
                    if 'green' in self.settings.XNEWA_COLOURS :
                        recObj['recColorGreen'] = True
                    else:
                        recObj['recColorGreen'] = False
                    if 'yellow' in self.settings.XNEWA_COLOURS :
                        recObj['recColorYellow'] = True
                    else:
                        recObj['recColorYellow'] = False
                    if 'blue' in self.settings.XNEWA_COLOURS :
                        recObj['recColorBlue'] = True
                    else:
                        recObj['recColorBlue'] = False

                if recDir != None:
                    recObj['recDir'] = recDir

                option = ''
                if sortTitle:
                    option = option + '&sortByName=true'
                if sortDate:
                    option = option + '&sortAscending=true'
                url = "http://" + self.ip + ":" + str(self.port) + '/public/ScheduleService/RecordingsSummary' + self.jsid + option
                xbmc.log(url)
                recObj = _json.dumps(recObj)
                xbmc.log(recObj)
                request = Request(url, recObj.encode('utf-8'))
                request.add_header('Content-Type', 'application/json')
                try:
                    response = urlopen(request)
                    xbmc.log("response from request was %d" % response.code)
                    results = response.read()
                    summaryResults = _json.loads(results)
                    retArr = []
                    for summary in summaryResults['RecordingsSummary']['summaryArray']:
                        retArr.append(self._sum2dict_json(summary))
                except URLError as e:
                    xbmc.log('error during request: %s' % e.code)
                    if e.code == 405:
                        return None
            except Exception as err:
                xbmc.log(str(err))
            xbmc.log("getRecordingsSummary json end")
        else:
            retArr = getRecordingsSummary_v5(self, sortTitle, sortDate)

        self.myCachedPickle(retArr,cached)
        return retArr

######################################################################################################
# Translating a (json) recordingobject into a dictionary object...
######################################################################################################
    def _sum2dict_json(self, summary):
        theDict = {}
        #todo fix suds processing
        if summary  is not None:
            theDict['title'] = py2_decode(summary['Name'])
            theDict['start'] =  dateutil.parser.parse(summary['StartTime']).astimezone(dateutil.tz.tzlocal())
            theDict['count'] = summary['Count']
        return theDict

######################################################################################################
# Retrieves a list of channels...
######################################################################################################
    def getChannelList(self):
        cached = 'channel.List'
        if self.checkCache(cached):
            dic = self.myCachedPickleLoad(cached)
            if '0' in dic:
                xbmc.log("getChannelList cached end")
                return dic

        if self.settings.XNEWA_INTERFACE == 'JSON':
            dic = self.getChannelList_json()
        else:
            dic = getChannelList_v5(self)

        if dic != None:
            self.myCachedPickle(dic,cached)
        return dic

    def getChannelList_json(self):

        xbmc.log("getChannelList JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/GuideService/Channels' + self.jsid
        dic = {}
        import imghdr
        import glob
        dic['0']= (u"Unknown",'0')
        myDlg = None
        try:
            channelList = self.nextJson(url)
            cnt = 0
            for channel in channelList['channelsJSONObject']['Channels']:
                chan = channel['channel']
                if chan['channelIcon'] != '':
                    cnt= cnt+1
            if cnt > 0 and self.settings.NextPVR_STREAM != 'PVR':
                icons = glob.glob(os.path.join(self.cached_channelPath,'*.*'))
                if cnt > len(icons) + 20:
                    myDlg = xbmcgui.DialogProgress()
                    myDlg.create(smartUTF8(__language__(30154)), smartUTF8(__language__(30139)))
                cnt = 0
            for channel in channelList['channelsJSONObject']['Channels']:
                chan = channel['channel']
                if myDlg != None:
                    completed = 100 * cnt//len(channelList['channelsJSONObject']['Channels'])
                    cnt = cnt + 1
                    myDlg.update(completed, py2_decode(chan['channelName']))
                if 'channelNumber' in chan:
                    dic[chan['channelOID']] = ( py2_decode(chan['channelName']),str(chan['channelNumber']),str(chan['channelMinor']) )
                elif 'channelMinor' in chan:
                    dic[str(chan['channelOID'])] = ( py2_decode(chan['channelName']),str(chan['channelNum']),str(chan['channelMinor']) )
                else:
                    dic[str(chan['channelOID'])] = ( py2_decode(chan['channelName']),str(chan['channelNum']),'0' )
                if chan['channelIcon'] != '':
                    try:
                        import string
                        valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
                        safename = ''.join(ch for ch in chan['channelName'] if ch in valid_chars)
                        output = os.path.join(self.channelPath,safename+".*")
                        icon = glob.glob(output)
                        if not icon:
                            url = self.getURL()+'/'+chan['channelIcon']
                            output = os.path.join(self.channelPath,"unknown")
                            urlretrieve (url,output)
                            img = imghdr.what(os.path.join(self.channelPath,"unknown"))
                            if img == "png":
                                os.rename(os.path.join(self.channelPath,"unknown"), os.path.join(self.channelPath,py2_decode(safename)+".png"))
                            elif img == "jpeg":
                                os.rename(os.path.join(self.channelPath,"unknown"), os.path.join(self.channelPath,safename.encode('utf-8')+".jpg"))
                            elif img is None:
                                xbmc.log(py2_decode(safename) + " is unknown")
                            else:
                                xbmc.log(py2_decode(safename) + " Type " + img)
                        else:
                            pass
                    except:
                        xbmc.log(str(chan['channelNum']) + " Error")
                        pass
                else:
                    xbmc.log(str(channel))
        except Exception as err:
            xbmc.log('getChannelList JSON error')
            print (err)
            dic = None
        xbmc.log("getChannelList JSON end")
        if myDlg != None:
            myDlg.close()
        return dic

######################################################################################################
# Sets the librar playback position
######################################################################################################

    def setLibraryPlaybackPosition(self,filename, position, duration):

        xbmc.log("setLibraryPlaybackPosition start")

        if int(duration) < 0:
            return True

        if int(duration) == 0 and int(position) != 0:
            duration = position + 30

        import re
        m = re.search('^.+\.(?i)(mpeg|mpg|m2v|avi|ty|avs|ogm|mp4|mov|m2ts|wmv|cdg|iso|rm|dvr-ms|ts|mkv|vob|divx|flv|ratDVD|m4v|3gp|rmvb|wtv|bdmv)$', filename)
        if m == None:
            xbmc.log("Not a video file")
            return True
        import os
        url = "http://" + self.ip + ":" + str(self.port) + '/public/detailsservice/set/PlaybackPosition' + self.jsid  + '&fname=' + quote(os.path.basename(filename),'\\/:%.?=;')  + '&dur=' + str(int(duration)) +'&pos=' +str(int(position))
        xbmc.log(url)
        try:
            json_file = urlopen(url)
            jsonPlaybackPosition = _json.load(json_file)
            json_file.close()
            xbmc.log(str(jsonPlaybackPosition))
            if 'url' in jsonPlaybackPosition:
                jsonPlaybackPosition['l']
            return True
        except Exception as err:
            xbmc.log(str(err))
            return False


######################################################################################################
# Sets the playback position
######################################################################################################
    def setPlaybackPositionObject(self, userid, password, rec, position, duration):

        if self.settings.XNEWA_INTERFACE == 'JSON':
            return self.setLibraryPlaybackPosition(rec["filename"], int(position),int(duration))
        else:
            return setLastPlayedPosition(self,rec["recording_oid"], int(position))

######################################################################################################
# Retrieves a list of channelGroups...
######################################################################################################
    def getChannelGroupList(self, userid, password):

        if self.settings.XNEWA_INTERFACE == 'JSON':
            dic = self.getChannelGroupList_json()
            if dic != None:
                return dic
        return getChannelGroupList_v5(self)


    def getChannelGroupList_json(self):

        xbmc.log("getChannelGroupList JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/GuideService/ChannelGroups' + self.jsid
        groups = []
        groups.append('All Channels')

        try:
            json_file = urlopen(url)
            epgGenres = _json.load(json_file)
            json_file.close()
            for group in epgGenres['channelGroupJSONObject']['ChannelGroups']:
                if group != 'All Channels':
                    groups.append(group.encode('utf-8'))
        except:
            xbmc.log('getChannelGroupList JSON error')
            groups = None
        xbmc.log("getChannelGroupList JSON end")
        return groups

    def setChannelGroups(self):
        import xml.etree.ElementTree as ET

        settings_file = os.path.join(WHERE_AM_I, 'resources' ,'settings.xml')
        tree = ET.parse(settings_file)
        root = tree.getroot()
        values = None
        try :
            for setting in root.findall("category/setting[@id='group']"):
                values = setting.attrib['values']
                break
        except:
            for setting in root.findall('.//setting'):
                if 'id' in setting.attrib:
                    if setting.attrib['id'] == 'group':
                        values =  setting.attrib['values']
                        break

        if values != None:
            groups = '|'.join(self.channelGroups)
            if values != groups:
                setting.set('values',groups)
                tree.write(settings_file)

######################################################################################################
# Retrieves a list of genres...
######################################################################################################
    def getEPGGenres(self, userid, password):

        if self.settings.XNEWA_INTERFACE == 'JSON':
            dic = self.getEPGGenres_json()
            if dic != None:
                return dic
        return getEPGGenres_v5(self)


    def getEPGGenres_json(self):

        xbmc.log("getEPGGenres JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/GuideService/Genres' + self.jsid

        dic = {}
        dic['xnewa'] = 0
        try:
            json_file = urlopen(url)
            epgGenres = _json.load(json_file)
            json_file.close()
            for genre in epgGenres['genreJSONObject']['genres']:
                try:
                    if int(genre['genre']['color'],16) !=0:
                        dic[genre['genre']['name']] = int(genre['genre']['color'],16)
                except:
                    pass
        except:
            xbmc.log('EPG Genres JSON error')
            dic = None
        xbmc.log("getEPG Genres JSON end")
        return dic

######################################################################################################
# Retrieves a list of recDir...
######################################################################################################
    def getRecDirList(self, userid, password):

        if self.settings.XNEWA_INTERFACE == 'JSON':
            return self.getRecDirList_json()

        return getRecDirList_v5(self)

    def getRecDirList_json(self):

        xbmc.log("getRecDirList JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ScheduleService/Get/RecDirs' + self.jsid
        xbmc.log(url)
        dirs = {}
        try:
            json_file = urlopen(url)
            allDirs = _json.load(json_file)
            json_file.close()
            dirs[allDirs['DefRecDir']['RecDirName']] = allDirs['DefRecDir']['RecDir']
            for dir in allDirs['dirArray']:
                if dir['RecDirName'] != 'Default':
                    try:
                        dirs[dir['RecDirName'].encode('utf-8')] = dir['RecDir']
                    except:
                        xbmc.log('Duplicate of ' + dir['RecDirName'].encode('utf-8'))
        except Exception as err:
            xbmc.log('getRecDirList JSON error')
            print(err)
            dirs = None
        xbmc.log("getRecDirList JSON end")
        return dirs

######################################################################################################
    def getDetails(self, userid, password, oid, type, fetchArt, passedData=None):

        xbmc.log('Details ' + type)
        if self.channels == None:
            self.channels = self.getChannelList()
        if self.settings.XNEWA_INTERFACE == 'JSON':
            if type=="E" or type=='P':
                url = "http://" + self.ip + ":" + str(self.port) + '/public/DetailsService/' + str(oid) + self.jsid
                xbmc.log(url)
                json_file = urlopen(url)
                detailsService = _json.load(json_file)
                json_file.close()
                return self._detail2array_json(detailsService,fetchArt)
            elif type=="R":
                url = "http://" + self.ip + ":" + str(self.port) + '/public/DetailsSchdService/' + str(oid) + self.jsid
                xbmc.log(url)
                json_file = urlopen(url)
                #json_file = open('c:/temp/36525000.json')
                detailsService = _json.load(json_file)
                json_file.close()
                return self._detail2array_json(detailsService,fetchArt)
            elif type=="F":
                url = "http://" + self.ip + ":" + str(self.port) + '/public/DetailsRecurrService/' + str(oid) + self.jsid
                xbmc.log(url)
                json_file = urlopen(url)
                #json_file = open('c:/temp/36525000.json')
                detailsService = _json.load(json_file)
                json_file.close()
                return self._recurr2dict(detailsService['epgEventJSONObject'])

        if type=="E" or type=='P':
            return epgTag2dict_v5(self,passedData)
        elif type=="R":
            return getRecording_v5(self,oid)
        elif type=="F":
            return getRecurringRecord(self,oid)

######################################################################################################
    def archiveRecording(self, userid, password, oid, directory):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            return self.archiveRecording_json(oid,directory)


    def archiveRecording_json(self, oid, directory):

        xbmc.log("archiveRecording JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/ArchiveRecording/' + str(oid) + self.jsid  + '&recdir=' + quote_plus(directory)
        xbmc.log(url)
        try:
            json_file = urlopen(url)
        except URLError as e:
                xbmc.log('archiveRecording  JSON error')
                return False
        else:
            archive = _json.load(json_file)
            json_file.close()
            xbmc.log(archive)
        xbmc.log("archiveRecording JSON end")
        return True

######################################################################################################
    def getGuideInfo(self, userid, password, dtTimeStart, dtTimeEnd, group):

        xbmc.log("getGuideInfo start ")
        timeStart = dtTimeStart.strftime("%Y-%m-%dT%H:%M:00")
        timeEnd = dtTimeEnd.strftime("%Y-%m-%dT%H:%M:00")
        cachedCount = self.cleanOldCache('guideListing-*.p')
        if group == None or  group == 'All Channels':
            group = ''
        if cachedCount > 0:
            cached = 'guideListing-' + dtTimeStart.strftime("%Y-%m-%dT%H") + group + '.p'
            if self.checkCache(cached):
                retArr = self.myCachedPickleLoad(cached)
                xbmc.log("getGuideInfo cached end")
                return retArr
            lastHour = dtTimeStart - timedelta(hours=1)
            cached = 'guideListing-' + lastHour.strftime("%Y-%m-%dT%H")  + group + '.p'
            if self.checkCache(cached):
                retArr = self.myCachedPickleLoad(cached)
                xbmc.log("getGuideInfo cached last hour end")
                return retArr

        if group != '':
            if group not in self.channelGroups:
                xbmc.log(group + " group not found")
                caseGroup = ''
                for groups in self.channelGroups:
                    if groups.lower() == group.lower():
                        xbmc.log(groups + " group found")
                        caseGroup = groups
                group = caseGroup
            elif group == 'All' or group == 'All Channels':
                group = ''

        cached = 'guideListing-' + dtTimeStart.strftime("%Y-%m-%dT%H") + group + '.p'

        if self.settings.XNEWA_INTERFACE != 'JSON' or self.settings.XNEWA_WEBCLIENT == True:
            import calendar
            if self.settings.XNEWA_INTERFACE == 'XML' or  self.settings.XNEWA_INTERFACE == 'Version5':
                start = '&start=' + str(int(calendar.timegm(dtTimeStart.timetuple()))) + '&end=' + str(int(calendar.timegm(dtTimeEnd.timetuple())))
            else:
                start = None
            xbmc.log(start)
            #retGuide = self._progs2array_xml(url)
            if group == '':
                retGuide = getGuideInfo_v5(self,start)
            else:
                retGuide = getGroupGuideInfo_v5(self,start,group)

        elif self.settings.XNEWA_INTERFACE == 'JSON':
            import calendar
            #url = "http://" + self.ip + ":" + str(self.port) + '/public/guideservice/listing?stime=' + dtTimeStart.strftime("%Y-%m-%dT%H:%M") + '&etime=' + dtTimeEnd.strftime("%Y-%m-%dT%H:%M")
            url = "http://" + self.ip + ":" + str(self.port) + '/public/guideservice/listing' + self.jsid + '&stime=' + str(int(calendar.timegm(dtTimeStart.timetuple()))) + '&etime=' + str(int(calendar.timegm(dtTimeEnd.timetuple()))-1)
            if group != None:
                url = url + '&chnlgroup=' + group.replace(' ','+')
            retGuide = self._progs2array_json(url)

        if retGuide != []:
            self.myCachedPickle(retGuide,cached)
        xbmc.log("getGuideInfo end")
        return retGuide

######################################################################################################
    def getUpcomingRecordings(self, userid, password, amount=0):

        cached = 'upcomingRecordings-' + str(amount) + '.p'
        if self.checkCache(cached):
          retArr = self.myCachedPickleLoad(cached)
          return retArr

        if self.settings.XNEWA_INTERFACE == 'JSON':
            retArr = self.getUpcomingRecordings_json(amount)
        else:
            retArr = getUpcomingRecordings_v5(self, amount)

        if ( retArr != None):
            self.myCachedPickle(retArr,cached)
        return retArr


    def getUpcomingRecordings_json(self, amount=0):

        xbmc.log("getUpcomingRecordings JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/Get/SortedFilteredList' + self.jsid
        xbmc.log(url)
        sortFilterObj = {}

        if amount == 0:
            amount = -1

        sortFilterObj['resultLimit'] = int(amount)

        # Figure out the sorting....
        sortFilterObj['datetimeSortSeq'] = 1
        sortFilterObj['channelSortSeq'] = 4
        sortFilterObj['titleSortSeq'] = 3
        sortFilterObj['statusSortSeq'] = 2
        sortFilterObj['datetimeDecending'] = False
        sortFilterObj['channelDecending'] = False
        sortFilterObj['titleDecending'] = False
        sortFilterObj['statusDecending'] = False

        # Then the filtering....
        sortFilterObj['All'] = False
        sortFilterObj['None'] = False
        sortFilterObj['Pending'] = True
        sortFilterObj['InProgress'] = True
        sortFilterObj['Completed'] = False
        sortFilterObj['Failed'] = False
        sortFilterObj['Conflict'] = False
        sortFilterObj['Recurring'] = False
        sortFilterObj['Deleted'] = False

        sortFilterObj['FilterByName'] = False
        sortFilterObj['NameFilter'] = ''
        sortFilterObj['NameFilterCaseSensitive'] = False

        retArr = []
        sortFilterObj = _json.dumps(sortFilterObj)
        try:
            request = Request(url, sortFilterObj.encode('utf-8'))
            request.add_header('content-type', 'application/json')
            response = urlopen(request)
            results = response.read()
            upcomingResults = _json.loads(results)
            for epgEvent in  upcomingResults['ManageResults']['EPGEvents']:
                theDict = self._rec2dict1_json(epgEvent)
                if theDict != None:
                    retArr.append(theDict)
        except Exception as err:
            print (str(err))
            retArr = None

        xbmc.log("getUpcomingRecordings JSON end")

        return retArr

######################################################################################################
    def getRecentRecordings(self, userid, password, amount=0, showName=None, sortTitle=True, sortDateDown=True ,recDir=None):
        if showName==None:
            cached = 'recentRecordings-' + str(amount) + '.p'
        else:
            import string
            valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
            filename = ''.join(ch for ch in showName if ch in valid_chars)
            cached = 'recentRecordings-' + filename + '.p'

        if self.checkCache(cached):
            retArr = self.myCachedPickleLoad(cached)
            return retArr
        if self.settings.XNEWA_INTERFACE == 'JSON':
            retArr = self.getRecentRecordings_json(amount, showName, sortTitle, sortDateDown, recDir)
        else:
        #v5
            retArr = getRecentRecordings_v5(self, amount, showName, sortTitle, sortDateDown, recDir)

        self.myCachedPickle(retArr,cached)
        return retArr



    def getRecentRecordings_json(self, amount=0, showName=None, sortTitle=True, sortDateDown=True, recDir=None):

        xbmc.log("getRecentRecordings JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/Get/SortedFilteredList' + self.jsid
        xbmc.log(url)
        sortFilterObj = {}

        if amount == 0:
            amount = -1
        sortFilterObj['resultLimit'] = int(amount)

        # Figure out the sorting....
        sortFilterObj['datetimeSortSeq'] = 1
        sortFilterObj['channelSortSeq'] = 4
        sortFilterObj['titleSortSeq'] = 3
        sortFilterObj['statusSortSeq'] = 2
        if sortDateDown:
            sortFilterObj['datetimeDecending'] = True
        else:
            sortFilterObj['datetimeDecending'] = False
        sortFilterObj['channelDecending'] = False
        if sortTitle:
            sortFilterObj['titleDecending'] = True
        else:
            sortFilterObj['titleDecending'] = False
        sortFilterObj['statusDecending'] = False

        # Then the filtering....
        sortFilterObj['All'] = False
        sortFilterObj['None'] = False
        sortFilterObj['Pending'] = False
        sortFilterObj['InProgress'] = True
        sortFilterObj['Completed'] = True
        sortFilterObj['Failed'] = True
        sortFilterObj['Conflict'] = False
        sortFilterObj['Recurring'] = False
        sortFilterObj['Deleted'] = True

        if showName == None:
            sortFilterObj['FilterByName'] = False
            sortFilterObj['NameFilter'] = ''
            sortFilterObj['NameFilterCaseSensitive'] = False
        else:
            sortFilterObj['FilterByName'] = True
            sortFilterObj['NameFilter'] = py2_decode(showName)
            sortFilterObj['NameFilterCaseSensitive'] = False

        retArr = []
        sortFilterObj = _json.dumps(sortFilterObj)
        try:
            request = Request(url, sortFilterObj.encode('utf-8'))
            request.add_header('Content-Type', 'application/json')
            response = urlopen(request)
            results = response.read()
            recentResults = _json.loads(results)
            for epgEvent in  recentResults['ManageResults']['EPGEvents']:
                theDict = self._rec2dict1_json(epgEvent, recDir)
                if theDict != None:
                    retArr.append(theDict)
        except Exception as err:
            print (err)
            retArr = None

        xbmc.log("getRecentRecordings JSON end")

        return retArr


######################################################################################################
    def getConflicts(self, userid, password, conflictRec):
        if self.settings.XNEWA_INTERFACE != 'SOAP':
            return self.getConflicts_json(userid, password, conflictRec)

    def getConflicts_json(self, userid, password, conflictRec):
        thePrograms =  self.getConflictedRecordings_json()
        #Now we get the attributes from the program
        start = conflictRec['start']
        end = conflictRec['end']

        retArr = []
        for prog in thePrograms:
            theDict = {}
            if prog['start'] <= end and prog['end'] >= start:
                if prog['schdConflicts'] != None:
                    for conflict in prog['schdConflicts']:
                        miniDetails = {}
                        miniDetails['title'] = conflict['Name']
                        miniDetails['rectype'] = conflict['Type']
                        miniDetails['status'] = conflict['Status']
                        miniDetails['recording_oid'] = conflict['OID']
                        miniDetails['start'] = self.jsonDate(conflict['StartTime'],self.dst_offset)
                        miniDetails['end'] = self.jsonDate(conflict['EndTime'],self.dst_offset)
                        retArr.append(miniDetails)
        return retArr

######################################################################################################
    def searchProgram(self, userid, password, needle, option):

        cached = 'search.List'
        if self.checkCache(cached):
            retArr = self.myCachedPickleLoad(cached)
            return retArr
        if needle == None:
            return None
        if self.settings.XNEWA_INTERFACE == 'JSON':
            retArr =  self.searchProgram_json(needle,option)
        else:
            retArr =  searchProgram_v5(self,quote(needle),option)
        if retArr:
            self.myCachedPickle(retArr,cached)

        return retArr




######################################################################################################
    def searchProgram_json(self, needle,option):

        xbmc.log("searchProgram JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/SearchService/Search' + self.jsid
        xbmc.log(url)
        searchObj = {}
        searchObj['searchName'] = needle
        searchObj['autoShowSearch'] = True
        searchObj['autoRecordSearch'] = False
        if option == 0 or option == 3:
            searchObj['searchTitle'] = True
            searchObj['searchSubTitle'] = True
        if option == 2 or option == 3:
            searchObj['searchCastCrew'] = True
        if option == 1 or option == 3:
            searchObj['searchDescription'] = True
        searchObj['matchTitle'] = False
        searchObj['matchSubTitle'] = False
        searchObj['matchDescription'] = False
        searchObj['startTitle'] = False
        searchObj['startSubTitle'] = False
        searchObj['startDescription'] = False
        searchObj['searchPhrase'] = needle
        searchObj['searchCaseSensitive'] = False
        searchObj = _json.dumps(searchObj)
        try:
            request = Request(url, searchObj.encode('utf-8'))
            request.add_header('Content-Type', 'application/json')
            response = urlopen(request)
            results = response.read()
            searchResults = _json.loads(results)
            retArr = []
            for prog in searchResults['SearchResults']['EPGEvents']:
                theDict = []
                theDict = self._rec2dict1_json(prog)
                if theDict != None:
                    retArr.append(theDict)


            xbmc.log( "searchProgram JSON end")
        except:
            retArr = None

        return retArr

######################################################################################################
    def getScheduledRecordings(self, userid, password):

        cached = 'scheduledRecordings.p'
        xbmc.log(cached)
        if self.checkCache(cached):
            retArr = self.myCachedPickleLoad(cached)
            return retArr

        if self.settings.XNEWA_INTERFACE == 'JSON':
            retArr = self.getScheduledRecordings_json()
        else:
            retArr = getScheduledRecordings_v5(self)

        if retArr:
            self.myCachedPickle(retArr,cached)

        return retArr


    def getScheduledRecordings_json(self):

        xbmc.log("getScheduledRecordings JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/Get/SortedFilteredList' + self.jsid
        xbmc.log(url)
        sortFilterObj = {}

        sortFilterObj['resultLimit'] = -1

        # Figure out the sorting....
        sortFilterObj['datetimeSortSeq'] = 0
        sortFilterObj['channelSortSeq'] = 0
        sortFilterObj['titleSortSeq'] = 0
        sortFilterObj['statusSortSeq'] = 0
        sortFilterObj['datetimeDecending'] = False
        sortFilterObj['channelDecending'] = False
        sortFilterObj['titleDecending'] = False
        sortFilterObj['statusDecending'] = False

        # Then the filtering....
        sortFilterObj['All'] = False
        sortFilterObj['None'] = False
        sortFilterObj['Pending'] = False
        sortFilterObj['InProgress'] = False
        sortFilterObj['Completed'] = False
        sortFilterObj['Failed'] = False
        sortFilterObj['Conflict'] = False
        sortFilterObj['Recurring'] = True
        sortFilterObj['Deleted'] = False

        sortFilterObj['FilterByName'] = False
        sortFilterObj['NameFilter'] = ''
        sortFilterObj['NameFilterCaseSensitive'] = False
        retArr = []
        sortFilterObj = _json.dumps(sortFilterObj)
        try:
            request = Request(url, sortFilterObj.encode('utf-8'))
            request.add_header('Content-Type', 'application/json')
            response = urlopen(request)
            results = response.read()
            recurringResults = _json.loads(results)
            for recurring in  recurringResults['ManageResults']['EPGEvents']:
                theDict = self._recurr2dict(recurring['epgEventJSONObject'])
                if theDict != None:
                    retArr.append(theDict)
        except:
            retArr = None

        xbmc.log("getScheduledRecordings JSON end")

        return retArr
######################################################################################################
    def getConflictedRecordings(self, userid, password):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            retArr = self.getConflictedRecordings_json()
            return retArr


    def getConflictedRecordings_json(self,conflict = False):
        xbmc.log("getConflictedRecordings JSON start")
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/Get/SortedFilteredList' + self.jsid
        xbmc.log(url)
        sortFilterObj = {}

        sortFilterObj['resultLimit'] = -1

        # Figure out the sorting....
        sortFilterObj['datetimeSortSeq'] = 0
        sortFilterObj['channelSortSeq'] = 0
        sortFilterObj['titleSortSeq'] = 0
        sortFilterObj['statusSortSeq'] = 0
        sortFilterObj['datetimeDecending'] = False
        sortFilterObj['channelDecending'] = False
        sortFilterObj['titleDecending'] = False
        sortFilterObj['statusDecending'] = False

        # Then the filtering....
        sortFilterObj['All'] = False
        sortFilterObj['None'] = False
        sortFilterObj['Pending'] = False
        sortFilterObj['InProgress'] = False
        sortFilterObj['Completed'] = False
        sortFilterObj['Failed'] = False
        sortFilterObj['Conflict'] = True
        sortFilterObj['Recurring'] = False
        sortFilterObj['Deleted'] = False

        sortFilterObj['FilterByName'] = False
        sortFilterObj['NameFilter'] = ''
        sortFilterObj['NameFilterCaseSensitive'] = False
        retArr = []
        sortFilterObj = _json.dumps(sortFilterObj)
        try:
            request = Request(url, sortFilterObj.encode('utf-8'))
            request.add_header('Content-Type', 'application/json')
            response = urlopen(request)
            results = response.read()
            conflictResults = _json.loads(results)
            for conflict in  conflictResults['ManageResults']['EPGEvents']:
                theDict = self._rec2dict1_json(conflict)
                if theDict != None:
                    retArr.append(theDict)
        except:
            retArr = None

        xbmc.log("getConflictedRecordings JSON end")

        return retArr


######################################################################################################
    def updateRecording(self, userid, password, progDetails):

        if self.settings.XNEWA_INTERFACE == 'JSON':
            return self.updateRecording_json(progDetails)
        else:
            return updateRecording_v5(self,progDetails)

    def updateRecording_json(self, progDetails):

        days = progDetails['day']

        recObj = {}

        recObj['ChannelOid'] = progDetails['channel_oid']
        recObj['startDate'] = str(progDetails['start'] - self.dst_offset)
        recObj['endDate'] = str(progDetails['end'] - self.dst_offset)
        if progDetails['recquality'].lower() == "good":
            recObj['qualityGood'] = True
        elif progDetails['recquality'].lower() == "better":
            recObj['qualityBetter'] = True
        elif progDetails['recquality'].lower() == "best":
            recObj['qualityBest'] = True
        else:
            recObj['qualityDefault'] = True

        if 'Monday' in days:
            recObj['dayMonday'] = True
        else:
            recObj['dayMonday'] = False
        if 'Tuesday' in days:
            recObj['dayTuesday'] = True
        else:
            recObj['dayTuesday'] = False
        if 'Wednesday' in days:
            recObj['dayWednesday'] = True
        else:
            recObj['dayWednesday'] = False
        if 'Thursday' in days:
            recObj['dayThursday'] = True
        else:
            recObj['dayThursday'] = False
        if 'Friday' in days:
            recObj['dayFriday'] = True
        else:
            recObj['dayFriday'] = False
        if 'Saturday' in days:
            recObj['daySaturday'] = True
        else:
            recObj['daySaturday'] = False
        if 'Sunday' in days:
            recObj['daySunday'] = True
        else:
            recObj['daySunday'] = False


        recObj['recColorRed'] = False
        recObj['recColorGreen'] = False
        recObj['recColorYellow'] = False
        recObj['recColorBlue'] = False

        recObj['onlyNew'] = progDetails['onlyNew']
        recObj['allChannels'] = progDetails['allChannels']
        recObj['pre_padding_min'] = progDetails['prepadding']
        recObj['post_padding_min'] = progDetails['postpadding']
        try:
            recObj['extend_end_time_min'] = progDetails['extendend']
        except:
            recObj['extend_end_time_min'] = 0

        recObj['days_to_keep'] = progDetails['maxrecs']

        if progDetails['directory'] != "Default":
            recObj['recDirId'] = progDetails['directory']

        if progDetails['rectype'] == 'Recurring':
            recObj['recurrOID'] = progDetails['recording_oid']
            recObj['recurringName'] = progDetails['name']
            recObj['manualRecTitle'] = progDetails['title']
            if 'TimeSlot' in progDetails['desc']:
                recObj['recordThisTimeslot'] = True
            else:
                recObj['recordAnyTimeslot'] = True

            if len(days) == 1:
                recObj['recordThisDay'] = True
            elif len(days) == 7:
                recObj['recordAnyDay'] = True
            else:
                recObj['recordSpecificDay'] = True

            if progDetails['rules'] != None:
                if progDetails['rules'].startswith('KEYWORD:'):
                    recObj['rules'] = progDetails['rules']
                #pass
                #recObj['rules'] = progDetails['rules']

            if progDetails['priority'] != 0:
                recObj['recurr_priority'] = progDetails['priority']

            url = "http://" + self.ip + ":" + str(self.port) + '/public/ScheduleService/UpdateRecurr' + self.jsid
        else:
            recObj['scheduleOID'] = progDetails['recording_oid']
            url = "http://" + self.ip + ":" + str(self.port) + '/public/ScheduleService/UpdateRec' + self.jsid

        recObj = _json.dumps(recObj)

        xbmc.log(url)
        try:
            try:
                request = Request(url, recObj)
                request.add_header('Content-Type', 'application/json')
                response = urlopen(request)
            except URLError as e:
                print (e.code)
                return False
            else:
                print (response.getcode())
                results = response.read()
                updateResults = _json.loads(results)
                print (updateResults)
            return True
        except Exception as err:
            print (err)
            return False


######################################################################################################
    def scheduleRecording(self, userid, password, progDetails):
        if self.settings.XNEWA_INTERFACE == 'JSON':
            return self.scheduleRecording_json(progDetails)
        else:
            return scheduleRecording_v5(self,progDetails)



######################################################################################################
    def scheduleRecording_json(self, progDetails):

        recObj = {}

        if progDetails['recquality'].lower() == "good":
            recObj['qualityGood'] = True
        elif progDetails['recquality'].lower() == "better":
            recObj['qualityBetter'] = True
        elif progDetails['recquality'].lower() == "best":
            recObj['qualityBest'] = True
        else:
            recObj['qualityDefault'] = True

        recObj['dayMonday'] = False
        recObj['dayTuesday'] = False
        recObj['dayWednesday'] = False
        recObj['dayThursday'] = False
        recObj['dayFriday'] = False
        recObj['daySaturday'] = False
        recObj['daySunday'] = False
        recObj['onlyNew'] = False
        recObj['allChannels'] = False

        recObj['recColorRed'] = False
        recObj['recColorGreen'] = False
        recObj['recColorYellow'] = False
        recObj['recColorBlue'] = False

        recObj['epgeventOID'] = progDetails['program_oid']
        recObj['ChannelOid'] = 0
        recObj['startDate'] = str(progDetails['start'])
        recObj['endDate'] = str(progDetails['end'])

        if progDetails['directory'] != "Default":
            recObj['recDirId'] = progDetails['directory']

        if progDetails['rectype'] == 'Record Once':
            recObj['recordOnce'] = True
            recObj['recordThisDay'] = True
        elif progDetails['rectype'] == "Record Season (NEW episodes on this channel)":
            recObj['onlyNew'] = True
            recObj['recordAnyDay'] = True
            recObj['recordAnyTimeslot'] = True
        elif progDetails['rectype'] == "Record Season (All episodes on this channel)":
            recObj['recordAnyDay'] = True
            recObj['recordAnyTimeslot']  = True
        elif progDetails['rectype'] == "Record Season (Daily, this timeslot)":
            recObj['recordAnyDay'] = True
            recObj['recordThisTimeslot'] = True
        elif progDetails['rectype'] == "Record Season (Weekly, this timeslot)":
            recObj['recordThisDay'] = True
            recObj['recordThisTimeslot'] = True
        elif progDetails['rectype'] == "Record Season (Monday-Friday, this timeslot)":
            recObj['recordSpecificdays'] = True
            recObj['recordThisTimeslot'] = True
            recObj['dayMonday'] = True
            recObj['dayTuesday'] = True
            recObj['dayWednesday'] = True
            recObj['dayThursday'] = True
            recObj['dayFriday'] = True
        elif progDetails['rectype'] == "Record Season (Weekends, this timeslot)":
            recObj['recordSpecificdays'] = True
            recObj['recordThisTimeslot'] = True
            recObj['daySaturday'] = True
            recObj['daySunday'] = True
        elif progDetails['rectype'] == "Record All Episodes, All Channels":
            recObj['allChannels'] = True
            recObj['recurringName'] = progDetails['title']
            recObj['manualRecTitle']  = progDetails['title']
            recObj['recordAnyDay'] = True
            recObj['recordAnyTimeslot'] = True
        else:
            xbmc.log("Unknown rectype")
            return False

        try:

            if self.defaultSchedule == None:
                self.getDefaultSchedule()

            recObj['pre_padding_min'] = progDetails['prepadding']
            recObj['post_padding_min'] = progDetails['postpadding']
            recObj['extend_end_time_min'] = 0
            recObj['days_to_keep'] = progDetails['maxrecs']
            recObj = _json.dumps(recObj)
            url = "http://" + self.ip + ":" + str(self.port) + '/public/ScheduleService/Record' + self.jsid
            xbmc.log(url)
            request = Request(url, recObj.encode('utf-8'))
            request.add_header('Content-Type', 'application/json')
            try:
                xbmc.log('Posting')
                response = urlopen(request)
                self.changedRecordings = True
                results = response.read()
                scheduleResults = _json.loads(results)
                return response.code

            except URLError as e:
                if e.code == 500:
                    eresults = e.read()
                    scheduleResults = _json.loads(eresults)
                    print (scheduleResults)
                    if 'schdConflicts' in scheduleResults['epgEventJSONObject']:
                        conflictName = []
                        for conflict in scheduleResults['epgEventJSONObject']['schdConflicts']:
                            conflictName.append(conflict['Name'])
                        choice =  xbmcgui.Dialog().select(smartUTF8(__language__(30132)), py2_decode(conflictName))
                        if choice != -1:
                            miniDetails = {}
                            miniDetails['rectype'] = conflict['Type']
                            miniDetails['status'] = conflict['Status']
                            miniDetails['recording_oid'] = conflict['OID']
                            cancelled = self.cancelRecording_json(miniDetails)
                            if cancelled == True:
                                return self.scheduleRecording_json(progDetails)
                            else:
                                return 400
                    else:
                        self.Last_Error = scheduleResults['epgEventJSONObject']['rtn']['Message']
                    return e.code
        except Exception as err:
            print(err)
            return -1

######################################################################################################

    def getDefaultSchedule(self):
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ScheduleService/Get/SchedSettingsObj' + self.jsid
        xbmc.log(url)
        json_file = urlopen(url)
        self.defaultSchedule = _json.load(json_file)
        json_file.close()
        xbmc.log(str(json_file))


######################################################################################################
    def cancelRecording(self, userid, password, progDetails):
        if self.settings.XNEWA_INTERFACE == 'JSON':
            return self.cancelRecording_json(progDetails)
        else:
            return cancelRecording_v5(self,progDetails)

    def cancelRecording_json(self, progDetails):
        xbmc.log(str(progDetails))
        if progDetails['rectype'].lower() == "recurring" or progDetails['status'].lower() == "recurring":
            debug("Cancelling Recurring")
            url = "http://" + self.ip + ":" + str(self.port) + '/Public/ScheduleService/CancelRecurr/' + str(progDetails['recording_oid']) + self.jsid
        elif progDetails['status'].lower() == "pending" or progDetails['status'].lower() == "in-progress":
            url = "http://" + self.ip + ":" + str(self.port) + '/Public/ScheduleService/CancelRec/' + str(progDetails['recording_oid']) + self.jsid
        elif progDetails['status'].lower() == "completed":
            debug("Cancelling and Deleting")
            url = "http://" + self.ip + ":" + str(self.port) + '/Public/ScheduleService/Delete/' + str(progDetails['recording_oid']) + self.jsid
        elif progDetails['status'].lower() == "failed"  or progDetails['status'].lower() == "conflict" :
            debug("Cancelling and Deleting")
            url = "http://" + self.ip + ":" + str(self.port) + '/Public/ScheduleService/Delete/' + str(progDetails['recording_oid']) + self.jsid
        else: ## "deleted":
            debug("Cancelling and Deleting")
            url = "http://" + self.ip + ":" + str(self.port) + '/Public/ScheduleService/CancelDelRec/' + str(progDetails['recording_oid']) + self.jsid
        xbmc.log(url)
        json_file = urlopen(url)
        cancelService = _json.load(json_file)
        json_file.close()
        if cancelService['epgEventJSONObject']['rtn']['Error'] == False:
            self.changedRecordings = True
        return (not cancelService['epgEventJSONObject']['rtn']['Error'])


# Helper functions


######################################################################################################
# public functions to format the datetime object returned by NPVR
######################################################################################################
    def formatDate( self, dt, withyear=False, gmtoffset=False ):
        if gmtoffset:
            dt = dt - timedelta(seconds=time.timezone if (time.localtime().tm_isdst == 0) else time.altzone)
        return dt.strftime( self._dateformat( withyear ) )


    def formatTime( self, dt, withsecs=False, leadzero=False, gmtoffset=False ):
        if gmtoffset:
            dt = dt - timedelta(seconds=time.timezone if (time.localtime().tm_isdst == 0) else time.altzone)
        df = dt.strftime( self._timeformat( withsecs ) )
        if leadzero or not df.startswith('0'):
            return df
        else:
            return df[1:]

######################################################################################################
# internal function to return a valid format string for strftime based on XBMC region settings
######################################################################################################
    def _dateformat( self, withyear ):
        datewithyear = xbmc.getRegion('datelong').replace('A', 'a').replace('B', 'b')
        if withyear:
            return datewithyear
        else:
            return datewithyear.replace('%Y', '').rstrip().rstrip(',')


    def _timeformat( self, withsecs ):
        timewithsecs = xbmc.getRegion('time')
        if withsecs:
            return timewithsecs
        else:
            return timewithsecs.replace(':%S', '')


######################################################################################################
# Translating a json epgEventJSONObject into a dictionary object...
######################################################################################################
    def _rec2dict1_json(self, epgEventJSONObject, recDir=None):
        import re
        theDict = {}
        theDict['schdConflicts'] = None
        try:
            q = epgEventJSONObject['epgEventJSONObject']['rtn']
        except:
            xbmc.log('Conflict?')
        try:
            prog = epgEventJSONObject['epgEventJSONObject']['epgEvent']
        except:
            return None
        if prog['HasSchedule'] is True:
            rec = epgEventJSONObject['epgEventJSONObject']['schd']
            if rec['Status'] == 'Conflict':
                if prog['ScheduleHasConflict'] is True:
                    theDict['schdConflicts'] = epgEventJSONObject['epgEventJSONObject']['schdConflicts']
        if prog['Title'] is not None:
            theDict['title'] = py2_decode(prog['Title'])
            if prog['Title'] == '' and prog['HasSchedule'] is True:
                theDict['title'] = py2_decode(rec['Name'])
        else:
            theDict['title'] = py2_decode(rec['Name'])
        if prog['StartTime'] != '' and prog['StartTime'] != '0001-01-01T00:00:00':
            theDict['start'] = self.jsonDate(prog['StartTime'],self.dst_offset)
            theDict['end'] = self.jsonDate(prog['EndTime'],self.dst_offset)
        else:
            theDict['start'] = self.jsonDate(rec['StartTime'],self.dst_offset)
            theDict['end'] = self.jsonDate(rec['EndTime'],self.dst_offset)
        if prog['Desc'] is not None:
            theDict['desc'] = py2_decode(prog['Desc'])
        else:
            theDict['desc'] = ""
        if prog['Subtitle'] is not None:
            theDict['subtitle'] = py2_decode(prog['Subtitle'])
        else:
            theDict['subtitle'] = ""
        if 'Season' in prog:
            theDict['season'] = prog['Season']
        else:
            theDict['season'] = 0
        if 'Episode' in prog:
            theDict['episode'] = prog['Episode']
        else:
            theDict['episode'] = 0
        if 'Significance' in prog:
            theDict['significance'] = prog['Significance']
        else:
            theDict['significance'] = ''
        theDict['program_oid'] = prog['OID']
        if prog['HasSchedule'] is True:
            theDict['priority'] = rec['Priority']
            if rec['Status'] == 'Recurring':
                theDict['rectype'] = prog['recordingType']
            else:
                theDict['rectype'] = self.SCHEDULE_ONCE
            if rec['RecordingFileName'] is not None:
                if rec['Status'] == "Completed" or rec['Status'] == "In-Progress":
                    if recDir != None and not rec['RecordingFileName'].startswith(recDir):
                        return None
                    m = re.search('.S(\d{1,2})E(\d{1,3})',rec['RecordingFileName'])
                    if m:
                        theDict['season'] = int(m.group(1))
                        theDict['episode'] = int(m.group(2))
                    theDict['start'] = self.jsonDate(rec['StartTime'],self.dst_offset)
                    theDict['end'] = self.jsonDate(rec['EndTime'],self.dst_offset)
                    theDict['filename'] = rec['RecordingFileName']
                    theDict['resume'] = rec['PlaybackPosition']
                    theDict['duration'] = rec['PlaybackDuration']
                    theDict['directory'] = ''
                    theDict['rec'] = False
                    if self.settings.XNEWA_COLOURS != None:
                        foundColour = False
                        if 'red' in self.settings.XNEWA_COLOURS and rec['Red'] :
                            foundColour = True
                        elif 'green' in self.settings.XNEWA_COLOURS  and rec['Green'] :
                            foundColour = True
                        elif 'yellow' in self.settings.XNEWA_COLOURS and rec['Yellow']:
                            foundColour = True
                        elif 'blue' in self.settings.XNEWA_COLOURS and rec['Blue']:
                            foundColour = True

                        if foundColour == False:
                            return None
                else:
                    theDict['filename'] = ''
                    theDict['resume'] = 0
                    theDict['duration'] = 0
                    theDict['directory'] = rec['RecordingFileName'][1:-1]
                    theDict['rec'] = True
            else:
                theDict['directory'] = "Default"
                theDict['filename'] = ''
                theDict['rec'] = True
            if theDict['duration'] !=0 and rec['Status'] == 'Completed':
                completed = theDict['duration'] - theDict['resume']
                if completed < 60:
                    theDict['status'] = 'Watched'
                elif theDict['resume'] < 60:
                    theDict['status'] = 'Not Watched'
                else:
                    theDict['status'] = 'Partial ' + str(100 * theDict['resume']//theDict['duration']) + ' %'
            else:
                theDict['status'] = rec['Status']

            theDict['recording_oid'] = rec['OID']
            theDict['channel_oid'] = rec['ChannelOid']
        else:
            theDict['priority'] = ""
            theDict['rectype'] = ""
            theDict['status'] = ""
            theDict['recording_oid'] = ""
            theDict['rec'] = False
            theDict['channel_oid'] = prog['ChannelOid']
        if str(theDict['channel_oid']) in self.channels:
            theDict['channel'] = self.channels[str(theDict['channel_oid'])]
        else:
            theDict['channel'] = self.channels['0']
        return theDict


######################################################################################################
# Translating a (JSON ) recurring object into a dictionary object...
######################################################################################################
    def _recurr2dict(self, epgEventJSONObject):
        theDict = {}
        rtn = epgEventJSONObject['rtn']
        rec = epgEventJSONObject['recurr']
        try:
            try:
                theDict['title'] = rec['EPGTitle'].encode('utf-8')
                theDict['name'] = rec['RecurringName'].encode('utf-8')
            except:
                if rec['RecurringName'] != None:
                    theDict['title'] = rec['RecurringName'].encode('utf-8')
                else:
                    theDict['title'] = 'Unnamed'
                    theDict['name'] = 'Unnamed'
        except:
            theDict['title'] = rec['Name'].encode('utf-8')
            theDict['name'] = rec['Name'].encode('utf-8')
        theDict['start'] = self.jsonDate(rec['StartTime'],self.dst_offset)
        theDict['end'] = self.jsonDate(rec['EndTime'],self.dst_offset)
        #todo fix Rules display
        rules = str(rec['RulesXmlDoc']['Rules'])
        if rec['AdvancedRules'] != None:
            theDict['rules'] = rec['AdvancedRules']
            if rec['AdvancedRules'].startswith('KEYWORD:'):
                theDict['desc'] = rec['AdvancedRules']
            else:
                theDict['desc'] = 'Advanced Rules = ' + rules
        else:
            theDict['desc'] = rules
            theDict['rules'] = None

        try:
            if rec['RecordingDirectoryID'] == '':
                theDict['directory'] = "Default"
            else:
                theDict['directory'] = rec['RecordingDirectoryID'][1:-1]
        except:
            theDict['directory'] = "Default"

        theDict['subtitle'] = ""
        theDict['program_oid'] = 0
        theDict['rec'] = False

        theDict['priority'] = rec['Priority']
        theDict['rectype'] = rec['Type']
        theDict['status'] = ''
        theDict['recording_oid'] = rec['OID']
        theDict['channel_oid'] = rec['ChannelOid']

        if str(theDict['channel_oid']) in self.channels:
            theDict['channel'] = self.channels[str(theDict['channel_oid'])]
        else:
            theDict['channel'] = self.channels['0']
        theDict['genres'] = ""
        theDict['recquality'] = rec['Quality']
        theDict['prepadding'] = rec['PrePadding']
        theDict['postpadding'] = rec['PostPadding']
        theDict['maxrecs'] = rec['MaxRecordings']
        theDict['onlyNew'] = rec['OnlyNew']
        theDict['day'] = rec['Day'].split(',')
        theDict['allChannels'] = rec['allChannels']
        theDict['movie'] = False
        return theDict


######################################################################################################
# Translating a (xml) recording.list into a dictionaries...
######################################################################################################
    def _rec2dictDirect(self):
        import xml.etree.ElementTree as ET
        xbmc.log("Processing xml pending recording list start")
        url = self.getURL()+ "/services?method=recording.list&filter=pending&sid=" + self.sid
        xbmc.log(url)
        request = Request(url, headers={"Accept" : "application/xml"})
        u = urlopen(request)
        tree = ET.parse(u)
        root = tree.getroot()
        dic = {}
        for recording in root.find('recordings'):
            if recording.find('status').text == 'Pending':
                dic[recording.find('epg_event_oid').text] = recording.find('status').text.encode('utf-8')
        xbmc.log("Processing xml pending recording list end")
        return dic

######################################################################################################
# Translating a (xml) programmelist into an array of dictionaries...
######################################################################################################
    def _progs2array_xml(self,url,getRecordings=True):

        xbmc.log("Processing xml listings start")

        retArr = []
        import xml.etree.ElementTree as ET
        import codecs
        import time
        self.miniEPG = datetime.max

        if getRecordings == True:
            pass
            #mydic = self._rec2dictDirect()
            mydic = {}
        else:
            mydic = {}

        #parser = ET.XMLParser(encoding="utf-8")
        #c = codecs.open('c:/temp/guide.xml',encoding='utf-16')
        if True:
            request = Request(url, headers={"Accept" : "application/xml"})
            u = urlopen(request)
            tree = ET.parse(u)
        else:
            tree = ET.parse('c:/temp/service.xml')
        root = tree.getroot()
        for channel in root.find('listings'):
            chan = {}
            chan['name'] = channel.attrib['name']
            chan['oid'] = channel.attrib['id']
            chan['num'] = channel.attrib['number']
            progs = []
            for listing in channel.findall('l'):
                dic = {}
                dic['title'] = str(listing.find('name').text)
                if listing.find('description').text != None:
                    temp = listing.find('description').text.split(':')
                    if len(temp) < 2:
                        dic['subtitle'] = ''
                        dic['desc'] = str(temp[0])
                    else:
                        dic['desc'] = str(temp[1])
                        dic['subtitle'] = str(temp[0])
                else:
                    dic['desc'] = ""
                    dic['subtitle'] = ""

                dic['start'] = datetime.fromtimestamp((float(listing.find('start').text)/1000))
                dic['end'] = datetime.fromtimestamp((float(listing.find('end').text)/1000))
                if self.miniEPG > dic['end']:
                   self.miniEPG = dic['end']

                dic['oid'] = listing.find('id').text
                if dic['oid'] in mydic:
                    dic['rec'] = True
                else:
                    dic['rec'] = False
                dic['genreColour'] = 0
                if listing.find('genre') != None:
                    genre = listing.find('genre').text
                    dic['genres'] = genre
                    try:
                        if self.genresColours[genre] != 0:
                            dic['genreColour'] = str(hex(self.genresColours[genre]))
                    except:
                        pass
                else:
                    dic['genres'] = ''
                if listing.find('firstrun') != None:
                    dic['firstrun'] = listing.find('firstrun').text == 'true'
                else:
                    dic['firstrun'] = False
                progs.append(dic)
            chan['progs'] = progs
            #v5 changes
            chan['season'] = 0
            retArr.append(chan)
        xbmc.log("Process listing end")
        return retArr


######################################################################################################
# Translating a (json) programmelist into an array of dictionaries...
######################################################################################################
    def _progs2array_json(self,url):

        xbmc.log("Processing json listings start")

        retArr = []

        import time
        self.miniEPG = datetime.max

        if True:
            guideService = self.nextJson(url)
        else:
            tree = ET.parse('c:/temp/service.xml')

        dict = {}
        for listing in guideService['Guide']['Listings']:
            channel = {}
            channel['name'] = py2_decode(listing['Channel']['channelName'])
            channel['oid'] = listing['Channel']['channelOID']
            if 'channelMinor' not in (listing['Channel']):
                channel['num'] = str(listing['Channel']['channelNumber'])
            elif listing['Channel']['channelMinor'] == 0:
                channel['num'] = str(listing['Channel']['channelNumber'])
            else:
                channel['num'] = str(listing['Channel']['channelNumber']) + '.' + str(listing['Channel']['channelMinor'])
            progs = []
            for event in listing['EPGEvents']:
                prog = event['epgEventJSONObject']['epgEvent']
                dic = {}
                dic['title'] = py2_decode(prog['Title'])
                dic['subtitle'] = py2_decode(prog['Subtitle'])
                if prog['Desc'] is not None:
                    dic['desc'] = py2_decode(prog['Desc'])
                else:
                    dic['desc'] = ""
                dic['start'] = self.jsonDate(prog['StartTime'],self.dst_offset)
                dic['end'] = self.jsonDate(prog['EndTime'],self.dst_offset)
                dic['oid'] = prog['OID']
                dic['genreColour'] = 0
                dic['season'] = prog['Season']
                dic['episode'] = prog['Episode']
                if prog['Genres']:
                    dic['genres'] = prog['Genres']
                    for genre in prog['Genres']:
                        try:
                            if self.genresColours[genre] != 0:
                                dic['genreColour'] = str(hex(self.genresColours[genre]))
                        except:
                            pass
                else:
                    dic['genres'] = ''

                if prog['HasSchedule'] is True:
                    rec = event['epgEventJSONObject']['schd']
                    if rec['Status'] == 'Pending' or rec['Status'] == 'In-Progress':
                        dic['rec'] = True
                    else:
                        dic['rec'] = False
                    if prog['ScheduleHasConflict'] == True:
                        dic['genreColour'] =  '0xFF000080'

                    if self.settings.XNEWA_COLOURS != None:
                        foundColour = False
                        if 'red' in self.settings.XNEWA_COLOURS and rec['Red'] :
                            foundColour = True
                        elif 'green' in self.settings.XNEWA_COLOURS  and rec['Green'] :
                            foundColour = True
                        elif 'yellow' in self.settings.XNEWA_COLOURS and rec['Yellow']:
                            foundColour = True
                        elif 'blue' in self.settings.XNEWA_COLOURS and rec['Blue']:
                            foundColour = True

                        if foundColour == False:
                            continue
                else:
                    dic['rec'] = False

                dic['firstrun'] = prog['FirstRun']
                if dic['firstrun'] and prog['UniqueId'].startswith('EP'):
                    if prog['Significance'] == 'Series Premiere':
                        dic['title'] = dic['title'] + ' (SP)'
                    elif prog['Significance'] == 'Series Finale':
                        dic['title'] = dic['title'] + ' (SF)'
                    else:
                        dic['title'] = dic['title'] + ' (N)'

                dic['significance'] = prog['Significance']

                progs.append(dic)
            channel['progs'] = progs
            retArr.append(channel)
        xbmc.log("Process listing end")
        return retArr

######################################################################################################
# fanart retrieval functions
######################################################################################################
    ######################################################################################################
    # Try to load a channel icon
    ######################################################################################################
    def getChannelIcon(self, name):
        self.channelIcons = self._getFiles(self.channelPath)
        self.cached_channelIcons = self._getFiles(self.cached_channelPath)
        return self._getLocalorCacheIcon(name, self.channelPath, self.channelIcons, self.cached_channelPath, self.cached_channelIcons)

    ######################################################################################################
    # Try to load a show icon
    ######################################################################################################
    def getShowIcon(self, name):
        self.showIcons = self._getFiles(self.showPath)
        self.cached_showIcons = self._getFiles(self.cached_showPath)
        return self._getLocalorCacheIcon(name, self.showPath, self.showIcons, self.cached_showPath, self.cached_showIcons)

    ######################################################################################################
    # Try to load a genre icon
    ######################################################################################################
    def getGenreIcon(self, name):
        self.genreIcons = self._getFiles(self.genrePath)
        self.cached_genreIcons = self._getFiles(self.cached_genrePath)
        return self._getLocalorCacheIcon(name, self.genrePath, self.genreIcons, self.cached_genrePath, self.cached_genreIcons)

    ######################################################################################################
    # download fanart from NextPVR
    ######################################################################################################
    def getFanArt(self, Fanart, title):
        if FanArt is not None:
            url = self.getURL() +'/'+ FanArt
            xbmc.log(url)
            try:
                host, path = urlparse(url)[1:3]    # elems [1] and [2]
                conn = http.client.HTTPConnection(host)
                conn.request('HEAD', path)
                mys = conn.getresponse().status
            except Exception:
                mys = 404
            if mys==200:
                try:
                    import string
                    valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
                    safename = ''.join(ch for ch in title if ch in valid_chars)

                    urlretrieve (url, self.showPath + '/' + safename + '.jpg')
                except Exception:
                    xbmc.log('Error downloading ' + url)

    #Helper Functions

    ######################################################################################################
    # Try the local directory first, then the cache
    ######################################################################################################
    def _getLocalorCacheIcon(self, name, path, icons, cached_path, cached_icons):
        savedIcon = self._getIcon(name, path, icons)
        if savedIcon is not None:
            return savedIcon
        return self._getIcon(name, cached_path, cached_icons)

    ######################################################################################################
    # Finding a file in a directory, caching the contents....
    ######################################################################################################
    def _getIcon(self, name1, path, var):
        name = name1.encode('ascii','ignore').decode('utf-8')
        import string
        valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
        safename = ''.join(ch for ch in name if ch in valid_chars)
        for icon1 in var:
            icon = icon1.decode('utf-8')
            if os.path.splitext(icon)[0].lower() == safename.lower():
                return os.path.join(path, icon)
            if len(safename) > 1 :
                for icon1 in var:
                    icon = icon1.decode('utf-8')
                    if os.path.splitext(icon)[0].lower().find(safename.lower().encode('ascii','ignore').decode('utf-8')) >= 0:
                        return os.path.join(path, icon)
                    if safename.lower().find(os.path.splitext(str(icon))[0].lower()) >= 0:
                        #xbmc.log(safename)
                        return os.path.join(path, icon)
        return None

    ######################################################################################################
    # Loading an array with contents
    ######################################################################################################
    def _getFiles(self, path, encoding='utf-8'):
      for (path, dirs, files) in os.walk(path.encode(encoding)):
          var = files
      return var


######################################################################################################
# Translating a (json) detailrecord into a dictionary...
######################################################################################################
    def _detail2array_json(self, detailsService,fetchArt=False):

        numrec = len(detailsService['epgEventJSONObject']) -1
        error = detailsService['epgEventJSONObject']['rtn']
        dict = {}

        if error['Error'] is True:
            xbmc.log(error['Message'])
            return dict


        detail =  detailsService['epgEventJSONObject']['epgEvent']
        try:
            if detail['HasSchedule'] is True:
                recording = detailsService['epgEventJSONObject']['schd']
            else:
                recording = None

            if detail['ScheduleIsRecurring'] is True:
                if 'recurr' in detailsService['epgEventJSONObject']:
                    recurring = detailsService['epgEventJSONObject']['recurr']
                else:
                    recurring = None
            else:
                recurring = None

            if detail['OID'] == 0:
                detail = None
                dict['channel_oid'] = recording['ChannelOid']
                dict['title'] = py2_decode(recording['Name'])
                dict['start'] = self.jsonDate(recording['StartTime'],self.my_offset)
                dict['end'] = self.jsonDate(recording['EndTime'],self.my_offset)
                dict['desc'] = ""
                dict['subtitle'] = ""
                dict['program_oid'] = None
                dict['genres'] = ''
                dict['movie'] = False
                dict['season'] = 0
                dict['episode'] = 0

        except:
            prog = None
            xbmc.log('unknown record error in details')

        import re

        if detail is not None:
            if detail['Title'] is not None:
                dict['title'] = py2_decode(detail['Title'])
            else:
                dict['title'] = py2_decode(rec.Name)

            if 'Significance' in detail:
                dict['significance'] = detail['Significance']
            else:
                dict['significance'] = ''

            if self.jsonDate(detail['StartTime'],self.my_offset).year > 1:
                dict['start'] = self.jsonDate(detail['StartTime'],self.my_offset)
                dict['end'] = self.jsonDate(detail['EndTime'],self.my_offset)
            else:
                dict['start'] = rec.StartTime + self.dst_offset
                dict['end'] = rec.EndTime + self.dst_offset

            if detail['Desc'] is not None:
                dict['desc'] = py2_decode(detail['Desc'])
            else:
                dict['desc'] = ""
            if detail['Subtitle'] is not None:
                dict['subtitle'] = py2_decode(detail['Subtitle'])
            else:
                dict['subtitle'] = ""

            if detail['OID'] != 0:
                dict['channel_oid'] = detail['ChannelOid']
            else:
                dict['channel_oid'] = rec.OID
            dict['program_oid'] = detail['OID']
            dict['movie'] = False
            if detail['Genres']:
                dict['genres'] = detail['Genres']
                for  genre in detail['Genres']:
                    if genre == "Movie" or genre == "Movies" or genre == "Film":
                        dict['movie'] = True
                        break
            else:
                dict['genres'] = ''
            if 'Season' in detail:
                dict['season'] = detail['Season']
            else:
                dict['season'] = 0
            if 'Episode' in detail:
                dict['episode'] = detail['Episode']
            else:
                dict['episode'] = 0

        if str(dict['channel_oid']) in self.channels:
            dict['channel'] = self.channels[str(dict['channel_oid'])]
        else:
            dict['channel'] = self.channels['0']
        if fetchArt == True and self.offline == False and self.getShowIcon(dict['title']) is None:
            FanArt = None
            try:
                if detail is not None:
                    if detail['FanArt'] != '':
                        FanArt = detail['FanArt']

                elif FanArt is None and rec is not None:
                    FanArt = recording['FanArt']
            except:
                pass

            if FanArt is not None:
                url = self.getURL() +'/'+ FanArt
                xbmc.log('getting fanart from %s' % url)
                try:
                    host, path = urlparse(url)[1:3]    # elems [1] and [2]
                    conn = http.client.HTTPConnection(host)
                    conn.request('HEAD', path)
                    mys = conn.getresponse().status
                except Exception:
                    mys = 404
                if mys==200:
                    try:
                        import string
                        valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
                        safename = ''.join(ch for ch in dict['title'] if ch in valid_chars)
                        urlretrieve (url,self.showPath + '/' + safename +'.jpg')
                    except Exception:
                        xbmc.log('Error downloaing ' + url)
        if recording is not None:
            dict['status'] = recording['Status']
            if recording['Status'] == "Completed" or recording['Status'] == "In-Progress" or recording['Status'] == "":
                dict['start'] = self.jsonDate(recording['StartTime'],self.my_offset)
                dict['end'] = self.jsonDate(recording['EndTime'],self.my_offset)
                if recording['RecordingFileName'] is not None:
                    f = recording['RecordingFileName']
                    dict['filename'] = f
                    dict['resume'] = recording['PlaybackPosition']
                    m = re.search('.S(\d{1,2})E(\d{1,3})',recording['RecordingFileName'])
                    if m != None:
                        dict['season'] = int(m.group(1))
                        dict['episode'] = int(m.group(2))

                else:
                    dict['filename'] = ''
                    dict['resume'] = 0
                dict['duration'] = recording['PlaybackDuration']
                dict['library_duration'] = (dict['end'] - dict['start']).seconds
                dict['directory'] = None
            else:
                dict['resume'] = 0
                dict['duration'] = 0
                if recording['RecordingFileName'] is not None:
                    dict['directory'] = recording['RecordingFileName'][1:-1]
                else:
                    dict['directory'] = "Default"
            dict['recording_oid'] = recording['OID']
            dict['rectype'] = recording['Type']
            dict['recday'] = recording['Day']
            dict['recquality'] = recording['Quality']
            dict['prepadding'] = recording['PrePadding']
            dict['postpadding'] = recording['PostPadding']
            dict['maxrecs'] = recording['MaxRecordings']
            dict['priority'] = recording['Priority']

        else:
            dict['status'] = ""
            dict['recording_oid'] = 0
            dict['rectype'] = ""
            dict['recday'] = ""
            dict['recquality'] = ""
            dict['prepadding'] = ""
            dict['postpadding'] = ""
            dict['maxrecs'] = ""
            dict['priority'] = ""
            dict['directory'] = ""
            dict['resume'] = 0


        if 'cast' in detailsService['epgEventJSONObject']:
            dict['cast'] = detailsService['epgEventJSONObject']['cast']
        else:
            dict['cast'] = ''

        if 'crew' in detailsService['epgEventJSONObject']:
            dict['crew'] = detailsService['epgEventJSONObject']['crew']
        else:
            dict['crew'] = ''

        #try:
        #    dict['genres'] = ""
        #except:
        #    pass

        return dict
######################################################################################################
# Retrieving an element-tree from a dom as a dictonary
######################################################################################################
    def _getdictfromdom(self, dom, tag):

        retArr = []

        if not dom:
            return None

        for tnode in dom.getElementsByTagName(tag):
            retDic = {}
            for n in tnode.childNodes:
                if n.nodeType == 1:
                    retDic[str(n.nodeName)] = n.firstChild.nodeValue #.encode('utf-8')

            retArr.append(retDic)

        return retArr
#################################################################################################################
    def jsonDate(self, dateStr, offset=datetime.min):
        try:
            d = datetime.fromtimestamp(time.mktime(time.strptime(dateStr,'%Y-%m-%dT%H:%M:%SZ'))) - self.my_offset
        except Exception as e:
            try:
                d = datetime.fromtimestamp(dateStr)
                d = d - self.my_offset
            except Exception as e:
                d = dateutil.parser.parse(dateStr)#.astimezone(dateutil.tz.tzlocal())
        return datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)
######################################################################################################
# Creating a guid (string) for authenthication
######################################################################################################
    def _Guid(self, *args ):

        import time, random, hashlib

        """
            Generates a universally unique ID.
            Any arguments only create more randomness.
        """
        t = int( time.time() * 1000 )
        r = int( random.random()*100000000000000000 )
        try:
            a = socket.gethostbyname( socket.gethostname() )
        except:
            # if we can't get a network address, just imagine one
            a = random.random()*100000000000000000
        data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
        h = hashlib.md5()
        h.update(data)
        data = "0000" + h.hexdigest()

        return data

######################################################################################################
# return JSON from NextPVR
######################################################################################################
    def nextJson (self,url):
        from io import StringIO, BytesIO
        import gzip
        xbmc.log(url)
        request = Request(url)
        request.add_header('content-type', 'application/json')
        request.add_header('accept-encoding', 'gzip')
        json_file = urlopen(request)
        if json_file.info().get('Content-Encoding') == 'gzip':
            compressed = BytesIO(json_file.read())
            f = gzip.GzipFile(fileobj=compressed)
            reader = f.read().decode('utf-8')
        else:
            reader = json_file.read().decode('utf-8')
        next = _json.loads(reader)
        json_file.close()
        return next

######################################################################################################
# sid Login
######################################################################################################
    def sidLogin (self):
        self.sid = 'xnewa'
        self.sidLogin_json()
        if self.sid != 'xnewa':
            return
        #v5
        if sidLogin5(self) == True:
            print (self.jsid)
            self.settings.XNEWA_INTERFACE = "Version5"
            #self.settings.XNEWA_WEBCLIENT = True
        return

    def sidLogin_json (self):
        url = "http://" + self.ip + ":" + str(self.port) + '/public/Util/NPVR/Client/Instantiate'
        xbmc.log(url)
        try:
            json_file = urlopen(url)
            keys = _json.load(json_file)
            json_file.close()
            if 'sid' in keys['clientKeys']:
                sid =  keys['clientKeys']['sid']
                xbmc.log(sid)
                self.jsid = '?sid=' + sid
                salt = keys['clientKeys']['salt']
                xbmc.log(salt)
                url = "http://" + self.ip + ":" + str(self.port) + '/public/Util/NPVR/Client/Initialize/' + self._hashMe(':' + self._hashMe(self.settings.NextPVR_PIN) + ':' + salt) + self.jsid
                xbmc.log(url)
                json_file = urlopen(url)
                json_file.close()
                self.sid = sid
                self.setClient()
                self.offline = False
        except Exception as err:
            xbmc.log(str(err))
            self.offline = True
            self.settings.XNEWA_INTERFACE = 'JSON'

    def logMessage(self,msg):
        if self.settings.XNEWA_INTERFACE != 'JSON':
            logMessage_v5(self,msg)

######################################################################################################
# sid Login
######################################################################################################
    def getSid (self):
        return self.sid


    def setClient (self):
        if self.strClient == None:
            self.strClient = '&client=KNEW5'
            setting = self.getSettingJson('/Settings/Version/BuildDate')
            if setting != None:
                if 'value' in setting:
                    if setting['value'] > '161029' and self.settings.XNEWA_LIVE_SKIN:
                        self.strClient = '&client=sdl-KNEW5'

        self.client = self.strClient + self.settings.XNEWA_CLIENT + '&sid=' + self.sid


    def getSettingJson (self, key):
        setting = None
        url = "http://" + self.ip + ":" + str(self.port) + '/services/service?method=setting.get&format=json&key=' + key + '&sid=' + self.sid
        xbmc.log(url)
        try:
            json_file = urlopen(url)
            setting = _json.load(json_file)
            json_file.close()
        except Exception as err:
            xbmc.log(str(err))
        return setting

######################################################################################################
# Get user defined keys
######################################################################################################

    def tryKeyEnum(self, hash, value ):
        if self.settings.XNEWA_INTERFACE == 'JSON':
            return None
        return getKeyEnum(self, hash, value)


######################################################################################################
# Creates a (MD5) hash of a string
######################################################################################################
    def _hashMe (self, thedata):
        import hashlib
        h = hashlib.md5()
        h.update(thedata.encode('utf-8'))
        return h.hexdigest()

######################################################################################################
# Creates a byte-array with an MS representation of unicode...
######################################################################################################
    def _toMsUniCode(self, text):
        clear = str(text)
        bytes_clear=""
        for i in clear:
            if ord(i) < 128:
                bytes_clear += i
                bytes_clear += chr(0)
            else:
                bytes_clear += i

        return bytes_clear


def _WakeOnLan(ethernet_address, broadcast_address):
    import struct, socket
    try:
        if ':' in ethernet_address:
            ch = ':'
        elif '-' in ethernet_address:
            ch = '-'
        elif '.' in ethernet_address:
            ch = '.'
        else:
            ch = ''

        if ch:
            xbmc.log('sending wol ' + broadcast_address)
           # Construct a six-byte hardware address
            addr_byte = ethernet_address.split(ch)
            hw_addr = struct.pack('BBBBBB',
                int(addr_byte[0], 16),
                int(addr_byte[1], 16),
                int(addr_byte[2], 16),
                int(addr_byte[3], 16),
                int(addr_byte[4], 16),
                int(addr_byte[5], 16))

            # Build the Wake-On-LAN "Magic Packet"...
            msg = b'\xff' * 6 + hw_addr  * 16

            # ...and send it to the broadcast address using UDP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(msg, (broadcast_address, 9))
            s.close()
    except:
        import traceback
        traceback.print_exc()
        return


def urlHEAD(self,url):
    xbmc.log(url)
    try:
        host, path = urlparse(url)[1:3]    # elems [1] and [2]
        conn = http.client.HTTPConnection(host)
        conn.request('HEAD', path)
        mys = conn.getresponse().status
    except:
        mys = 404
    return mys

# locate server on subnet

def zeroConf(self):
    import socket
    import struct
    import sys

    message = 'KNEW5 looking for NextPVR'

    multicast_group = ('255.255.255.255', 16891)

    # Create the datagram socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Set a timeout so the socket does not block indefinitely when trying
    # to receive data.
    sock.settimeout(0.2)

    # Set the time-to-live for messages to 1 so they do not go past the
    # local network segment.
    ttl = struct.pack('b', 5)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:

        # Send data to the multicast group
        xbmc.log('Sending "%s"' % message)
        sent = sock.sendto(message, multicast_group)

        # Look for responses from all recipients
        while True:
            try:
                data, server = sock.recvfrom(512)
            except socket.timeout:
                xbmc.log('Timed out, no more responses')
                break
            else:
                xbmc.log(data.rstrip('\0'))
                self.ip = data.split(':')[0]
                self.port = data.split(':')[1]
                break
    finally:
        sock.close()
