######################################################################################################
# Class for connecting to a NextPVR instance
#
# Requires:     PyCrypto (for Rijnsdael Authentication)
#          Suds (for SOAP interaction)
#          PBKDF2 (RFC PBKDF2 support)
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
NEWA_WS_MANAGE_PATH = "/public/services/ManageService.asmx?WSDL"
NEWA_WS_SEARCH_PATH = "/public/services/SearchService.asmx?WSDL"
NEWA_WS_DETAIL_PATH = "/public/services/DetailService.asmx?WSDL"
NEWA_WS_GUIDE_PATH = "/public/services/GuideService.asmx?WSDL"
NEWA_WS_SCHEDULE_PATH = "/public/services/ScheduleService.asmx?WSDL"
NEWA_WS_VLC_PATH = "/public/services/VlcService.asmx?WSDL"
FANART_PATH = 'fanart'
CHANNEL_PATH = 'Channels'
SHOW_PATH = 'Shows'
GENRE_PATH = 'Genres'

Last_Error = ""
# For WS Search functions, sort and filters....
# Sort fields

import time
import _strptime
import datetime, time
from datetime import timedelta
import dateutil.parser
import tempfile
import os.path
import cPickle as pickle
import xbmc, xbmcvfs, xbmcaddon
import sys
from fix_utf8 import smartUTF8
from XNEWAGlobals import *
import urllib2
import urllib

if sys.version_info >=  (2, 7):
    import json as _json
else:
    try:
        import simplejson as _json
    except:
        import json as _json

__language__ = xbmcaddon.Addon().getLocalizedString
DATAROOT = xbmc.translatePath( 'special://profile/addon_data/%s' % xbmcaddon.Addon().getAddonInfo('id') )
CACHEROOT = os.path.join(xbmc.translatePath('special://temp'), 'x-newa')

class XNEWA_Connect:

    SORT_DATE = 0
    SORT_CHANNEL = 1
    SORT_TITLE = 2
    SORT_STATUS = 3
    # Sort order
    SORT_ASCENDING = 1
    SORT_DESCENDING = 2
    #Filter fields
    FILTER_ALL = 0
    FILTER_NONE = 1
    FILTER_PENDING = 2
    FILTER_INPROGRESS = 3
    FILTER_COMPLETED = 4
    FILTER_FAILED = 5
    FILTER_CONFLICT = 6
    FILTER_REOCURRING = 7
    FILTER_DELETED = 8
    # Detail-record types
    DETAIL_RECORDING = 1
    DETAIL_SCHEDULE = 2
    DETAIL_SHOW = 3
    # Schedule-types
    SCHEDULE_ANYTIMESLOT = 'any timeslot'
    SCHEDULE_WEEKLYTIMESLOT = 'weekly timeslot'
    SCHEDULE_DAILYTIMESLOT = 'daily timeslot'
    SCHEDULE_ONCE = 'Single'

    # Instantiation
    def __init__(self, *args, **kwargs):
        self.settings = kwargs['settings']

        self.port = self.settings.NextPVR_PORT
        self.ip = self.settings.NextPVR_HOST
        print self.ip

        import re
        m = re.search('(^127\.)|(^10\.)|(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|(^192\.168\.)', self.ip )
        if m == None:
            m = re.search('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', self.ip )
            if m != None:
                print 'Using Internet IPv4 restrictions on non-local IP'
                self.LOCAL_NEWA = False
                self.NextPVR_USEWOL = False
            else:
                try:
                    debug("Resolving hostname of: " + self.ip)
                    from socket import getaddrinfo
                    temp = getaddrinfo(self.ip, self.port)
                    print temp
                    ipv6 = temp[0][4][0]
                    m = re.search('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', ipv6 )
                    if m != None:
                        #IPv4
                        m = re.search('(^127\.)|(^10\.)|(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|(^192\.168\.)', ipv6 )
                        if m == None:
                            print 'Using Internet IPv4 restrictions'
                            self.LOCAL_NEWA = False
                            self.NextPVR_USEWOL = False
                    else:
                        if ipv6 == self.ip:
                            self.ip = '[' + urllib.unquote(self.ip) + ']'
                        print self.ip
                        if ipv6.startswith ('fd') or ipv6.startswith ('fe80') or ipv6.replace(':','') == '1':
                            print 'Local IPv6'
                        else:
                            print 'Using Internet IPv6 restrictions'
                            self.LOCAL_NEWA = False
                            self.NextPVR_USEWOL = False
                    #self.ip = temp
                except:
                    self.offline = True
                    debug("Error instantiating (cannot resolve host-name)")
                    raise Exception, "cannot resolve host-name."

        self.vlc_url = None
        self.vlc_process = -1
        self.miniEPG = datetime.datetime.max
        self.interface = self.settings.XNEWA_INTERFACE
        self.channels = None
        print self.miniEPG
        self.update_time = 9223372036854775807
        self.isdst = time.localtime(time.time()).tm_isdst
        if self.isdst == 1:
            print 'atz ' + str(time.altzone)
            self.my_offset = timedelta(seconds=time.altzone)
        else:
            print 'tz ' + str(time.timezone)
            self.my_offset = timedelta(seconds=time.timezone)

        if kwargs.has_key('offline'):
            self.offline = kwargs['offline']
        else:
            self.offline = False
        self.changedRecordings = False
        if not os.path.exists(CACHEROOT):
            os.makedirs(CACHEROOT)

        self.getfilesystemencoding = sys.getfilesystemencoding()
        if self.getfilesystemencoding is None:
            self.getfilesystemencoding = 'utf-8'
        print self.getfilesystemencoding
        if  time.localtime(time.time()).tm_isdst != 0:
            self.dst_offset = timedelta(seconds=time.timezone) - timedelta(seconds=time.altzone)
            print 'DST on'
        else:
            self.dst_offset = timedelta(0)
            print 'DST off'


        from suds.cache import ObjectCache
        self.objCache = ObjectCache()
        self.objCache.setduration(hours=4)

        self.manage_client = None
        self.search_client = None
        self.detail_client = None
        self.guide_client = None
        self.schedule_client = None
        self.defaultSchedule = None
        self.methodTranscode = None

    ######################################################################################################
    # checking to see if NEWA is responding
    ######################################################################################################

        self.sid = None
        self.client = None
        self.strClient = None

        self.AreYouThere(self.settings.usewol(), self.settings.NextPVR_MAC, self.settings.NextPVR_BROADCAST)

        if self.sid == None:
            self.sidLogin()
            if self.sid == None:
                self.offline = True

        self.mycache = CACHEROOT

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
        print 'init fanart'
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
                            import xbmcgui
                            WolProgress = xbmcgui.DialogProgress()
                            WolProgress.create("%s WOL" % smartUTF8(__language__(30152)), '%s %s' % (smartUTF8(__language__(30153)), self.ip), smartUTF8(__language__(30139)))
                        completed = 100 * count/ int(self.settings.NextPVR_CONTACTS)
                        WolProgress.update(completed)
                        print 'sending wol ' + mac + ' ' + str(count)
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
        if response.has_key('result'):
            channels = [x['channel'] for x in response['result']['channels']]
        else:
             channels = None
        return channels

######################################################################################################
# Starting streaming by vlc schedule oid
######################################################################################################
    def startVlcFileByScheduleOID(self, userid, password, scheduleOID):

        bitrate = ['128', '256', '512', 'LAN', 'HD-2K', 'HD-4K', 'HD-8K' ]
        size = [320,480, 720]

        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/StreamByScheduleOID/' + str(scheduleOID) + self.jsid  + '&strmVideoSize=' + str(size.index(self.settings.VLC_VIDEO_SIZE)) + '&strmBitRate=' + str(bitrate.index(self.settings.VLC_VIDEO_BITRATE)) + '&strmAudioBitrate=' + str(self.settings.VLC_AUDIO_BITRATE)
        print url
        json_file = urllib2.urlopen(url)
        JSONVlcObject = _json.load(json_file)
        json_file.close()

        if JSONVlcObject['JSONVlcObject']['rtn']['Error'] == False:
            vlcObject = JSONVlcObject['JSONVlcObject']['VLC_Obj']
            print vlcObject
            self.vlc_url = vlcObject['StreamLocation']
            self.vlc_process = vlcObject['ProcessId']
            return True
        else:
            print JSONVlcObject['JSONVlcObject']['rtn']['Message']
            return False



######################################################################################################
# Starting streaming by vlc event oid
######################################################################################################
    def startVlcFileByEPGEventOID(self, userid, password, eventOID):

        bitrate = ['128', '256', '512', 'LAN', 'HD-2K', 'HD-4K', 'HD-8K' ]
        size = [320,480, 720]
        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/StreamByEPGOID/' + str(eventOID) + self.jsid  + '&strmVideoSize=' + str(size.index(self.settings.VLC_VIDEO_SIZE)) + '&strmBitRate=' + str(bitrate.index(self.settings.VLC_VIDEO_BITRATE)) + '&strmAudioBitrate=' + str(self.settings.VLC_AUDIO_BITRATE)

        print url

        json_file = urllib2.urlopen(url)
        JSONVlcObject = _json.load(json_file)
        json_file.close()

        if JSONVlcObject['JSONVlcObject']['rtn']['Error'] == False:
            vlcObject = JSONVlcObject['JSONVlcObject']['VLC_Obj']
            print vlcObject
            self.vlc_url = vlcObject['StreamLocation']
            self.vlc_process = vlcObject['ProcessId']
            return True
        else:
            print JSONVlcObject['JSONVlcObject']['rtn']['Message']
            return False

######################################################################################################
# Starting streaming by vlc
######################################################################################################
    def startVlcLiveStreamByChannelNumberObject(self, userid, password, channelNum):

        bitrate = ['128', '256', '512', 'LAN', 'HD-2K', 'HD-4K', 'HD-8K' ]
        size = [320,480, 720]
        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/Dump/StreamByChannel/Number/' + str(channelNum) + self.jsid
        print url

        json_file = urllib2.urlopen(url)
        JSONVlcObject = _json.load(json_file)
        json_file.close()

        if JSONVlcObject['JSONVlcObject']['rtn']['Error'] == False:
            vlcObject = JSONVlcObject['JSONVlcObject']['VLC_Obj']
            print vlcObject
            self.vlc_url = vlcObject['StreamLocation']
            self.vlc_process = vlcObject['ProcessId']
            return True
        else:
            print JSONVlcObject['JSONVlcObject']['rtn']['Message']
            return False



######################################################################################################
# Stop streaming by vlc
######################################################################################################
    def stopVlcStreamProcess(self, userid, password):

        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/KillVLC/' + str(self.vlc_process) + self.jsid
        print url
        json_file = urllib2.urlopen(url)
        JSONVlcObject = _json.load(json_file)
        json_file.close()
        print JSONVlcObject

        self.vlc_process = -1
        return True


######################################################################################################
# Send vlc heartbeat
######################################################################################################
    def sendVlcHeartbeat(self, userid, password):
        url = "http://" + self.ip + ":" + str(self.port) + '/public/VLCService/sendHeartBeat/' + str(self.vlc_process)
        print url
        json_file = urllib2.urlopen(url)
        print json_file.getcode()
        json_file.close()
        return True


######################################################################################################
# transcoding
######################################################################################################

    def startTranscodeLiveStreamByChannelNumber(self, channelNum):
        self.methodTranscode = 'channel'
        self.getTranscodeStatus()
        url = "http://" + self.ip + ":" + str(self.port) + '/services/services?method=channel.transcode.initiate&format=json&profile=' + self.settings.TRANSCODE_PROFILE + '&channel=' + str(channelNum) + '&sid=' + self.sid
        print url
        try:
            xml_file = urllib2.urlopen(url)
            xml_return = xml_file.read()
            if 'stat="ok"' not in xml_return:
                print xml_return
        except Exception, err:
            print err

    def startTranscodeRecording(self, recording_oid):
        self.methodTranscode = 'recording'
        self.getTranscodeStatus()
        url = "http://" + self.ip + ":" + str(self.port) + '/services/services?method=recording.transcode.initiate&profile=' + self.settings.TRANSCODE_PROFILE + '&recording_id=' + str(recording_oid) + '&sid=' + self.sid
        print url
        try:
            xml_file = urllib2.urlopen(url)
            xml_return = xml_file.read()
            if 'stat="ok"' not in xml_return:
                print xml_return
        except Exception, err:
            print err


    def sendTranscodeHeartbeat(self):
        url = "http://" + self.ip + ":" + str(self.port) + '/services/services?method=' + self.methodTranscode + '.transcode.lease&sid=' + self.sid
        print url
        try:
            request = urllib2.Request(url)
            xml_file = urllib2.urlopen(request, timeout=4)
            xml_return = xml_file.read()
            if 'stat="ok"' not in xml_return:
                xbmc.player.stop()
                print xml_return
        except Exception, err:
            print err


    def sendTranscodeStop(self):
        url = "http://" + self.ip + ":" + str(self.port) + '/services/services?method=' + self.methodTranscode + '.transcode.stop&sid=' + self.sid
        print url
        try:
            xml_file = urllib2.urlopen(url)
            xml_return = xml_file.read()
            if 'stat="ok"' not in xml_return:
                print xml_return
        except Exception, err:
            print err


    def getTranscodeStatus(self):
        url = "http://" + self.ip + ":" + str(self.port) + '/services/services?method=' + self.methodTranscode + '.transcode.status&format=json&sid=' + self.sid
        print url
        retval = 0
        try:
            request = urllib2.Request(url)
            json_file = urllib2.urlopen(request,timeout=.25)
            JSONTranscodeObject = _json.load(json_file)
            json_file.close()
            if  JSONTranscodeObject.has_key('percentage'):
                retval = JSONTranscodeObject['percentage']
            else:
                print JSONTranscodeObject
        except Exception, err:
            print err
        print retval
        return retval





######################################################################################################
# Retrieving XMLInfo information and returning in dictionary
######################################################################################################
    def GetNextPVRInfo(self, userid, password,channels=True):
        dic = {}
        if self.settings.XNEWA_WEBCLIENT != True:
            from xml.dom import minidom
            print 'XML info'
            print datetime.datetime.now()
            address = "http://" + self.ip + ":" + str(self.port) + NEWA_XMLINFO_PATH
            print address
            website = urllib2.urlopen(address)
            website_html = website.read()

            dom = minidom.parseString(website_html)
            #dom = None
            if dom != None:
                ret = self._getdictfromdom(dom, "Directory")
                dic['directory'] = ret
                print ret
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
                print datetime.datetime.now()
            else:
                dic['directory'] = None
        if channels == True:
            # We also get, and cache, the channel data
            self.channels = self.getChannelList(userid, password)
            self.channelGroups = self.getChannelGroupList(userid, password)
            self.setChannelGroups()
            self.RecDirs = self.getRecDirList(userid, password)
            self.genresColours = self.getEPGGenres(userid, password)
        print 'XML Info end'
        return dic

######################################################################################################
# Retrieving last update time 3.4.x
######################################################################################################
    def getRecordingUpdate(self):
        #print datetime.datetime.now()
        if self.settings.XNEWA_INTERFACE == 'XML' or True:
            url  = "http://" + self.ip + ":" + str(self.port) + '/service?method=recording.lastupdated&sid=' + self.sid
            print url
            try:
                import xml.etree.ElementTree as ET
                request = urllib2.Request(url, headers={"Accept" : "application/xml"})
                u = urllib2.urlopen(request, timeout=10)
                tree = ET.parse(u)
                root = tree.getroot()
                if root.attrib['stat'] == 'ok':
                    self.update_time =  int(root.find('last_update').text)
                    print datetime.datetime.fromtimestamp(self.update_time).strftime('%Y-%m-%d %H:%M:%S')
                elif root.attrib['stat'] == 'fail':
                    err = root.find('err')
                    if err.attrib['code'] == '8':
                        print err.attrib['msg']
                        if self.settings.LOCAL_NEWA == False or True:
                            self.sid = None
                            print 'Clear SID'
            except Exception, err:
                print err
        else:
            url  = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/Get/LastRecordingListChangeTime?sid=' + self.sid
            print url
            try:
                request = urllib2.Request(url, headers={"Accept" : "application/json"})
                response = urllib2.urlopen(request, timeout=5)
                results = response.read()
                changed = _json.loads(results)
                self.update_time = int(changed['RecordingListChangeTime']['Time'])
                print datetime.datetime.fromtimestamp(self.update_time).strftime('%Y-%m-%d %H:%M:%S')
            except Exception, err:
                print err
        return self.update_time

    def checkCache(self,cached):
        if os.path.isfile(os.path.join(self.mycache,cached)) == True:
            if self.offline == True:
                return True
            if self.update_time != 9223372036854775807:
                update_time = self.update_time
                self.getRecordingUpdate()
                if update_time == self.update_time:
                    if self.update_time <= int(os.path.getmtime(os.path.join(self.mycache,cached))):
                        return True
                return False
            ft =  datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(self.mycache,cached)))
            if ft + timedelta(hours=2) > datetime.datetime.now():
                return True

        return False

    def cleanCache(self,spec):
        import glob
        print "clean cache for " + spec
        fileNames = glob.glob(os.path.join(self.mycache,spec))
        for file in fileNames:
            os.remove(file)
        return True

    def cleanCoverCache(self):
        import glob
        print "clean covers"
        fileNames = glob.glob(os.path.join(self.cached_showPath,'*.jpg'))
        for file in fileNames:
            os.remove(file)
        return True

    def cleanOldCache(self,spec):
        if self.offline == True:
            return True
        import glob
        import os
        print "clean old files for " + spec
        cnt = 0
        fileNames = glob.glob(os.path.join(self.mycache,spec))
        for file in fileNames:
            ft =  datetime.datetime.fromtimestamp(os.path.getmtime(file))
            if ft + timedelta(hours=2) < datetime.datetime.now():
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

        if sortTitle:
            sortDate = True

        print "getRecordingsSummary json start"

        #import xbmcgui

        try:

            if self.defaultSchedule == None:
                self.getDefaultSchedule()

            import copy
            recObj = copy.deepcopy(self.defaultSchedule)
            if self.settings.XNEWA_COLOURS != None:
                if 'red' in self.settings.XNEWA_COLOURS :
                    print 'is red'
                    recObj['recColorRed'] = True
                else:
                    recObj['recColorRed'] = False
                if 'green' in self.settings.XNEWA_COLOURS :
                    print 'is green'
                    recObj['recColorGreen'] = True
                else:
                    recObj['recColorGreen'] = False
                if 'yellow' in self.settings.XNEWA_COLOURS :
                    recObj['recColorYellow'] = True
                else:
                    recObj['recColorYellow'] = False
                if 'blue' in self.settings.XNEWA_COLOURS :
                    print 'is blue'
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
            print url
            recObj = _json.dumps(recObj)
            print recObj
            request = urllib2.Request(url, recObj)
            request.add_header('Content-Type', 'application/json')
            try:
                print 'Posting to %s' % url
                response = urllib2.urlopen(request)
                print "response from request was %s" % response.code
                results = response.read()
                summaryResults = _json.loads(results)
                #print summaryResults
                retArr = []
                for summary in summaryResults['RecordingsSummary']['summaryArray']:
                    retArr.append(self._sum2dict_json(summary))
                print response.code
            except urllib2.URLError, e:
                print 'error during request: %s' % e.code
                if e.code == 405:
                    return None
        except Exception, err:
            print err
        print "getRecordingsSummary json end"
        self.myCachedPickle(retArr,cached)
        return retArr

######################################################################################################
# Translating a (soap)1 recordingobject into a dictionary object...
######################################################################################################
    def _sum2dict(self, summary):
        theDict = {}
        #todo fix suds processing
        if summary  is not None:
            theDict['title'] = summary.Name.encode('utf-8')
            theDict['start'] = datetime.datetime.fromtimestamp(time.mktime(time.strptime(str(summary.StartTime),'%Y-%m-%d %H:%M:%S')))
            theDict['count'] = summary.Count
        return theDict
######################################################################################################
# Translating a (json) recordingobject into a dictionary object...
######################################################################################################
    def _sum2dict_json(self, summary):
        theDict = {}
        #todo fix suds processing
        if summary  is not None:
            theDict['title'] = summary['Name'].encode('utf-8')
            theDict['start'] =  dateutil.parser.parse(summary['StartTime']).astimezone(dateutil.tz.tzlocal())
            theDict['count'] = summary['Count']
        return theDict

######################################################################################################
# Retrieves a list of channels...
######################################################################################################
    def getChannelList(self, userid, password):
        cached = 'channel.List'
        if self.checkCache(cached):
            dic = self.myCachedPickleLoad(cached)
            if dic.has_key('0'):
                print "getChannelList cached end"
                return dic
        if self.settings.XNEWA_INTERFACE != 'SOAP':
            dic = self.getChannelList_json()
            if dic != None:
                self.myCachedPickle(dic,cached)
                return dic

        print "getChannelList start"

        import suds.client
        if self.search_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SEARCH_PATH
            self.search_client = suds.client.Client(url,cache=self.objCache)
        client = self.search_client
        authObj = client.factory.create('webServiceAuthentication')
        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)
        client.set_options(soapheaders=authObj)
        #import logging
        #logging.basicConfig(level=logging.INFO)
        #logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)
        ret_soap = client.service.getChannelListObject(soapheaders=authObj)

        dic = {}
        import imghdr
        import glob

        dic['0']= (u"Unknown",'0')
        for chan in ret_soap.anyType:
            temp = chan.split('!')
            dic[temp[2]] = ( temp[1].encode('utf-8'),temp[0] )
            try:
                output = os.path.join(self.cached_channelPath,temp[1].encode('utf-8')+".*")
                icon = glob.glob(output)
                if not icon:
                    url = self.getURL()+'/'+temp[3]
                    output = os.path.join(self.channelPath,"unknown")
                    urllib.urlretrieve (url,output)
                    img = imghdr.what(os.path.join(self.cached_channelPath,"unknown"))
                    if img == "png":
                        os.rename(os.path.join(self.cached_channelPath,"unknown"), os.path.join(self.cached_channelPath,temp[1].encode('utf-8')+".png"))
                    elif img == "jpeg":
                        os.rename(os.path.join(self.cached_channelPath,"unknown"), os.path.join(self.cached_channelPath,temp[1].encode('utf-8')+".jpg"))
                    elif img is None:
                        print temp[1].encode('utf-8') + " is unknown"
                    else:
                        print temp[1].encode('utf-8') + " Type " + img
                else:
                    #print "Found " + icon[0]
                    pass
            except:
                print chan + " Error"
                pass
        print "getChannelList end"
        self.myCachedPickle(dic,cached)
        return dic


    def getChannelList_json(self):

        print "getChannelList JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/GuideService/Channels' + self.jsid
        dic = {}
        import imghdr
        import glob
        dic['0']= (u"Unknown",'0')
        import xbmcgui
        myDlg = None
        try:
            channelList = self.nextJson(url)
            cnt = 0
            for channel in channelList['channelsJSONObject']['Channels']:
                chan = channel['channel']
                if chan['channelIcon'] != '':
                    cnt= cnt+1
            if cnt > 0:
                icons = glob.glob(os.path.join(self.cached_channelPath,'*.*'))
                if cnt > len(icons) + 20:
                    myDlg = xbmcgui.DialogProgress()
                    myDlg.create(smartUTF8(__language__(30154)), smartUTF8(__language__(30139)))
                cnt = 0
            for channel in channelList['channelsJSONObject']['Channels']:
                chan = channel['channel']
                if myDlg != None:
                    completed = 100 * cnt/len(channelList['channelsJSONObject']['Channels'])
                    cnt = cnt + 1
                    myDlg.update(completed, str(chan['channelName'].encode('utf-8')))
                if chan.has_key('channelNumber'):
                    dic[str(chan['channelOID'])] = ( chan['channelName'].encode('utf-8'),str(chan['channelNumber']),str(chan['channelMinor']) )
                elif chan.has_key('channelMinor'):
                    dic[str(chan['channelOID'])] = ( chan['channelName'].encode('utf-8'),str(chan['channelNum']),str(chan['channelMinor']) )
                else:
                    dic[str(chan['channelOID'])] = ( chan['channelName'].encode('utf-8'),str(chan['channelNum']),'0' )
                #print dic[str(chan['channelOID'])]
                if chan['channelIcon'] != '':
                    try:
                        import string
                        valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
                        safename = ''.join(ch for ch in chan['channelName'] if ch in valid_chars)

                        output = os.path.join(self.channelPath,safename.encode('utf-8')+".*")
                        icon = glob.glob(output)
                        if not icon:
                            url = self.getURL()+'/'+chan['channelIcon']
                            output = os.path.join(self.channelPath,"unknown")
                            urllib.urlretrieve (url,output)
                            img = imghdr.what(os.path.join(self.channelPath,"unknown"))
                            if img == "png":
                                os.rename(os.path.join(self.channelPath,"unknown"), os.path.join(self.channelPath,safename.encode('utf-8')+".png"))
                            elif img == "jpeg":
                                os.rename(os.path.join(self.channelPath,"unknown"), os.path.join(self.channelPath,safename.encode('utf-8')+".jpg"))
                            elif img is None:
                                print safename.encode('utf-8') + " is unknown"
                            else:
                                print safename.encode('utf-8') + " Type " + img
                        else:
                            #print "Found " + icon[0]
                            pass
                    except:
                        print str(chan['channelNum']) + " Error"
                        pass
                else:
                    print channel
        except:
            print 'getChannelList JSON error'
            dic = None
        print "getChannelList JSON end"
        if myDlg != None:
            myDlg.close()
        return dic

######################################################################################################
# Sets the librar playback position
######################################################################################################

    def setLibraryPlaybackPosition(self,filename, position, duration):

        print "setLibraryPlaybackPosition start"

        if int(duration) < 0:
            print "Should I bother with zero"
            return True

        if int(duration) == 0 and int(position) != 0:
            duration = position + 30

        import re
        m = re.search('^.+\.(?i)(mpeg|mpg|m2v|avi|ty|avs|ogm|mp4|mov|m2ts|wmv|cdg|iso|rm|dvr-ms|ts|mkv|vob|divx|flv|ratDVD|m4v|3gp|rmvb|wtv|bdmv)$', filename)
        if m == None:
            print "Not a video file"
            return True
        import os
        url = "http://" + self.ip + ":" + str(self.port) + '/public/detailsservice/set/PlaybackPosition' + self.jsid  + '&fname=' + urllib.quote(os.path.basename(filename),'\\/:%.?=;')  + '&dur=' + str(int(duration)) +'&pos=' +str(int(position))
        print url
        try:
            json_file = urllib2.urlopen(url)
            jsonPlaybackPosition = _json.load(json_file)
            json_file.close()
            print jsonPlaybackPosition
            if jsonPlaybackPosition.has_key('url'):
                jsonPlaybackPositio['l']
            return True
        except Exception, err:
            print err
            return False


######################################################################################################
# Sets the playback position
######################################################################################################
    def setPlaybackPositionObject(self, userid, password, rec, position, duration):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            return self.setLibraryPlaybackPosition(rec["filename"], int(position),int(duration))

        import suds.client

        print "setPlaybackPositiontObject start"

        if int(duration) <= 0 and int(position) == 0:
            print "Not bothering with zero"
            return True

        if int(duration) == 0 and int(position) != 0:
            duration = position + 30

        url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_DETAIL_PATH

        if self.detail_client==None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_DETAIL_PATH
            self.detail_client = suds.client.Client(url,cache=self.objCache)


        client = self.detail_client

        authObj = client.factory.create('webServiceAuthentication')

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)

        client.set_options(soapheaders=authObj)

        ret_soap = client.service.setPlaybackPositiontObject(rec["recording_oid"],rec["filename"],
            int(position), int(duration),soapheaders=authObj)
        print "setPlaybackPositiontObject end"
        if ret_soap.webServiceEPGEventObjects.webServiceReturn.Message is not None:
            print ret_soap.webServiceEPGEventObjects.webServiceReturn.Message
            last_Error = ret_soap.webServiceEPGEventObjects.webServiceReturn.Message
        return (not ret_soap.webServiceEPGEventObjects.webServiceReturn.Error)

######################################################################################################
# Retrieves a list of channelGroups...
######################################################################################################
    def getChannelGroupList(self, userid, password):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            dic = self.getChannelGroupList_json()
            if dic != None:
                return dic

        import suds.client
        print "getChannelGroupList start"

        if self.guide_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_GUIDE_PATH
            self.guide_client = suds.client.Client(url,cache=self.objCache)

        client = self.guide_client

        authObj = client.factory.create('webServiceAuthentication')

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)

        client.set_options(soapheaders=authObj)
        #import logging
        #logging.basicConfig(level=logging.INFO)
        #logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)

        groups = []
        groups.append('All Channels')
        try:
            ret_soap = client.service.getChannelGroupsObject(soapheaders=authObj)
            print ret_soap
            if len(ret_soap) > 0:
                for group in ret_soap.anyType:
                    if group != 'All Channels':
                        groups.append(group.encode('utf-8'))
        except:
            print 'channel group error'
            pass

        print "getChannelGroupList end"
        return groups

    def getChannelGroupList_json(self):

        print "getChannelGroupList JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/GuideService/ChannelGroups' + self.jsid
        groups = []
        groups.append('All Channels')

        try:
            json_file = urllib2.urlopen(url)
            epgGenres = _json.load(json_file)
            json_file.close()
            for group in epgGenres['channelGroupJSONObject']['ChannelGroups']:
                if group != 'All Channels':
                    groups.append(group.encode('utf-8'))
        except:
            print 'getChannelGroupList JSON error'
            groups = None
        print "getChannelGroupList JSON end"
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
                if setting.attrib.has_key('id'):
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

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            dic = self.getEPGGenres_json()
            if dic != None:
                return dic

        import suds.client

        print "getEPGGenres start"

        url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_GUIDE_PATH

        if self.guide_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_GUIDE_PATH
            self.guide_client = suds.client.Client(url,cache=self.objCache)

        client = self.guide_client

        authObj = client.factory.create('webServiceAuthentication')

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)

        client.set_options(soapheaders=authObj)

        dic = {}
        dic['xnewa'] = 0
        try:
            ret_soap = client.service.getGenreListObject(soapheaders=authObj)
            if len(ret_soap) > 0:
                for group in ret_soap.anyType:
                    try:
                        temp = group.split('|')
                        dic[temp[0]] = int(temp[1], 16)
                    except:
                        pass
        except:
            print 'EPG Genres error'
        print "getEPG Genres end"
        return dic

    def getEPGGenres_json(self):

        print "getEPGGenres JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/GuideService/Genres' + self.jsid

        dic = {}
        dic['xnewa'] = 0
        try:
            json_file = urllib2.urlopen(url)
            epgGenres = _json.load(json_file)
            json_file.close()
            for genre in epgGenres['genreJSONObject']['genres']:
                try:
                    if int(genre['genre']['color'],16) !=0:
                        dic[genre['genre']['name']] = int(genre['genre']['color'],16)
                except:
                    pass
        except:
            print 'EPG Genres JSON error'
            dic = None
        print "getEPG Genres JSON end"
        return dic

######################################################################################################
# Retrieves a list of recDir...
######################################################################################################
    def getRecDirList(self, userid, password):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            return self.getRecDirList_json()

        import suds.client
        print "getRecDirList start"

        if self.schedule_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SCHEDULE_PATH
            self.schedule_client = suds.client.Client(url,cache=self.objCache)
        client = self.schedule_client

        authObj = client.factory.create('webServiceAuthentication')
        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)
        client.set_options(soapheaders=authObj)
        ret_soap = client.service.getRecDirObject(soapheaders=authObj)

        groups = []
        groups.append(ret_soap.DefaultRecordingDirectory.RecDirName.encode('utf-8'))
        if len(ret_soap.ExtraRecordingDirectories) != 0:
            for dirs in ret_soap.ExtraRecordingDirectories.webServiceRecordingDirectory:
                groups.append(dirs.RecDirName.encode('utf-8'))
        return groups

    def getRecDirList_json(self):

        print "getRecDirList JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ScheduleService/Get/RecDirs' + self.jsid
        dirs = {}
        try:
            json_file = urllib2.urlopen(url)
            allDirs = _json.load(json_file)
            json_file.close()
            dirs[allDirs['DefRecDir']['RecDirName']] = allDirs['DefRecDir']['RecDir']
            for dir in allDirs['dirArray']:
                if dir['RecDirName'] != 'Default':
                    try:
                        dirs[dir['RecDirName'].encode('utf-8')] = dir['RecDir']
                    except:
                        print 'Duplicate of ' + dir['RecDirName'].encode('utf-8')
        except:
            print 'getRecDirList JSON error'
            dirs = None
        print dirs
        print "getRecDirList JSON end"
        return dirs

######################################################################################################
    def getDetails(self, userid, password, oid, type, fetchArt):

        print 'Details ' + type
        if self.settings.XNEWA_INTERFACE != 'SOAP':
            if self.channels == None:
                self.channels = self.getChannelList(userid, password)
            if type=="E" or type=='P':
                url = "http://" + self.ip + ":" + str(self.port) + '/public/DetailsService/' + str(oid) + self.jsid
                print url
                json_file = urllib2.urlopen(url)
                detailsService = _json.load(json_file)
                json_file.close()
                return self._detail2array_json(detailsService,fetchArt)
            elif type=="R":
                url = "http://" + self.ip + ":" + str(self.port) + '/public/DetailsSchdService/' + str(oid) + self.jsid
                print url
                json_file = urllib2.urlopen(url)
                #json_file = open('c:/temp/36525000.json')
                detailsService = _json.load(json_file)
                json_file.close()
                return self._detail2array_json(detailsService,fetchArt)
            elif type=="F":
                url = "http://" + self.ip + ":" + str(self.port) + '/public/DetailsRecurrService/' + str(oid) + self.jsid
                print url
                json_file = urllib2.urlopen(url)
                #json_file = open('c:/temp/36525000.json')
                detailsService = _json.load(json_file)
                json_file.close()
                return self._recurr2dict(detailsService['epgEventJSONObject'])


        import suds.client

        if self.detail_client==None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_DETAIL_PATH
            self.detail_client = suds.client.Client(url,cache=self.objCache)

        client = self.detail_client

        authObj = client.factory.create('webServiceAuthentication')

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)

        client.set_options(soapheaders=authObj)
        #todo fix types
        if type=="F":
            ret_soap = client.service.getwebServiceEPGEventObjectByRecurringOID(oid, soapheaders=authObj)
            return self._rec2dict2(ret_soap[0] )
        elif type=="P" or type=="E":
            ret_soap = client.service.getwebServiceEPGEventObjectByEPGEventOID(oid, soapheaders=authObj)
        else:
            ret_soap = client.service.getwebServiceEPGEventObjectByScheduleOID(oid, soapheaders=authObj)

        return self._detail2array(ret_soap,fetchArt)

######################################################################################################
    def archiveRecording(self, userid, password, oid, directory):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            return self.archiveRecording_json(oid,directory)

        import suds.client


        if self.manage_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH
            self.manage_client = suds.client.Client(url,cache=self.objCache)
        client = self.manage_client

        authObj = client.factory.create('webServiceAuthentication')

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)

        client.set_options(soapheaders=authObj)

        if directory != "Default":
            recDirId = directory
        else:
            recDirId = directory

        #import logging
        #logging.basicConfig(level=logging.INFO)
        #logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)

        ret_soap = client.service.archiveRecording(oid, recDirId, soapheaders=authObj)
        if ret_soap.Error == True:
            print ret_soap.Message
        return not ret_soap.Error

    def archiveRecording_json(self, oid, directory):

        print "archiveRecording JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/ArchiveRecording/' + str(oid) + self.jsid  + '&recdir=' + urllib.quote_plus(directory)
        print url
        try:
            json_file = urllib2.urlopen(url)
        except urllib2.URLError, e:
                print 'archiveRecording  JSON error'
                print e.code
                return False
        else:
            archive = _json.load(json_file)
            json_file.close()
            print archive
        print "archiveRecording JSON end"
        return True

######################################################################################################
    def getGuideInfo(self, userid, password, dtTimeStart, dtTimeEnd, group):

        print "getGuideInfo start "
        #print dtTimeStart
        #print dtTimeEnd
        timeStart = dtTimeStart.strftime("%Y-%m-%dT%H:%M:00")
        timeEnd = dtTimeEnd.strftime("%Y-%m-%dT%H:%M:00")
        cachedCount = self.cleanOldCache('guideListing-*.p')
        if cachedCount > 0:
            cached = 'guideListing-' + dtTimeStart.strftime("%Y-%m-%dT%H") + '.p'
            #print cached + ' from ' + str(cachedCount)
            if self.checkCache(cached):
                retArr = self.myCachedPickleLoad(cached)
                print "getGuideInfo cached end"
                return retArr
            print 'Try previous hour'
            lastHour = dtTimeStart - timedelta(hours=1)
            cached = 'guideListing-' + lastHour.strftime("%Y-%m-%dT%H")  + '.p'
            print cached
            if self.checkCache(cached):
                retArr = self.myCachedPickleLoad(cached)
                print "getGuideInfo cached last hour end"
                return retArr



        if group is not None:
            if group not in self.channelGroups:
                print group + " group not found"
                caseGroup = None
                for groups in self.channelGroups:
                    if groups.lower() == group.lower():
                        print groups + " group found"
                        caseGroup = groups
                group = caseGroup
            elif group == 'All' or group == 'All Channels':
                group = None

        cached = 'guideListing-' + dtTimeStart.strftime("%Y-%m-%dT%H") + '.p'
        print self.settings.XNEWA_INTERFACE

        if self.settings.XNEWA_INTERFACE == 'XML' or self.settings.XNEWA_INTERFACE == 'Short' or self.settings.XNEWA_WEBCLIENT == True:
            import calendar
            if self.settings.XNEWA_INTERFACE == 'XML':
                url = "http://" + self.ip + ":" + str(self.port) + '/services?method=channel.listings.current&sid='+ self.sid + '&start=' + str(int(calendar.timegm(dtTimeStart.timetuple()))) + '&end=' + str(int(calendar.timegm(dtTimeEnd.timetuple())))
            else:
                url = "http://" + self.ip + ":" + str(self.port) + '/services?method=channel.listings.current&sid=' + self.sid
            print url
            retGuide = self._progs2array_xml(url)
        elif self.settings.XNEWA_INTERFACE == 'JSON':
            import calendar
            #url = "http://" + self.ip + ":" + str(self.port) + '/public/guideservice/listing?stime=' + dtTimeStart.strftime("%Y-%m-%dT%H:%M") + '&etime=' + dtTimeEnd.strftime("%Y-%m-%dT%H:%M")
            url = "http://" + self.ip + ":" + str(self.port) + '/public/guideservice/listing' + self.jsid + '&stime=' + str(int(calendar.timegm(dtTimeStart.timetuple()))) + '&etime=' + str(int(calendar.timegm(dtTimeEnd.timetuple()))-1)
            if group != None:
                url = url + '&chnlgroup=' + group.replace(' ','+')
            retGuide = self._progs2array_json(url)
        else:
            import suds.client
            if self.guide_client == None:
                url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_GUIDE_PATH
                self.guide_client = suds.client.Client(url,cache=self.objCache)

            client = self.guide_client

            authObj = client.factory.create('webServiceAuthentication')

            # Fill authentication object
            authObj = self._AddAuthentication(authObj, userid, password)

            client.set_options(soapheaders=authObj)
            ret_soap = client.service.getGuideObject( timeStart, timeEnd, channelGroup=group, soapheaders=authObj)
            retGuide = self._progs2array(ret_soap)
        self.myCachedPickle(retGuide,cached)
        print "getGuideInfo end"
        return retGuide

######################################################################################################
    def getUpcomingRecordings(self, userid, password, amount=0):

        cached = 'upcomingRecordings-' + str(amount) + '.p'
        if self.checkCache(cached):
          retArr = self.myCachedPickleLoad(cached)
          return retArr

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            retArr = self.getUpcomingRecordings_json(amount)
            self.myCachedPickle(retArr,cached)
            return retArr

        import suds.client

        if self.manage_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH
            self.manage_client = suds.client.Client(url,cache=self.objCache)
        client = self.manage_client

        authObj = client.factory.create('webServiceAuthentication')
        sortObj = client.factory.create('recordingsSort')
        fltrObj = client.factory.create('recordingsFilter')

        # Figure out the sorting....
        sortObj.datetimeSortSeq = 1
        sortObj.channelSortSeq = 4
        sortObj.titleSortSeq = 3
        sortObj.statusSortSeq = 2
        sortObj.datetimeDecending = 0
        sortObj.channelDecending = 0
        sortObj.titleDecending = 0
        sortObj.statusDecending = 0
        # Then the filtering....
        fltrObj.All = 0
        setattr(fltrObj, "None", 0)
        fltrObj.Pending = 1
        fltrObj.InProgress = 1
        fltrObj.Completed = 0
        fltrObj.Failed = 0
        fltrObj.Conflict = 1
        fltrObj.Recurring = 0
        fltrObj.Deleted = 0

        fltrObj.FilterByName = False
        fltrObj.NameFilterCaseSensitive = False

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)
        client.set_options(soapheaders=authObj)
        if amount == 0:
            ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)
        else:
            ret_soap = client.service.getSortedFilteredManageListObjectLimitResults(sortObj, fltrObj, amount, soapheaders=authObj)
        retArr = self._recs2array(ret_soap)
        self.myCachedPickle(retArr,cached)
        return retArr

    def getUpcomingRecordings_json(self, amount=0):

        print "getUpcomingRecordings JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/Get/SortedFilteredList' + self.jsid
        print url
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
        print sortFilterObj
        try:
            request = urllib2.Request(url, sortFilterObj)
            request.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(request)
            results = response.read()
            upcomingResults = _json.loads(results)
            for epgEvent in  upcomingResults['ManageResults']['EPGEvents']:
                theDict = self._rec2dict1_json(epgEvent)
                if theDict != None:
                    retArr.append(theDict)
        except:
            retArr = None

        print "getUpcomingRecordings JSON end"

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

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            retArr = self.getRecentRecordings_json(amount, showName, sortTitle, sortDateDown, recDir)
            self.myCachedPickle(retArr,cached)
            return retArr

        import suds.client

        if self.manage_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH
            self.manage_client = suds.client.Client(url,cache=self.objCache)
        client = self.manage_client

        authObj = client.factory.create('webServiceAuthentication')
        sortObj = client.factory.create('recordingsSort')
        fltrObj = client.factory.create('recordingsFilter')

        # Figure out the sorting....
        sortObj.datetimeSortSeq = 1
        sortObj.channelSortSeq = 4
        sortObj.titleSortSeq = 3
        sortObj.statusSortSeq = 2
        if sortDateDown:
            sortObj.datetimeDecending = 1
        else:
            sortObj.datetimeDecending = 0
        sortObj.channelDecending = 0
        if sortTitle:
            sortObj.titleDecending = 0
        else:
            sortObj.titleDecending = 1
        sortObj.statusDecending = 0

        # Then the filtering....
        fltrObj.All = 0
        setattr(fltrObj, "None", 0)
        fltrObj.Pending = 0
        fltrObj.InProgress = 1
        fltrObj.Completed = 1
        fltrObj.Failed = 1
        fltrObj.Conflict = 0
        fltrObj.Recurring = 0
        fltrObj.Deleted = 1
        if showName == None:
            fltrObj.FilterByName = False
        else:
            fltrObj.FilterByName = True
            fltrObj.NameFilter = showName.decode('utf-8')

        fltrObj.NameFilterCaseSensitive = True
        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)

        #client.set_options(soapheaders=authObj)
        #import logging
        #logging.basicConfig(level=logging.INFO)
        #logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)

        if amount == 0:
            ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)
        else:
            ret_soap = client.service.getSortedFilteredManageListObjectLimitResults(sortObj, fltrObj, amount, soapheaders=authObj)
        retArr = self._recs2array(ret_soap)
        if amount !=0 or len(retArr) > 10:
            self.myCachedPickle(retArr,cached)
        return retArr

    def getRecentRecordings_json(self, amount=0, showName=None, sortTitle=True, sortDateDown=True, recDir=None):

        print "getRecentRecordings JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/Get/SortedFilteredList' + self.jsid
        print url
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
            sortFilterObj['NameFilter'] = showName.decode('utf-8')
            sortFilterObj['NameFilterCaseSensitive'] = False

        retArr = []
        sortFilterObj = _json.dumps(sortFilterObj)
        print sortFilterObj

        try:
            request = urllib2.Request(url, sortFilterObj)
            request.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(request)
            results = response.read()
            recentResults = _json.loads(results)
            for epgEvent in  recentResults['ManageResults']['EPGEvents']:
                theDict = self._rec2dict1_json(epgEvent, recDir)
                if theDict != None:
                    retArr.append(theDict)
        except:
            retArr = None

        print "getRecentRecordings JSON end"

        return retArr


######################################################################################################
    def getConflicts(self, userid, password, conflictRec):

        import suds.client
            # First, we get a list of recordings sorted by date.....


        if self.manage_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH
            self.manage_client = suds.client.Client(url,cache=self.objCache)
        client = self.manage_client

        authObj = client.factory.create('webServiceAuthentication')
        sortObj = client.factory.create('recordingsSort')
        fltrObj = client.factory.create('recordingsFilter')

        # Figure out the sorting....
        sortObj.datetimeSortSeq = 1
        sortObj.channelSortSeq = 2
        sortObj.titleSortSeq = 3
        sortObj.statusSortSeq = 4
        sortObj.datetimeDecending = 0
        sortObj.channelDecending = 0
        sortObj.titleDecending = 0
        sortObj.statusDecending = 0

        # Then the filtering....
        fltrObj.All = 0
        setattr(fltrObj, "None", 0)
        fltrObj.Pending = 1
        fltrObj.InProgress = 0
        fltrObj.Completed = 0
        fltrObj.Failed = 0
        fltrObj.Conflict = 1
        fltrObj.Recurring = 0
        fltrObj.Deleted = 0

        fltrObj.FilterByName = False
        fltrObj.NameFilterCaseSensitive = False

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)

        client.set_options(soapheaders=authObj)
        ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)
        thePrograms =  self._recs2array(ret_soap)

        #Now we get the attributes from the program
        start = conflictRec['start']
        end = conflictRec['end']

        retArr = []
        if ret_soap is None:
                return retArr
        if ret_soap.webServiceManageListing is None:
            return retArr
        if len(ret_soap.webServiceManageListing) == 0:
            return retArr

        for prog in ret_soap.webServiceManageListing.webServiceProgramme:
            theDict = {}
            if prog.startTime <= end and prog.endTime >= start:
                #program in overlapping time
                theDict = self._rec2dict(prog)
                if theDict != None:
                    retArr.append(theDict)

        return retArr

    def getConflicts_json(self, userid, password, conflictRec):

        thePrograms =  self.getConflictedRecordings_json()

        #Now we get the attributes from the program
        start = conflictRec['start']
        end = conflictRec['end']

        retArr = []
        if ret_soap is None:
                return retArr
        if ret_soap.webServiceManageListing is None:
            return retArr
        if len(ret_soap.webServiceManageListing) == 0:
            return retArr

        for prog in ret_soap.webServiceManageListing.webServiceProgramme:
            theDict = {}
            if prog.startTime <= end and prog.endTime >= start:
                #program in overlapping time
                theDict = self._rec2dict(prog)
                if theDict != None:
                    retArr.append(theDict)
        return retArr

######################################################################################################
    def searchProgram(self, userid, password, needle, option):

        cached = 'search.List'
        if self.checkCache(cached):
            retArr = self.myCachedPickleLoad(cached)
            return retArr
        if needle == None:
            return None
        if self.settings.XNEWA_INTERFACE != 'SOAP':
            retArr =  self.searchProgram_json(needle,option)
            if retArr:
                self.myCachedPickle(retArr,cached)
            return retArr

        import suds.client

        import suds.client
        if self.search_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SEARCH_PATH
            self.search_client = suds.client.Client(url,cache=self.objCache)
        client = self.search_client


        authObj = client.factory.create('webServiceAuthentication')
        searchObj = client.factory.create('SavedSearch')
        # Figure out the sorting....
        searchObj.searchName = needle
        searchObj.autoShowSearch = True
        searchObj.autoRecordSearch = False
        searchObj.searchTitle = True
        searchObj.searchSubTitle = True
        searchObj.searchDescription = False
        searchObj.matchTitle = False
        searchObj.matchSubTitle = False
        searchObj.matchDescription = False
        searchObj.startTitle = False
        searchObj.startSubTitle = False
        searchObj.startDescription = False
        searchObj.searchPhrase = needle
        searchObj.searchCaseSensitive = False

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)
        client.set_options(soapheaders=authObj)

    #    import logging
    #    logging.basicConfig(level=logging.INFO)
    #    logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)
        ret_soap = client.service.searchObject(searchObj, soapheaders=authObj)
        return self._recs2array1(ret_soap)



######################################################################################################
    def searchProgram_json(self, needle,option):

        print "searchProgram JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/SearchService/Search' + self.jsid
        print url
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
        print searchObj

        try:
            request = urllib2.Request(url, searchObj)
            request.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(request)
            results = response.read()
            searchResults = _json.loads(results)
            retArr = []
            for prog in searchResults['SearchResults']['EPGEvents']:
                theDict = []
                theDict = self._rec2dict1_json(prog)
                if theDict != None:
                    retArr.append(theDict)


            print "searchProgram JSON end"
        except:
            retArr = None

        return retArr

######################################################################################################
    def getScheduledRecordings(self, userid, password):

        cached = 'scheduledRecordings.p'
        print cached
        if self.checkCache(cached):
            retArr = self.myCachedPickleLoad(cached)
            #return retArr

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            retArr = self.getScheduledRecordings_json()
            self.myCachedPickle(retArr,cached)
            return retArr

        import suds.client

        if self.manage_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH
            self.manage_client = suds.client.Client(url,cache=self.objCache)
        client = self.manage_client

        authObj = client.factory.create('webServiceAuthentication')
        sortObj = client.factory.create('recordingsSort')
        fltrObj = client.factory.create('recordingsFilter')

        # Figure out the sorting....
        sortObj.datetimeSortSeq = 0
        sortObj.channelSortSeq = 0
        sortObj.titleSortSeq = 0
        sortObj.statusSortSeq = 0
        sortObj.datetimeDecending = 0
        sortObj.channelDecending = 0
        sortObj.titleDecending = 0
        sortObj.statusDecending = 0

        # Then the filtering....
        fltrObj.All = 0
        setattr(fltrObj, "None", 0)
        fltrObj.Pending = 0
        fltrObj.InProgress = 0
        fltrObj.Completed = 0
        fltrObj.Failed = 0
        fltrObj.Conflict = 0
        fltrObj.Recurring = 1
        fltrObj.Deleted = 0

        fltrObj.FilterByName = False
        fltrObj.NameFilterCaseSensitive = False

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)
        client.set_options(soapheaders=authObj)
        ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)
        retArr = self._recs2array2(ret_soap)
        self.myCachedPickle(retArr,cached)
        return retArr



    def getScheduledRecordings_json(self):

        print "getScheduledRecordings JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/Get/SortedFilteredList' + self.jsid
        print url
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
        print sortFilterObj

        try:
            request = urllib2.Request(url, sortFilterObj)
            request.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(request)
            results = response.read()
            recurringResults = _json.loads(results)
            for recurring in  recurringResults['ManageResults']['EPGEvents']:
                theDict = self._recurr2dict(recurring['epgEventJSONObject'])
                if theDict != None:
                    retArr.append(theDict)
        except:
            retArr = None

        print "getScheduledRecordings JSON end"

        return retArr
######################################################################################################
    def getConflictedRecordings(self, userid, password):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            retArr = self.getConflictedRecordings_json()
            return retArr

        import suds.client

        if self.manage_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH
            self.manage_client = suds.client.Client(url,cache=self.objCache)
        client = self.manage_client

        authObj = client.factory.create('webServiceAuthentication')
        sortObj = client.factory.create('recordingsSort')
        fltrObj = client.factory.create('recordingsFilter')

        # Figure out the sorting....
        sortObj.datetimeSortSeq = 1
        sortObj.channelSortSeq = 4
        sortObj.titleSortSeq = 3
        sortObj.statusSortSeq = 2
        sortObj.datetimeDecending = 0
        sortObj.channelDecending = 0
        sortObj.titleDecending = 0
        sortObj.statusDecending = 0

        # Then the filtering....
        fltrObj.All = 0
        setattr(fltrObj, "None", 0)
        fltrObj.Pending = 0
        fltrObj.InProgress = 0
        fltrObj.Completed = 0
        fltrObj.Failed = 0
        fltrObj.Conflict = 1
        fltrObj.Recurring = 0
        fltrObj.Deleted = 0

        fltrObj.FilterByName = False
        fltrObj.NameFilterCaseSensitive = False

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)

        client.set_options(soapheaders=authObj)
        ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)

        return self._recs2array(ret_soap)

    def getConflictedRecordings_json(self):

        print "getConflictedRecordings JSON start"
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ManageService/Get/SortedFilteredList' + self.jsid
        print url
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
        print sortFilterObj

        try:
            request = urllib2.Request(url, sortFilterObj)
            request.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(request)
            results = response.read()
            conflictResults = _json.loads(results)
            for conflict in  conflictResults['ManageResults']['EPGEvents']:
                theDict = self._rec2dict1_json(conflict)
                if theDict != None:
                    retArr.append(theDict)
        except:
            retArr = None

        print "getConflictedRecordings JSON end"

        return retArr


######################################################################################################
    def updateRecording(self, userid, password, progDetails):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            return self.updateRecording_json(progDetails)

        import suds.client

        days = progDetails['day']

        if self.schedule_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SCHEDULE_PATH
            self.schedule_client = suds.client.Client(url,cache=self.objCache)
        client = self.schedule_client

        authObj = client.factory.create('webServiceAuthentication')

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)
        recObj = client.factory.create('webServiceScheduleSettings')
        qualObj = client.factory.create('RecordingQuality')

        recObj.ChannelOid = progDetails['channel_oid']
        recObj.startDate = progDetails['start'] - self.dst_offset
        recObj.endDate = progDetails['end'] - self.dst_offset
        if progDetails['recquality'].lower() == "good":
            recObj.quality = qualObj.QUALITY_GOOD
        elif progDetails['recquality'].lower() == "better":
            recObj.quality = qualObj.QUALITY_BETTER
        elif progDetails['recquality'].lower() == "best":
            recObj.quality = qualObj.QUALITY_BEST
        else:
            recObj.quality = qualObj.QUALITY_DEFAULT
        recObj.qualityBest = qualObj.QUALITY_BEST
        recObj.qualityBetter = qualObj.QUALITY_BETTER
        recObj.qualityGood = qualObj.QUALITY_GOOD
        recObj.qualityDefault = qualObj.QUALITY_DEFAULT
        if 'Monday' in days:
            recObj.dayMonday = True
        else:
            recObj.dayMonday = False
        if 'Tuesday' in days:
            recObj.dayTuesday = True
        else:
            recObj.dayTuesday = False
        if 'Wednesday' in days:
            recObj.dayWednesday = True
        else:
            recObj.dayWednesday = False
        if 'Thursday' in days:
            recObj.dayThursday = True
        else:
            recObj.dayThursday = False
        if 'Friday' in days:
            recObj.dayFriday = True
        else:
            recObj.dayFriday = False
        if 'Saturday' in days:
            recObj.daySaturday = True
        else:
            recObj.daySaturday = False
        if 'Sunday' in days:
            recObj.daySunday = True
        else:
            recObj.daySunday = False


        recObj.recColorRed = False
        recObj.recColorGreen = False
        recObj.recColorYellow = False
        recObj.recColorBlue = False

        recObj.onlyNew = progDetails['onlyNew']
        recObj.allChannels = progDetails['allChannels']
        recObj.pre_padding_min = progDetails['prepadding']
        recObj.post_padding_min = progDetails['postpadding']
        try:
            recObj.extend_end_time_min = progDetails['extendend']
        except:
            recObj.extend_end_time_min = 0

        recObj.days_to_keep = progDetails['maxrecs']

        client.set_options(soapheaders=authObj)

        if progDetails['directory'] != "Default":
            #recObj.recDirId = '[' + progDetails['directory'] + ']'
            recObj.recDirId = progDetails['directory']

        if progDetails['rectype'] == 'Recurring':
            recObj.recurringName = progDetails['name']
            recObj.manualRecTitle = progDetails['title']
            recordTimeIntervalType = client.factory.create('recordTimeIntervalType')
            if 'TimeSlot' in progDetails['desc']:
                recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot
            else:
                recObj.recordTimeInterval = recordTimeIntervalType.recordAnyTimeslot

            recordDayIntervalType = client.factory.create('recordDayIntervalType')
            if len(days) == 1:
                recObj.recordDayInterval = recordDayIntervalType.recordThisDay
            elif len(days) == 7:
                recObj.recordDayInterval = recordDayIntervalType.recordAnyDay
            else:
                recObj.recordDayInterval = recordDayIntervalType.recordSpecificDay
            if progDetails['rules'] != None:
                recObj.rules = progDetails['rules']

            #recObj.AdvancedRules = progDetails['rulesxml']
            #rec.Name = progDetails['name']
            #import logging
            #logging.basicConfig(level=logging.INFO)
            #logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)
            ret_soap = client.service.updateRecurring(progDetails['recording_oid'], recObj, soapheaders=authObj)
        else:
            ret_soap = client.service.updateRecording(progDetails['recording_oid'], recObj, soapheaders=authObj)

        if ret_soap.webServiceEPGEventObjects.webServiceReturn.Message is not None:
            print ret_soap.webServiceEPGEventObjects.webServiceReturn.Message
            last_Error = ret_soap.webServiceEPGEventObjects.webServiceReturn.Message

        return (not  ret_soap.webServiceEPGEventObjects.webServiceReturn.Error)

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
        print recObj

        try:
            print url
            try:
                request = urllib2.Request(url, recObj)
                request.add_header('Content-Type', 'application/json')
                response = urllib2.urlopen(request)
            except urllib2.URLError, e:
                print e.code
                if e.code == 500:
                    eresults = e.read()
                    scheduleResults = _json.loads(eresults)
                    print scheduleResults
                print scheduleResults['epgEventJSONObject']
                self.Last_Error = scheduleResults['epgEventJSONObject']['rtn']['Message']
                return False
            else:
                print response.getcode()
                results = response.read()
                updateResults = _json.loads(results)
                print updateResults
            return True
        except Exception, err:
            print err
            return False

######################################################################################################
    def scheduleRecording(self, userid, password, progDetails):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            return self.scheduleRecording_json(progDetails)

        import suds.client

        if self.schedule_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SCHEDULE_PATH
            self.schedule_client = suds.client.Client(url,cache=self.objCache)
        client = self.schedule_client

        authObj = client.factory.create('webServiceAuthentication')

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)
        recObj = client.factory.create('webServiceScheduleSettings')
        qualObj = client.factory.create('RecordingQuality')
        if progDetails['recquality'].lower() == "good":
            recObj.quality = qualObj.QUALITY_GOOD
        elif progDetails['recquality'].lower() == "better":
            recObj.quality = qualObj.QUALITY_BETTER
        elif progDetails['recquality'].lower() == "best":
            recObj.quality = qualObj.QUALITY_BEST
        else:
            recObj.quality = qualObj.QUALITY_DEFAULT

        recObj.qualityGood = qualObj.QUALITY_GOOD
        recObj.qualityBetter = qualObj.QUALITY_BETTER
        recObj.qualityBest = qualObj.QUALITY_BEST
        recObj.qualityDefault = qualObj.QUALITY_DEFAULT

        recObj.dayMonday = False
        recObj.dayTuesday = False
        recObj.dayWednesday = False
        recObj.dayThursday = False
        recObj.dayFriday = False
        recObj.daySaturday = False
        recObj.daySunday = False
        recObj.onlyNew = False
        recObj.allChannels = False

        recObj.recColorRed = False
        recObj.recColorGreen = False
        recObj.recColorYellow = False
        recObj.recColorBlue = False

        recObj.epgeventOID = progDetails['program_oid']
        recObj.ChannelOid = 0
        recObj.startDate = progDetails['start']
        recObj.endDate = progDetails['end']

        if progDetails['directory'] != "Default":
            recObj.recDirId = progDetails['directory']

        recordDayIntervalType = client.factory.create('recordDayIntervalType')
        recordTimeIntervalType = client.factory.create('recordTimeIntervalType')

        if progDetails['rectype'] == 'Record Once':
            recObj.recordTimeInterval = recordTimeIntervalType.recordOnce
            recObj.recordDayInterval = recordDayIntervalType.recordThisDay
        elif progDetails['rectype'] == "Record Season (NEW episodes on this channel)":
            recObj.onlyNew = true
            recObj.recordDayInterval = recordDayIntervalType.recordAnyDay
            recObj.recordTimeInterval = recordTimeIntervalType.recordAnyTimeslot
        elif progDetails['rectype'] == "Record Season (All episodes on this channel)":
            recObj.recordDayInterval = recordDayIntervalType.recordAnyDay
            recObj.recordTimeInterval = recordTimeIntervalType.recordAnyTimeslot
        elif progDetails['rectype'] == "Record Season (Daily, this timeslot)":
            recObj.recordDayInterval =  recordDayIntervalType.recordAnyDay
            recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot
        elif progDetails['rectype'] == "Record Season (Weekly, this timeslot)":
            recObj.recordDayInterval =  recordDayIntervalType.recordThisDay
            recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot
        elif progDetails['rectype'] == "Record Season (Monday-Friday, this timeslot)":
            recObj.recordDayInterval =  recordDayIntervalType.recordSpecificDay
            recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot
            recObj.dayMonday = True
            recObj.dayTuesday = True
            recObj.dayWednesday = True
            recObj.dayThursday = True
            recObj.dayFriday = True
        elif progDetails['rectype'] == "Record Season (Weekends, this timeslot)":
            recObj.recordDayInterval =  recordDayIntervalType.recordSpecificDay
            recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot
            recObj.daySaturday = True
            recObj.daySunday = True
        elif progDetails['rectype'] == "Record All Episodes, All Channels":
            recObj.allChannels = True
            recObj.recurringName = progDetails['title']
            recObj.manualRecTitle  = progDetails['title']
            recObj.recordDayInterval = recordDayIntervalType.recordAnyDay
            recObj.recordTimeInterval = recordTimeIntervalType.recordAnyTimeslot
        else:
            print "Unknown rectype"
            return False

        recObj.pre_padding_min = progDetails['prepadding']
        recObj.post_padding_min = progDetails['postpadding']
        recObj.extend_end_time_min = 0
        recObj.days_to_keep = progDetails['maxrecs']


        client.set_options(soapheaders=authObj)

        #import logging
        #logging.basicConfig(level=logging.INFO)
        #logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)
        print recObj
        ret_soap = client.service.scheduleRecording(recObj, soapheaders=authObj)
        print ret_soap
        if ret_soap.webServiceEPGEventObjects.webServiceReturn.Message is not None:
            print ret_soap.webServiceEPGEventObjects.webServiceReturn.Message
            last_Error = ret_soap.webServiceEPGEventObjects.webServiceReturn.Message
            if progDetails['rectype'] != 'Record Once':
                return 200
        else:
            self.changedRecordings = True
        if ret_soap.webServiceEPGEventObjects.webServiceReturn.Error == True:
            return 400
        else:
            return 200


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
            print "Unknown rectype"
            return False

        import xbmcgui

        try:

            if self.defaultSchedule == None:
                self.getDefaultSchedule()

            recObj['pre_padding_min'] = progDetails['prepadding']
            recObj['post_padding_min'] = progDetails['postpadding']
            recObj['extend_end_time_min'] = 0
            recObj['days_to_keep'] = progDetails['maxrecs']
            print recObj
            recObj = _json.dumps(recObj)
            print recObj

            url = "http://" + self.ip + ":" + str(self.port) + '/public/ScheduleService/Record' + self.jsid
            print url
            request = urllib2.Request(url, recObj)
            request.add_header('Content-Type', 'application/json')
            try:
                print 'Posting'
                response = urllib2.urlopen(request)
                self.changedRecordings = True
                print response.code
                results = response.read()
                scheduleResults = _json.loads(results)
                return response.code

            except urllib2.URLError, e:
                print e.code
                if e.code == 500:
                    eresults = e.read()
                    scheduleResults = _json.loads(eresults)
                    print scheduleResults
                    if 'schdConflicts' in scheduleResults['epgEventJSONObject']:
                        conflictName = []
                        for conflict in scheduleResults['epgEventJSONObject']['schdConflicts']:
                            conflictName.append(conflict['Name'])
                        choice =  xbmcgui.Dialog().select(smartUTF8(__language__(30132)), conflictName)
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
        except Exception, err:
            print err
            return -1

######################################################################################################

    def getDefaultSchedule(self):
        url = "http://" + self.ip + ":" + str(self.port) + '/public/ScheduleService/Get/SchedSettingsObj' + self.jsid
        print url
        json_file = urllib2.urlopen(url)
        self.defaultSchedule = _json.load(json_file)
        json_file.close()
        print self.defaultSchedule


######################################################################################################
    def cancelRecording(self, userid, password, progDetails):

        if self.settings.XNEWA_INTERFACE != 'SOAP':
            return self.cancelRecording_json(progDetails)

        import suds.client
        if self.schedule_client == None:
            url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SCHEDULE_PATH
            self.schedule_client = suds.client.Client(url,cache=self.objCache)
        client = self.schedule_client

        authObj = client.factory.create('webServiceAuthentication')

        # Fill authentication object
        authObj = self._AddAuthentication(authObj, userid, password)

        client.set_options(soapheaders=authObj)

        if progDetails['rectype'].lower() == "recurring" or progDetails['status'].lower() == "recurring":
            debug("Cancelling")
            ret_soap = client.service.cancelRecurring(progDetails['recording_oid'], soapheaders=authObj)
        elif progDetails['status'].lower() == "pending":
            debug("Cancelling")
            ret_soap = client.service.cancelRecording(progDetails['recording_oid'], soapheaders=authObj)
        elif progDetails['status'].lower() == "conflict":
            debug("Cancelling")
            ret_soap = client.service.cancelRecording(progDetails['recording_oid'], soapheaders=authObj)
        elif progDetails['status'].lower() == "in-progress":
            debug("Cancelling")
            ret_soap = client.service.cancelRecording(progDetails['recording_oid'], soapheaders=authObj)
        elif progDetails['status'].lower() == "completed":
            debug("Cancelling and Deleting")
            ret_soap = client.service.cancelAndDeleteRecording(progDetails['recording_oid'], soapheaders=authObj)
        elif progDetails['status'].lower() == "failed":
            debug("Cancelling and Deleting")
            ret_soap = client.service.cancelAndDeleteRecording(progDetails['recording_oid'], soapheaders=authObj)
        else: ## "deleted":
            debug("Cancelling and Deleting")
            ret_soap = client.service.cancelAndDeleteRecording(progDetails['recording_oid'], soapheaders=authObj)

        if ret_soap.webServiceEPGEventObjects.webServiceReturn.Message is not None:
            print ret_soap.webServiceEPGEventObjects.webServiceReturn.Message
            last_Error = ret_soap.webServiceEPGEventObjects.webServiceReturn.Message
        else:
            self.changedRecordings = True
        print 'DONE'
        return (not ret_soap.webServiceEPGEventObjects.webServiceReturn.Error)

    def cancelRecording_json(self, progDetails):
        print progDetails
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

        json_file = urllib2.urlopen(url)
        cancelService = _json.load(json_file)
        json_file.close()
        print cancelService
        if cancelService['epgEventJSONObject']['rtn']['Error'] == False:
            self.changedRecordings = True
        return (not cancelService['epgEventJSONObject']['rtn']['Error'])


# Helper functions
######################################################################################################
# Translating a (soap) recordinglist into an array of dictionaries...
######################################################################################################
    def _recs2array(self, soapObj):
        retArr = []

        if soapObj is None:
            return retArr
        if soapObj.webServiceManageListing is None:
            return retArr
        if len(soapObj.webServiceManageListing) == 0:
            return retArr
        for prog1 in soapObj.webServiceManageListing.webServiceEPGEvent:
            try:
                for prog in prog1:
                    theDict = self._rec2dict(prog)
                    if theDict != None:
                        retArr.append(theDict)
                    break
            except:
                print '_recs2array manual entry'
                pass

        return retArr

######################################################################################################
# public functions to format the datetime object returned by NPVR
######################################################################################################
    def formatDate( self, dt, withyear=False, gmtoffset=False ):
        if gmtoffset:
            dt = dt - datetime.timedelta(seconds=time.timezone if (time.localtime().tm_isdst == 0) else time.altzone)
        return dt.strftime( self._dateformat( withyear ) )


    def formatTime( self, dt, withsecs=False, leadzero=False, gmtoffset=False ):
        if gmtoffset:
            dt = dt - datetime.timedelta(seconds=time.timezone if (time.localtime().tm_isdst == 0) else time.altzone)
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
# Translating a (soap) recordinglist into an array of dictionaries...
######################################################################################################
    def _recs2array1(self, soapObj):
        retArr = []

        if soapObj is None:
            return retArr
        if soapObj.webServiceManageListing is None:
            return retArr
        if len(soapObj.webServiceManageListing) == 0:
            return retArr
        for prog in soapObj.webServiceManageListing.webServiceEPGEvent:
            theDict = self._rec2dict1(prog)
            if theDict != None:
                retArr.append(theDict)
        return retArr

######################################################################################################
# Translating a (soap) recordinglist into an array of dictionaries...
######################################################################################################
    def _recs2array2(self, soapObj):
        retArr = []
        if soapObj is None:
            return retArr
        if soapObj.webServiceManageListing is None:
            return retArr
        if len(soapObj.webServiceManageListing  ) == 0:
            return retArr

        #todo fix suds processing
        x = soapObj.webServiceManageListing
        for prog in x[0]:
            p1 = prog[0].webServiceReturn
            theDict = self._rec2dict2(prog[0])
            retArr.append(theDict)
        return retArr


    ######################################################################################################
    # Translating a (soap)1 recordingobject into a dictionary object...
    ######################################################################################################
    def _rec2dict(self, epgo):
        theDict = {}
        #todo fix suds processing
        L = epgo
        try:
            if L[1].webServiceEPGEventObject is not None:
                prog = L[1].webServiceEPGEventObject
            if prog.HasSchedule:
                rec = L[1].webServiceScheduleObject
            else:
                rec = None
        except:
            prog = None
            rec = L[1].webServiceScheduleObject
        if prog is not None:
            theDict['title'] = prog.Title.encode('utf-8')
            theDict['start'] = prog.StartTime + self.dst_offset
            theDict['end'] = prog.EndTime + self.dst_offset
            if prog.Desc is not None:
                theDict['desc'] = prog.Desc.encode('utf-8')
            else:
                theDict['desc'] = ""
            if prog.Subtitle is not None:
                theDict['subtitle'] = prog.Subtitle.encode('utf-8')
            else:
                theDict['subtitle'] = ""
            theDict['program_oid'] = prog.OID
            if prog.ChannelOid !=0:
                theDict['channel_oid'] = prog.ChannelOid
            if prog.HasSchedule:
                theDict['recording_oid'] = rec.OID
                if prog.ChannelOid == 0:
                    theDict['channel_oid'] = rec.ChannelOid
                theDict['status'] = rec.Status
                if rec.Status == "Completed" or rec.Status == "In-Progress":
                    if rec.RecordingFileName is not None:
                        theDict['filename'] = rec.RecordingFileName
                    else:
                        theDict['filename'] = ""
                    theDict['directory'] = ""
                    if self.settings.XNEWA_COLOURS != None:
                        foundColour = False
                        if 'red' in self.settings.XNEWA_COLOURS and rec.Red :
                            print 'is red'
                            foundColour = True
                        elif 'green' in self.settings.XNEWA_COLOURS  and rec.Green :
                            print 'is green'
                            foundColour = True
                        elif 'yellow' in self.settings.XNEWA_COLOURS and rec.Yellow:
                            foundColour = True
                        elif 'blue' in self.settings.XNEWA_COLOURS and rec.Blue:
                            print 'is blue'
                            foundColour = True

                        if foundColour == False:
                            return None
                elif rec.RecordingFileName is not None:
                    theDict['directory'] = rec.RecordingFileName[1:-1]
                else:
                    theDict['directory'] = "Default"
            else:
                theDict['status'] = ""
            theDict['priority'] = 0
            if prog.OID > 0 and rec.Status != "Completed" and rec.Status != "Failure":
                theDict['rec'] = True
            else:
                theDict['rec'] = False
            theDict['directory'] = ""
        else:
            theDict['title'] = rec.Name.encode('utf-8')
            theDict['start'] = rec.StartTime + self.dst_offset
            theDict['end'] = rec.EndTime + self.dst_offset
            theDict['desc'] = ""
            theDict['subtitle'] = ""
            theDict['program_oid'] = None
            theDict['recording_oid'] = rec.OID
            theDict['priority'] = rec.Priority
            theDict['channel_oid'] = rec.ChannelOid
            theDict['rec'] = False
            theDict['directory'] = ""
            if rec.Status == "Completed" or rec.Status == "In-Progress":
                theDict['filename'] = rec.RecordingFileName
            else:
                theDict['filename'] = ''
            if rec.Status is not None:
                theDict['status'] = rec.Status
            else:
                theDict['status'] = ""
        if str(theDict['channel_oid']) in self.channels:
            theDict['channel'] = self.channels[str(theDict['channel_oid'])]
        else:
            theDict['channel'] = self.channels['0']
        if rec.Status == 'Recurring':
            theDict['rectype'] = prog.recordingType
        else:
            theDict['rectype'] = self.SCHEDULE_ONCE

        theDict['resume'] = 0
        return theDict

######################################################################################################
# Translating a (soap)1 recordingobject into a dictionary object...
######################################################################################################
    def _rec2dict1(self, epgo):
        theDict = {}
        q = epgo[0].webServiceReturn

        try:
            prog = epgo[0].webServiceEPGEventObject
        except:
            return _rect2dict(epgo)

    #    if L.webServiceEPGEventObject is not None:
    #        prog = L.webServiceEPGEventObject

        if prog.HasSchedule is True:
            rec = epgo[0].webServiceScheduleObject

        if prog.Title is not None:
            theDict['title'] = prog.Title.encode('utf-8')
        else:
            theDict['title'] = rec.Name.encode('utf-8')

        if prog.StartTime.year > 1:
            theDict['start'] = prog.StartTime + self.dst_offset
            theDict['end'] = prog.EndTime + self.dst_offset
        else:
            theDict['start'] = rec.StartTime + self.dst_offset
            theDict['end'] = rec.EndTime + self.dst_offset

        if prog.Desc is not None:
            theDict['desc'] = prog.Desc.encode('utf-8')
        else:
            theDict['desc'] = ""

        if prog.Subtitle is not None:
            theDict['subtitle'] = prog.Subtitle.encode('utf-8')
        else:
            theDict['subtitle'] = ""

        theDict['program_oid'] = prog.OID
        if prog.HasSchedule is True:
            theDict['priority'] = rec.Priority
            if rec.Status == 'Recurring':
                theDict['rectype'] = prog.recordingType
            else:
                theDict['rectype'] = self.SCHEDULE_ONCE
            if rec.RecordingFileName is not None:
                if rec.Status == "Completed" or rec.Status == "In-Progress":
                    theDict['filename'] = rec.RecordingFileName
                    theDict['directory'] = ''
                    theDict['rec'] = False
                    if self.settings.XNEWA_COLOURS != None:
                        foundColour = False
                        if 'red' in self.settings.XNEWA_COLOURS and rec.Red :
                            print 'is red'
                            foundColour = True
                        elif 'green' in self.settings.XNEWA_COLOURS  and rec.Green :
                            print 'is green'
                            foundColour = True
                        elif 'yellow' in self.settings.XNEWA_COLOURS and rec.Yellow:
                            foundColour = True
                        elif 'blue' in self.settings.XNEWA_COLOURS and rec.Blue:
                            print 'is blue'
                            foundColour = True

                        if foundColour == False:
                            return None
                else:
                    theDict['filename'] = ''
                    theDict['directory'] = rec.RecordingFileName[1:-1]
                    theDict['rec'] = True
            else:
                theDict['directory'] = "Default"
                theDict['filename'] = ''
                theDict['rec'] = True
            theDict['status'] = rec.Status
            theDict['recording_oid'] = rec.OID
            theDict['channel_oid'] = rec.ChannelOid
        else:
            theDict['priority'] = ""
            theDict['rectype'] = ""
            theDict['status'] = ""
            theDict['recording_oid'] = ""
            theDict['rec'] = False
            theDict['channel_oid'] = prog.ChannelOid
        if str(theDict['channel_oid']) in self.channels:
            theDict['channel'] = self.channels[str(theDict['channel_oid'])]
        else:
            theDict['channel'] = self.channels['0']
        return theDict

######################################################################################################
# Translating a json epgEventJSONObject into a dictionary object...
######################################################################################################
    def _rec2dict1_json(self, epgEventJSONObject, recDir=None):
        import re
        theDict = {}
        try:
            q = epgEventJSONObject['epgEventJSONObject']['rtn']
        except:
            print 'Conflict?'
        try:
            prog = epgEventJSONObject['epgEventJSONObject']['epgEvent']
        except:
            return _rect2dict(epgo)
        if prog['HasSchedule'] is True:
            rec = epgEventJSONObject['epgEventJSONObject']['schd']
        if prog['Title'] is not None:
            theDict['title'] = prog['Title'].encode('utf-8')
            if prog['Title'] == '' and prog['HasSchedule'] is True:
                theDict['title'] = rec['Name'].encode('utf-8')
        else:
            theDict['title'] = rec['Name'].encode('utf-8')
        if prog['StartTime'] != '' and prog['StartTime'] != '0001-01-01T00:00:00':
            theDict['start'] = self.jsonDate(prog['StartTime'],self.dst_offset)
            theDict['end'] = self.jsonDate(prog['EndTime'],self.dst_offset)
        else:
            theDict['start'] = self.jsonDate(rec['StartTime'],self.dst_offset)
            theDict['end'] = self.jsonDate(rec['EndTime'],self.dst_offset)
        if prog['Desc'] is not None:
            theDict['desc'] = prog['Desc'].encode('utf-8')
        else:
            theDict['desc'] = ""
        if prog['Subtitle'] is not None:
            theDict['subtitle'] = prog['Subtitle'].encode('utf-8')
        else:
            theDict['subtitle'] = ""
        if prog.has_key('Season'):
            theDict['season'] = prog['Season']
        else:
            theDict['season'] = 0
        if prog.has_key('Episode'):
            theDict['episode'] = prog['Episode']
        else:
            theDict['episode'] = 0
        if prog.has_key('Significance'):
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
                            print 'is red'
                            foundColour = True
                        elif 'green' in self.settings.XNEWA_COLOURS  and rec['Green'] :
                            print 'is green'
                            foundColour = True
                        elif 'yellow' in self.settings.XNEWA_COLOURS and rec['Yellow']:
                            foundColour = True
                        elif 'blue' in self.settings.XNEWA_COLOURS and rec['Blue']:
                            print 'is blue'
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
                    theDict['status'] = 'Partial ' + str(100 * theDict['resume']/theDict['duration']) + ' %'
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
# Translating a (soap)1 recordingobject into a dictionary object...
######################################################################################################
    def _rec2dict2(self, epgo):
        theDict = {}
        q = epgo.webServiceReturn
        rec = epgo.webServiceRecurringObject
        try:
            try:
                theDict['title'] = rec.EPGTitle.encode('utf-8')
                theDict['name'] = rec.RecurringName.encode('utf-8')
            except:
                if rec.RecurringName != None:
                    theDict['title'] = rec.RecurringName.encode('utf-8')
                else:
                    theDict['title'] = 'Unnamed'
                    theDict['name'] = 'Unnamed'
        except:
            theDict['title'] = rec.Name.encode('utf-8')
            theDict['name'] = rec.Name.encode('utf-8')
        theDict['start'] = rec.StartTime + self.dst_offset
        theDict['end'] = rec.EndTime + self.dst_offset
        #todo fix Rules display
        rules = str(rec.RulesXmlDoc.Rules)
        rules = rules.decode('iso-8859-1').encode('utf8')
        #theDict['rulesxml'] = rec.RulesXmlDoc.Rules
        try:
            theDict['rules'] = rec.AdvancedRules
            theDict['desc'] = 'Advanced Rules = ' + rules
        except:
            theDict['desc'] = rules
            theDict['rules'] = None

        try:
            if rec.RecordingDirectoryID =='[]':
                theDict['directory'] = "Default"
            else:
                theDict['directory'] = rec.RecordingDirectoryID[1:-1]
        except:
            theDict['directory'] = "Default"

        theDict['subtitle'] = ""
        theDict['program_oid'] = 0
        theDict['rec'] = False

        theDict['priority'] = rec.Priority
        theDict['rectype'] = rec.Type
        theDict['status'] = ''
        theDict['recording_oid'] = rec.OID
        theDict['channel_oid'] = rec.ChannelOid

        if str(theDict['channel_oid']) in self.channels:
            theDict['channel'] = self.channels[str(theDict['channel_oid'])]
        else:
            theDict['channel'] = self.channels['0']
        theDict['genres'] = ""
        theDict['recquality'] = rec.Quality
        theDict['prepadding'] = rec.PrePadding
        theDict['postpadding'] = rec.PostPadding
        theDict['maxrecs'] = rec.MaxRecordings
        theDict['onlyNew'] = rec.OnlyNew
        theDict['day'] = rec.Day.split(',')
        theDict['allChannels'] = rec.allChannels
        theDict['movie'] = False
        return theDict

    def _rec2dict2_json(self, epgo):
         theDict = {}
         q = epgo.webServiceReturn
         rec = epgo.webServiceRecurringObject
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
         theDict['start'] = rec['StartTime'] + self.dst_offset
         theDict['end'] = rec['EndTime'] + self.dst_offset
         #todo fix Rules display
         rules = str(rec['RulesXmlDoc'].Rules)
         rules = rules.decode('iso-8859-1').encode('utf8')
         #theDict['rulesxml'] = rec['RulesXmlDoc'].Rules
         try:
             theDict['rules'] = rec['AdvancedRules']
             theDict['desc'] = 'Advanced Rules = ' + rules
         except:
             theDict['desc'] = rules
             theDict['rules'] = None

         try:
             if rec['RecordingDirectoryID'] == None:
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
        rules = rules.decode('iso-8859-1').encode('utf8')
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
# Translating a (soap) programmelist into an array of dictionaries...
######################################################################################################
    def _progs2array(self, soapObj):

        print "Processing listings start"

        retArr = []

        for chnl in soapObj.webServiceGuideListing.webServiceGuideChannel:
            channel = {}
            channel['name'] = chnl.channelName
            channel['oid'] = chnl.channelOID
            channel['num'] = chnl.channelNumber
            progs = []
            for event in chnl.webServiceGuideChannelEPGEvents.webServiceEPGEvent:
                prog = event.webServiceEPGEventObjects.webServiceEPGEventObject
                dic = {}
                dic['title'] = unicode(prog.Title)
                dic['subtitle'] = unicode(prog.Subtitle)
                if prog.Desc is not None:
                    dic['desc'] = unicode(prog.Desc)
                else:
                    dic['desc'] = ""

                dic['start'] = prog.StartTime + self.dst_offset
                dic['end'] = prog.EndTime + self.dst_offset

                dic['oid'] = prog.OID
                if prog.HasSchedule is True:
                    rec = event.webServiceEPGEventObjects.webServiceScheduleObject
                    if rec.Status == 'Pending' or rec.Status == 'In-Progress':
                        dic['rec'] = True
                    else:
                        dic['rec'] = False
                    if self.settings.XNEWA_COLOURS != None:
                        foundColour = False
                        if 'red' in self.settings.XNEWA_COLOURS and rec.Red :
                            print 'is red'
                            foundColour = True
                        elif 'green' in self.settings.XNEWA_COLOURS  and rec.Green :
                            print 'is green'
                            foundColour = True
                        elif 'yellow' in self.settings.XNEWA_COLOURS and rec.Yellow:
                            foundColour = True
                        elif 'blue' in self.settings.XNEWA_COLOURS and rec.Blue:
                            print 'is blue'
                            foundColour = True

                        if foundColour == False:
                            contine
                else:
                    dic['rec'] = False
                #todo are genres used
                dic['genreColour'] = 0
                if prog.Genres:
                    dic['genres'] = prog.Genres.Genre
                    for genre in prog.Genres.Genre:
                        try:
                            if self.genresColours[genre] != 0:
                                dic['genreColour'] = str(hex(self.genresColours[genre]))
                        except:
                            print 'no genres'
                else:
                    dic['genres'] = ''

                dic['firstrun'] = prog.FirstRun
                progs.append(dic)
            channel['progs'] = progs
            retArr.append(channel)
        print "Process listing end"
        return retArr


######################################################################################################
# Translating a (xml) recording.list into a dictionaries...
######################################################################################################
    def _rec2dictDirect(self):
        import xml.etree.ElementTree as ET
        import datetime
        print "Processing xml pending recording list start"
        url = self.getURL()+ "/services?method=recording.list&filter=pending&sid=" + self.sid
        print url
        request = urllib2.Request(url, headers={"Accept" : "application/xml"})
        u = urllib2.urlopen(request)
        tree = ET.parse(u)
        root = tree.getroot()
        dic = {}
        for recording in root.find('recordings'):
            print recording
            #print recording.find('epg_event_oid').text
            #print recording.find('name').text.encode('utf-8')
            #print recording.find('status').text.encode('utf-8')
            #print datetime.datetime.fromtimestamp(float(recording.find('start_time_ticks').text))
            if recording.find('status').text == 'Pending':
                dic[recording.find('epg_event_oid').text] = recording.find('status').text.encode('utf-8')
        print "Processing xml pending recording list end"
        return dic

######################################################################################################
# Translating a (xml) programmelist into an array of dictionaries...
######################################################################################################
    def _progs2array_xml(self,url,getRecordings=True):

        print "Processing xml listings start"

        retArr = []
        import xml.etree.ElementTree as ET
        import codecs
        import datetime
        import time
        self.miniEPG = datetime.datetime.max

        if getRecordings == True:
            mydic = self._rec2dictDirect()
        else:
            mydic = {}

        #parser = ET.XMLParser(encoding="utf-8")
        #c = codecs.open('c:/temp/guide.xml',encoding='utf-16')
        if True:
            request = urllib2.Request(url, headers={"Accept" : "application/xml"})
            u = urllib2.urlopen(request)
            tree = ET.parse(u)
        else:
            tree = ET.parse('c:/temp/service.xml')
        root = tree.getroot()
        print root
        for channel in root.find('listings'):
            #print channel.attrib['id']
            ss = channel.attrib['id']
            chan = {}
            chan['name'] = channel.attrib['name']
            chan['oid'] = channel.attrib['id']
            #print self.channels[ss]
            chan['num'] = channel.attrib['number']
            progs = []
            for listing in channel.findall('l'):
                #print listing.find('id').text
                #print listing.find('name').text.encode('utf-8')
                #print datetime.datetime.fromtimestamp((float(listing.find('start').text)/1000))
                #print datetime.datetime.fromtimestamp((float(listing.find('end').text)/1000))
                dic = {}
                dic['title'] = unicode(listing.find('name').text)
                if listing.find('description').text != None:
                    temp = listing.find('description').text.split(':')
                    if len(temp) < 2:
                        dic['subtitle'] = ''
                        dic['desc'] = unicode(temp[0])
                    else:
                        dic['desc'] = unicode(temp[1])
                        dic['subtitle'] = unicode(temp[0])
                else:
                    dic['desc'] = ""
                    dic['subtitle'] = ""

                dic['start'] = datetime.datetime.fromtimestamp((float(listing.find('start').text)/1000))
                dic['end'] = datetime.datetime.fromtimestamp((float(listing.find('end').text)/1000))
                if self.miniEPG > dic['end']:
                   self.miniEPG = dic['end']

                dic['oid'] = listing.find('id').text
                if mydic.has_key(dic['oid']):
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
            retArr.append(chan)
        print "Process listing end"
        return retArr


######################################################################################################
# Translating a (json) programmelist into an array of dictionaries...
######################################################################################################
    def _progs2array_json(self,url):

        print "Processing json listings start"

        retArr = []

        import time
        self.miniEPG = datetime.datetime.max

        if True:
            guideService = self.nextJson(url)
        else:
            tree = ET.parse('c:/temp/service.xml')

        #error = guideService['Guide']['rtn']
        #print "Guide error returns: " + str(error['Error'])
        dict = {}

        #if error['Error'] is True:
        #    print error['Message']
        #    return dict

        for listing in guideService['Guide']['Listings']:
            channel = {}
            channel['name'] = listing['Channel']['channelName'].encode('utf-8')
            channel['oid'] = listing['Channel']['channelOID']
            if not (listing['Channel']).has_key('channelMinor'):
                channel['num'] = str(listing['Channel']['channelNumber'])
            elif listing['Channel']['channelMinor'] == 0:
                channel['num'] = str(listing['Channel']['channelNumber'])
            else:
                channel['num'] = str(listing['Channel']['channelNumber']) + '.' + str(listing['Channel']['channelMinor'])
            progs = []
            for event in listing['EPGEvents']:
                prog = event['epgEventJSONObject']['epgEvent']
                dic = {}
                dic['title'] = prog['Title'].encode('utf-8')
                dic['subtitle'] = prog['Subtitle'].encode('utf-8')
                if prog['Desc'] is not None:
                    dic['desc'] = prog['Desc'].encode('utf-8')
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
                            print 'is red'
                            foundColour = True
                        elif 'green' in self.settings.XNEWA_COLOURS  and rec['Green'] :
                            print 'is green'
                            foundColour = True
                        elif 'yellow' in self.settings.XNEWA_COLOURS and rec['Yellow']:
                            foundColour = True
                        elif 'blue' in self.settings.XNEWA_COLOURS and rec['Blue']:
                            print 'is blue'
                            foundColour = True

                        if foundColour == False:
                            contine
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
        print "Process listing end"
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
            print url
            import httplib
            import urlparse
            try:
                host, path = urlparse.urlparse(url)[1:3]    # elems [1] and [2]
                conn = httplib.HTTPConnection(host)
                conn.request('HEAD', path)
                mys = conn.getresponse().status
            except StandardError:
                mys = 404
            if mys==200:
                try:
                    import string
                    valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
                    safename = ''.join(ch for ch in title if ch in valid_chars)

                    urllib.urlretrieve (url, self.showPath + '/' + safename + '.jpg')
                except StandardError:
                    print 'Error downloading ' + url

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
      name = name1.decode('ascii','ignore')
      import string
      valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
      safename = ''.join(ch for ch in name if ch in valid_chars)
      for icon1 in var:
          icon = icon1.decode('ascii','ignore')
          if os.path.splitext(icon)[0].lower() == safename.lower():
              return os.path.join(path, icon1);
      if len(safename) > 1 :
          for icon1 in var:
              icon = icon1.decode('ascii','ignore')
              if os.path.splitext(icon)[0].lower().find(safename.lower()) >= 0:
                  return os.path.join(path, icon1);
              if safename.lower().find(os.path.splitext(icon)[0].lower()) >= 0:
                  print os.path.splitext(icon)[0].lower()
                  print safename
                  return os.path.join(path, icon1);
      return None

    ######################################################################################################
    # Loading an array with contents
    ######################################################################################################
    def _getFiles(self, path, encoding='utf-8'):
      for (path, dirs, files) in os.walk(path.encode(encoding)):
          var = files
      return var

######################################################################################################
# Translating a (soap) detailrecord into a dictionary...
######################################################################################################
    def _detail2array(self, soapObj, fetchArt=False):
        print "Detail error returns: " + str(soapObj.webServiceEPGEventObjects.webServiceReturn.Error)
        dict = {}

        if soapObj.webServiceEPGEventObjects.webServiceReturn.Error is True:
            print soapObj.webServiceEPGEventObjects.webServiceReturn.Message
            return dict

        try:
            L = soapObj.webServiceEPGEventObjects
            if L.webServiceEPGEventObject is not None:
                prog = L.webServiceEPGEventObject
            else:
                prog = L.webServiceRecurringObject

            if prog.HasSchedule is True:
                rec = L.webServiceScheduleObject
            else:
                rec = None
        except:
            prog = None
            rec = L.webServiceScheduleObject
            dict['title'] = rec.Name.encode('utf-8')
            dict['start'] = rec.StartTime + self.dst_offset
            dict['end'] = rec.EndTime + self.dst_offset
            dict['desc'] = ""
            dict['subtitle'] = ""
            dict['channel_oid'] = rec.ChannelOid
            dict['program_oid'] = None
            dict['genres'] = ''
        if prog is not None:
            if prog.Title is not None:
                dict['title'] = prog.Title.encode('utf-8')
            else:
                dict['title'] = rec.Name.encode('utf-8')


            if prog.StartTime.year > 1:
                    dict['start'] = prog.StartTime + self.dst_offset
                    print dict['start']
                    dict['end'] = prog.EndTime + self.dst_offset
            else:
                    dict['start'] = rec.StartTime + self.dst_offset
                    dict['end'] = rec.EndTime + self.dst_offset

            if prog.Desc is not None:
                dict['desc'] = prog.Desc.encode('utf-8')
            else:
                dict['desc'] = ""

            if prog.Subtitle is not None:
                dict['subtitle'] = prog.Subtitle.encode('utf-8')
            else:
                dict['subtitle'] = ""

            if prog.OID is not 0:
                dict['channel_oid'] = prog.ChannelOid
            else:
                dict['channel_oid'] = rec.OID
            dict['program_oid'] = prog.OID
            if prog.Genres:
                dict['genres'] = prog.Genres.Genre
                for genre in prog.Genres.Genre:
                    if genre == "Movie" or genre == "Movies" or genre == "Film":
                        dict['movie'] = True
                        break
            else:
                dict['genres'] = ''

        dict['movie'] = False
        if str(dict['channel_oid']) in self.channels:
            dict['channel'] = self.channels[str(dict['channel_oid'])]
        else:
            dict['channel'] = self.channels['0']

        if fetchArt == True and self.offline == False and self.getShowIcon(dict['title']) is None:
            FanArt = None
            try:
                if prog is not None:
                    FanArt = prog.FanArt
                elif FanArt is None and rec is not None:
                    FanArt = rec.FanArt
            except:
                #print 'NEWA version does not support fanart'
                pass

            if FanArt is not None:
                url = self.getURL() +'/'+ FanArt
                print 'downloading fanart from %s' % url
                import httplib
                import urlparse
                try:
                    host, path = urlparse.urlparse(url)[1:3]    # elems [1] and [2]
                    conn = httplib.HTTPConnection(host)
                    conn.request('HEAD', path)
                    mys = conn.getresponse().status
                except StandardError:
                    mys = 404
                if mys==200:
                    try:
                        import string
                        valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
                        safename = ''.join(ch for ch in dict['title'] if ch in valid_chars)
                        urllib.urlretrieve (url, self.showPath + '/' + safename + '.jpg')

                    except StandardError:
                        print 'Error downloading ' + url

        if rec is not None:
            dict['status'] = rec.Status
            if rec.Status == "Completed" or rec.Status == "In-Progress" or rec.Status == "":
                if rec.RecordingFileName is not None:
                    f = rec.RecordingFileName
                    dict['filename'] = f
                    dict['resume'] = rec.PlaybackPosition
                else:
                    dict['filename'] = ''
                    dict['resume'] = 0
                dict['duration'] = rec.PlaybackDuration
                dict['directory'] = None
            else:
                dict['resume'] = 0
                dict['duration'] = 0
                if rec.RecordingFileName is not None:
                    dict['directory'] = rec.RecordingFileName[1:-1]
                else:
                    dict['directory'] = "Default"
            dict['recording_oid'] = rec.OID
            dict['rectype'] = rec.Type
            dict['recday'] = rec.Day
            dict['recquality'] = rec.Quality
            dict['prepadding'] = rec.PrePadding
            dict['postpadding'] = rec.PostPadding
            dict['maxrecs'] = rec.MaxRecordings
            dict['priority'] = rec.Priority

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

        #try:
        #    dict['genres'] = ""
        #except:
        #    pass

        return dict


######################################################################################################
# Translating a (json) detailrecord into a dictionary...
######################################################################################################
    def _detail2array_json(self, detailsService,fetchArt=False):

        numrec = len(detailsService['epgEventJSONObject']) -1
        error = detailsService['epgEventJSONObject']['rtn']
        #print "Detail error returns: " + str(error['Error'])
        dict = {}

        if error['Error'] is True:
            print error['Message']
            return dict


        detail =  detailsService['epgEventJSONObject']['epgEvent']
        try:
            if detail['HasSchedule'] is True:
                recording = detailsService['epgEventJSONObject']['schd']
            else:
                recording = None

            if detail['ScheduleIsRecurring'] is True:
                if detailsService['epgEventJSONObject'].has_key('recurr'):
                    recurring = detailsService['epgEventJSONObject']['recurr']
                    print 'Is recurring'
                else:
                    print detailsService['epgEventJSONObject']
                    recurring = None
            else:
                recurring = None

            if detail['OID'] == 0:
                detail = None
                dict['channel_oid'] = recording['ChannelOid']
                dict['title'] = recording['Name'].encode('utf-8')
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
            print 'unknown record error in details'

        import re

        if detail is not None:
            if detail['Title'] is not None:
                dict['title'] = detail['Title'].encode('utf-8')
            else:
                dict['title'] = rec.Name.encode('utf-8')

            print detail['StartTime'][:-1]
            #s = datetime.datetime(*map(int, re.split('[^\d]', detail['StartTime'])[:-1]))
            #e = datetime.datetime(*map(int, re.split('[^\d]', detail['EndTime'])[:-1]))
            #if iso8601.parse_date( detail['StartTime']).year > 1:
            #    dict['start'] = iso8601.parse_date(detail['StartTime']).replace(tzinfo=None) - my_offset
            #    dict['end'] = iso8601.parse_date(detail['EndTime']).replace(tzinfo=None) - my_offset

            if detail.has_key('Significance'):
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
                dict['desc'] = detail['Desc'].encode('utf-8')
            else:
                dict['desc'] = ""
            if detail['Subtitle'] is not None:
                dict['subtitle'] = detail['Subtitle'].encode('utf-8')
            else:
                dict['subtitle'] = ""

            if detail['OID'] is not 0:
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
            if detail.has_key('Season'):
                dict['season'] = detail['Season']
            else:
                dict['season'] = 0
            if detail.has_key('Episode'):
                dict['episode'] = detail['Episode']
            else:
                dict['episode'] = 0

        if str(dict['channel_oid']) in self.channels:
            dict['channel'] = self.channels[str(dict['channel_oid'])]
        else:
            dict['channel'] = self.channels['0']
        print 'fetching'
        if fetchArt == True and self.offline == False and self.getShowIcon(dict['title']) is None:
            FanArt = None
            try:
                if detail is not None:
                    if detail['FanArt'] != '':
                        FanArt = detail['FanArt']

                elif FanArt is None and rec is not None:
                    FanArt = recording['FanArt']
            except:
                #print 'NEWA version does not support fanart'
                pass

            if FanArt is not None:
                url = self.getURL() +'/'+ FanArt
                print 'getting fanart from %s' % url
                import httplib
                import urlparse
                try:
                    host, path = urlparse.urlparse(url)[1:3]    # elems [1] and [2]
                    conn = httplib.HTTPConnection(host)
                    conn.request('HEAD', path)
                    mys = conn.getresponse().status
                except StandardError:
                    mys = 404
                if mys==200:
                    try:
                        import string
                        valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
                        safename = ''.join(ch for ch in dict['title'] if ch in valid_chars)
                        urllib.urlretrieve (url,self.showPath + '/' + safename +'.jpg')
                    except StandardError:
                        print 'Error downloaing ' + url
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


        if detailsService['epgEventJSONObject'].has_key('cast'):
            dict['cast'] = detailsService['epgEventJSONObject']['cast']
        else:
            dict['cast'] = ''

        if detailsService['epgEventJSONObject'].has_key('crew'):
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
                    retDic[str(n.nodeName)] = str(n.firstChild.nodeValue.encode('utf-8'))

            retArr.append(retDic)

        return retArr
#################################################################################################################
    def jsonDate(self, dateStr, offset=datetime.datetime.min):
        #print dateStr
        try:
            d = datetime.datetime.fromtimestamp(time.mktime(time.strptime(dateStr,'%Y-%m-%dT%H:%M:%SZ'))) - self.my_offset
        except:
            d = dateutil.parser.parse(dateStr)#.astimezone(dateutil.tz.tzlocal())
        return datetime.datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)
######################################################################################################
# Creating a guid (string) for authenthication
######################################################################################################
    def _Guid(self, *args ):

        import time, random, hashlib

        """
            Generates a universally unique ID.
            Any arguments only create more randomness.
        """
        t = long( time.time() * 1000 )
        r = long( random.random()*100000000000000000L )
        try:
            a = socket.gethostbyname( socket.gethostname() )
        except:
            # if we can't get a network address, just imagine one
            a = random.random()*100000000000000000L
        data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
        h = hashlib.md5()
        h.update(data)
        data = "0000" + h.hexdigest()

        return data

######################################################################################################
# Encrypting with AES(Rijndael) for authentication
# Note: Requires PCCrypto....
######################################################################################################
    def _AESEncrypt(self, plain_text, key, iv):
        try:
            from Crypto.Cipher import AES
        except:
            return "Nothing to decrypt here"

        block_size = 16
        key_size = 32
        mode = AES.MODE_CBC

        key_bytes = key[:key_size]
        pad = block_size - len(plain_text) % block_size
        data = str(plain_text) + pad * chr(pad)
        iv_bytes = iv[:block_size]
        encrypted = AES.new(key_bytes, mode, iv_bytes).encrypt(data)
        return encrypted

######################################################################################################
# return JSON from NextPVR
######################################################################################################
    def nextJson (self,url):
        from StringIO import StringIO
        import gzip

        print url
        request = urllib2.Request(url)
        request.add_header('Content-Type', 'application/json')
        request.add_header('Accept-encoding', 'gzip')
        json_file = urllib2.urlopen(request)
        print json_file.info()
        if json_file.info().get('Content-Encoding') == 'gzip':
            jsontxt = StringIO( json_file.read())
            f = gzip.GzipFile(fileobj=jsontxt)
            next = _json.load(f)
        else:
            next = _json.load(json_file)
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
        import xml.etree.ElementTree as ET
        import codecs
        url = "http://" + self.ip + ":" + str(self.port) + '/service?method=session.initiate&ver=1.0&device=xbmc'
        print url
        try:
            request = urllib2.Request(url, headers={"Accept" : "application/xml"})
            u = urllib2.urlopen(request)
            tree = ET.parse(u)
            root = tree.getroot()
            if root.attrib['stat'] == 'ok':
                sid =  root.find('sid').text
                salt = root.find('salt').text
                #print self._hashMe(self.settings.NextPVR_PIN)
                url = "http://" + self.ip + ":" + str(self.port) + '/service?method=session.login&sid=' + sid + '&md5='+ self._hashMe(':' + self._hashMe(self.settings.NextPVR_PIN) + ':' + salt)
                print url
                request = urllib2.Request(url, headers={"Accept" : "application/xml"})
                u = urllib2.urlopen(request)
                tree = ET.parse(u)
                root = tree.getroot()
                if root.attrib['stat'] == 'ok':
                    self.sid =  root.find('sid').text
                    print self.sid
                    self.setClient()

        except Exception, err:
            print err
            self.offline = True
            self.settings.XNEWA_INTERFACE = 'JSON'


    def sidLogin_json (self):
        url = "http://" + self.ip + ":" + str(self.port) + '/public/Util/NPVR/Client/Instantiate'
        print url
        try:
            json_file = urllib2.urlopen(url)
            keys = _json.load(json_file)
            print keys
            json_file.close()
            if 'sid' in keys['clientKeys']:
                sid =  keys['clientKeys']['sid']
                print sid
                self.jsid = '?sid=' + sid
                salt = keys['clientKeys']['salt']
                print salt
                #print self._hashMe(self.settings.NextPVR_PIN)
                url = "http://" + self.ip + ":" + str(self.port) + '/public/Util/NPVR/Client/Initialize/' + self._hashMe(':' + self._hashMe(self.settings.NextPVR_PIN) + ':' + salt) + self.jsid
                print url
                json_file = urllib2.urlopen(url)
                print json_file.getcode()
                print _json.load(json_file)
                json_file.close()
                self.sid = sid
                self.setClient()
                self.offline = False
        except Exception, err:
            print err
            self.offline = True
            self.settings.XNEWA_INTERFACE = 'JSON'


######################################################################################################
# sid Login
######################################################################################################
    def getSid (self):
        return self.sid


    def setClient (self):
        if self.strClient == None:
            self.strClient = '&client=KNEWA'
            url = "http://" + self.ip + ":" + str(self.port) + '/services/service?method=setting.get&format=json&key=/Settings/Version/BuildDate&sid=' + self.sid
            print url
            try:
                json_file = urllib2.urlopen(url)
                setting = _json.load(json_file)
                print setting
                json_file.close()
                if setting.has_key('value'):
                    if setting['value'] > '161029' and self.settings.XNEWA_LIVE_SKIN:
                        self.strClient = '&client=sdl-KNEWA'
            except Exception, err:
                print err
                pass

        self.client = self.strClient + self.settings.XNEWA_MAC + '&sid=' + self.sid



######################################################################################################
# Creates a (MD5) hash of a string
######################################################################################################
    def _hashMe (self, thedata):
        import hashlib
        h = hashlib.md5()
        h.update(thedata)
        return h.hexdigest()

######################################################################################################
# Creates a byte-array with an MS representation of unicode...
######################################################################################################
    def _toMsUniCode(self, text):
        clear = unicode(text)
        bytes_clear=""
        for i in clear:
            if ord(i) < 128:
                bytes_clear += i
                bytes_clear += chr(0)
            else:
                bytes_clear += i

        return bytes_clear

######################################################################################################
# Encrypts a string with password and salt for authentication
######################################################################################################
    def _Encrypt(self, cleartext, password, salt):
        from PBKDF2 import PBKDF2
        import base64

        clearBytes = self._toMsUniCode(cleartext)

        safepw = PBKDF2(password, salt, 25)

        key = safepw.read(32) # 256-bit key

        iv = safepw.read(16) # 256-bit key
        result = self._AESEncrypt(clearBytes, key, iv)
        return base64.b64encode(result)

######################################################################################################
# Adds authentication fields to an authentication object...
######################################################################################################
    def _AddAuthentication(self, myObj, userid, password):

        from datetime import datetime
        timeString = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        encodingSalt = self._hashMe(timeString)
        print timeString
        pwdHash = self._hashMe(password)
        pwd = self._Encrypt(password, pwdHash, encodingSalt)
        id = self._Encrypt(userid, pwdHash, encodingSalt)

        myguid = self._Guid()
        #We're encrypting the date/time we used to create the salt with the guid so the decrypt of the re-passed credentials knows
        #what is used as the salt
        RL = self._Encrypt(str ( len ( id ) ), pwdHash, myguid)
        myObj.RL = RL

        rt = self._Encrypt(timeString, pwdHash, myguid)

        RTL = self._Encrypt(str ( len (rt ) ), pwdHash, myguid)
        myObj.RTL = RTL

        R = rt + id + pwd + myguid
        myObj.R = R
        return myObj

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
            print 'sending wol ' + broadcast_address
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
            msg = '\xff' * 6 + hw_addr * 16

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
    print url
    import httplib
    import urlparse
    try:
        host, path = urlparse.urlparse(url)[1:3]    # elems [1] and [2]
        conn = httplib.HTTPConnection(host)
        conn.request('HEAD', path)
        mys = conn.getresponse().status
    except:
        mys = 404
    print mys
    return mys
#################################################################################################################
def debug( value ):
    global debugIndentLvl
    if (DEBUG and value):
        try:
            if value[0] == ">": debugIndentLvl += 2
            pad = rjust("", debugIndentLvl)
            print pad + str(value)
            if value[0] == "<": debugIndentLvl -= 2
        except:
            try:
                print value
            except:
                print "Debug() Bad chars in string"

# locate server on subnet

def zeroConf(self):
    import socket
    import struct
    import sys

    message = 'X-NEWA looking for NextPVR'

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
        print 'Sending "%s"' % message
        sent = sock.sendto(message, multicast_group)

        # Look for responses from all recipients
        while True:
            try:
                data, server = sock.recvfrom(512)
            except socket.timeout:
                print 'Timed out, no more responses'
                break
            else:
                print data.rstrip('\0')
                self.ip = data.split(':')[0]
                self.port = data.split(':')[1]
                break
    finally:
        sock.close()

