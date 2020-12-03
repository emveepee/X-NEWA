from __future__ import print_function
from __future__ import division

from future import standard_library
standard_library.install_aliases()
from builtins import chr
from builtins import str
from builtins import hex
from builtins import range
from builtins import object

import time
from  datetime import datetime, timedelta

from dateutil import parser
import tempfile
import os.path
import pickle as pickle
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from kodi_six.utils import py2_encode, py2_decode
import sys
from fix_utf8 import smartUTF8
from XNEWAGlobals import *
import http.client
import re

if sys.version_info >=  (2, 7):
    import json as _json
else:
    try:
        import simplejson as _json
    except:
        import json as _json


__language__ = xbmcaddon.Addon().getLocalizedString

try:
    from urllib.parse import urlparse, quote, unquote
    from urllib.request import urlopen, Request, urlretrieve
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError, URLError
    from urlparse import urlparse
    from urllib import quote, unquote, urlretrieve

try:
    from httplib import HTTPException
except:
    from http.client import HTTPException

def doRequest5(self, method, isJSON = True):
    retval = False
    getResult = None
    url = "http://" + self.ip + ":" + str(self.port) + '/service?method=' + method
    if (not 'session.initiate' in method):
        url += '&sid=' + self.sid
    xbmc.log(url)
    try:
        if isJSON:
            request = Request(url, headers={"Accept" : "application/json"})
            json_file = urlopen(request)
            getResult = _json.load(json_file)
            json_file.close()
            if 'stat' in getResult and getResult['stat'] != 'ok':
                if getResult['code'] == 8 and not method.startswith('session'):
                    sidLogin5(self)
                    if self.offline == False:
                        return doRequest5(self, method)
            else:
                retval = True
        else:
            response = urlopen(url)
            getResult = response.read()
            response.close()
            retval = True
    except HTTPError as e:
        print (e)
        xbmc.log("HTTPError")
    except URLError as e:
        print (e)
        xbmc.log("URLError")
    except HTTPException as e:
        print (e)
        xbmc.log("HTTPException")
    except Exception as e:
        xbmc.log(str(e))

    return retval, getResult

def  sidLogin5(self):
    self.settings.XNEWA_INTERFACE = "Version5"
    cached = 'sid.p'
    if self.checkCache(cached):
        login = self.myCachedPickleLoad(cached)
        self.sid =  login['sid']
        method = 'session.valid'
        ret, keys = doRequest5(self,method)
        if ret == True and keys['stat'] == 'ok':
            xbmc.log(self.sid)
            setClient5(self)
            self.offline = False
            return
    method = 'session.initiate&ver=1.0&device=jellyfin'
    ret, keys = doRequest5(self,method)
    if ret == True:
        self.sid =  keys['sid']
        xbmc.log(self.sid)
        self.jsid = '?sid=' + self.sid
        salt = keys['salt']
        xbmc.log(salt)
        method = 'session.login&md5=' + self._hashMe(':' + self._hashMe(self.settings.NextPVR_PIN) + ':' + salt)
        ret, login  = doRequest5(self,method)
        if ret and login['stat'] == 'ok':
            self.sid =  login['sid']
            xbmc.log(self.sid)
            setClient5(self)
            self.offline = False
            self.myCachedPickle(keys,cached)
        else:
            self.sid = 'xnewa'
    else:
        self.offline = True
        self.settings.XNEWA_INTERFACE = 'JSON'

def setClient5(self):
    if self.strClient == None:
        self.strClient = '&client=KNEW5'
        method = 'setting.list'
        ret, settings = doRequest5(self,method)
        if ret == True:
            if 'nextPVRVersion' in settings:
                xbmc.log(settings['nextPVRVersion'])
            if self.settings.XNEWA_LIVE_SKIN:
                self.strClient = '&client=sdl-KNEW5'
            self.defaultSchedule = {}
            self.defaultSchedule['pre_padding_min'] = int(settings['prePadding'])
            self.defaultSchedule['post_padding_min'] = int(settings['postPadding'])
            self.defaultSchedule['days_to_keep'] = 0


    self.client = self.strClient + self.settings.XNEWA_CLIENT + '&sid=' + self.sid


def getRecDirList_v5(self):

    dirs = {}
    xbmc.log("getRecDirList v5 start")
    setting = self.getSettingJson('/Settings/Recording/RecordingDirectory')
    if setting != None:
        if 'value' in setting:
            dirs['Default'] = setting['value']
    setting = self.getSettingJson('/Settings/Recording/ExtraRecordingDirectories')
    if setting != None:
        if 'value' in setting:
            if setting['value'] != '':
                extras  = setting['value'].split('~')
                for i in range(0,len(extras),2):
                    try:
                        dirs[extras[i]] = extras[i+1]
                    except:
                        xbmc.log('Setting error ' + setting['value'])

    xbmc.log("getRecDirList v5 end")
    return dirs

def getChannelList_v5(self):
    xbmc.log("getChannelList v5 start")
    dic = {}
    cnt = 0
    dic['0']= (u"Unknown",'0')
    myDlg = None
    try:
        import imghdr
        import glob
        method = 'channel.list'
        ret, channels = doRequest5(self,method)
        if ret == False:
            return dic
        for channel in channels['channels']:
            if (channel['channelIcon']):
                cnt= cnt+1
        if cnt > 0 and self.settings.XNEWA_WEBCLIENT == False:
            icons = glob.glob(os.path.join(self.cached_channelPath,'*.*'))
            if cnt > len(icons) + 20:
                myDlg = xbmcgui.DialogProgress()
                myDlg.create(smartUTF8(__language__(30154)), smartUTF8(__language__(30139)))
            cnt = 0
        for channel in channels['channels']:
            if myDlg != None:
                completed = 100 * cnt//len(channels)
                cnt = cnt + 1
                myDlg.update(completed, py2_decode(channel['channelName']))
            if 'channelNumber' in channel:
                dic[str(channel['channelId'])] = ( py2_decode(channel['channelName']),str(channel['channelNumber']),str(channel['channelMinor']) )
            if channel['channelIcon']:
                try:
                    import string
                    valid_chars = "!@#&-_.,() %s%s" % (string.ascii_letters, string.digits)
                    safename = ''.join(ch for ch in channel['channelName'] if ch in valid_chars)
                    output = os.path.join(self.channelPath,safename+".*")
                    icon = glob.glob(output)
                    if not icon:
                        method = 'channel.icon&channel_id=' + str(channel['channelId'])
                        ret, binaryIcon = doRequest5(self,method,False)
                        if ret == True:
                            unknown = os.path.join(self.channelPath,"unknown")
                            with open(unknown, 'wb')  as outfile:
                                outfile.write(binaryIcon)
                            img = imghdr.what(unknown)
                            if img == "png":
                                os.rename(unknown, os.path.join(self.channelPath,py2_decode(safename)+".png"))
                            elif img == "jpeg":
                                os.rename(unknown, os.path.join(self.channelPath,py2_decode(safename)+".jpg"))
                            elif img is None:
                                xbmc.log(py2_decode(safename) + " is unknown")
                            else:
                                xbmc.log(py2_decode(safename) + " Type " + img)
                    else:
                        pass
                except Exception as err:
                    xbmc.log(str(err))
                    xbmc.log(str(channel['channelNum']) + " Error")

                pass
            else:
                pass
    except Exception as err:
        xbmc.log(str(err))
    if myDlg != None:
        myDlg.close()
    xbmc.log("getChannelList v5 end")
    return dic

def getChannelGroupList_v5(self):

    xbmc.log("getChannelGroupList v5 start")
    groups = []
    groups.append('All Channels')
    method = 'channel.groups'
    ret, myGroups = doRequest5(self,method)
    if ret:
        for group in myGroups['groups']:
            if group != 'All Channels':
                groups.append(py2_encode(group))
    else:
        xbmc.log('getChannelGroupList v5 error')
        groups = None
    xbmc.log("getChannelGroupList v5 end")
    return groups

def getEPGGenres_v5(self):

    xbmc.log("getEPGGenres v5 start")
    dic = {}
    dic['xnewa'] = 0
    method = 'system.genre'
    ret, epgGenres = doRequest5(self,method)
    if ret:
        for genre in epgGenres:
            try:
                if int(genre['color'],16) !=0:
                    dic[genre['name']] = int(genre['color'],16)
            except:
                pass
    xbmc.log("getEPG Genres v5 end")
    return dic

def getUpcomingRecordings_v5(self, amount=0):

    xbmc.log("getUpcomingRecordings v5 start")
    pending = []
    method = 'recording.list'
    ret, recordings = doRequest5(self,method)
    if ret:
        for recording in recordings['recordings']:
            try:
                theDict = recording2dict_v5(self,recording)
                pending.append(theDict)
            except:
                pass
    xbmc.log("getUpcomingRecordings v5 end")
    return pending


def getRecentRecordings_v5(self, amount=0, showName=None, sortTitle=True, sortDateDown=True, recDir=None):

    xbmc.log("getRecentRecordings v5 start")
    recent = []
    if amount !=0:
        method = 'recording.list&filter=recent'
    else:
        method = 'recording.list&filter=ready'
    ret, recordings = doRequest5(self,method)
    if ret:
        for recording in recordings['recordings']:
            try:
                if showName == None or showName == recording['name']:
                    theDict = recording2dict_v5(self,recording)
                    recent.append(theDict)
            except:
                pass
    xbmc.log("getRecentRecordings v5 end")
    return recent

def getRecording_v5(self, recording_id):

    xbmc.log("getRecording v5 start")
    theDict = {}
    method = 'recording.list&recording_id=' + str(recording_id)
    ret, recordings = doRequest5(self,method)
    if ret:
        for recording in recordings['recordings']:
            try:
                theDict = recording2dict_v5(self,recording,setWatched=False)
            except:
                pass
    xbmc.log("getRecording v5 end")
    return theDict


def recording2dict_v5(self, recording, recDir=None,setWatched=True):
    import re
    theDict = {}
    if recording['status'] == 'conflict':
        theDict['schdConflicts'] = True

    theDict['title'] = py2_decode(recording['name'])
    theDict['start'] = jsonDate_v5(self,recording['startTime'])
    theDict['end'] = jsonDate_v5(self,recording['startTime'] + recording['duration'])
    theDict['desc'] = py2_decode(recording['desc'])
    m = re.match(r'S(\d{1,2})E(\d{1,3})(?: - (.+))?',recording['subtitle'])
    if m:
        theDict['season'] = m.group(1)
        theDict['episode'] = m.group(2)
        if (len(m.groups())==3):
            theDict['subtitle'] = py2_decode(m.group(3))
        else:
            theDict['subtitle'] = ''
    else:
        theDict['subtitle'] = py2_decode(recording['subtitle'])
        if 'season' in recording:
            theDict['season'] = recording['season']
        else:
            theDict['season'] = 0
        if 'episode' in recording:
            theDict['episode'] = recording['episode']
        else:
            theDict['episode'] = 0
    if 'significance' in recording:
        theDict['significance'] = recording['significance']
    else:
        theDict['significance'] = ''

    theDict['program_oid'] = recording['epgEventId']
    #theDict['priority'] = rec['Priority'] v5
    if recording['recurring'] == True:
        theDict['rectype'] = 'Multiple'
    else:
        theDict['rectype'] = self.SCHEDULE_ONCE
    if 'file' in recording:
        if recording['status'] == "ready" or recording ['status'] == "recording":
            if recDir != None and not recording['file'].startswith(recDir):
                return None
            theDict['filename'] = recording['file']
            if 'playbackPosition' in recording:
                theDict['resume'] = recording['playbackPosition']
            else:
                theDict['resume'] = 0
            theDict['duration'] = recording['duration']
            theDict['directory'] = ''
            theDict['rec'] = False
            if self.settings.XNEWA_COLOURS != None:
                foundColour = False
                if 'red' in self.settings.XNEWA_COLOURS and recording['red'] :
                    foundColour = True
                elif 'green' in self.settings.XNEWA_COLOURS  and recording['green'] :
                    foundColour = True
                elif 'yellow' in self.settings.XNEWA_COLOURS and recording['yellow']:
                    foundColour = True
                elif 'blue' in self.settings.XNEWA_COLOURS and recording['blue']:
                    foundColour = True

                if foundColour == False:
                    return None
        else:
            theDict['filename'] = ''
            theDict['resume'] = 0
            theDict['directory'] = recording['file'][1:-1]
            theDict['rec'] = True

        if theDict['duration'] !=0 and recording['status'] == 'ready' and setWatched:
            completed = theDict['duration'] - theDict['resume']
            if completed < 60:
                theDict['status'] = 'Watched'
            elif theDict['resume'] < 60:
                theDict['status'] = 'Not Watched'
            else:
                theDict['status'] = 'Partial ' + str(100 * theDict['resume']//theDict['duration']) + ' %'
        else:
            if (recording['status']=='recording'):
                theDict['status'] = "In-Progress"
            elif (recording['status']=='ready'):
                theDict['status'] = "Completed"
            else:
                theDict['status'] = recording['status'].capitalize()
    else:
        theDict['priority'] = ""
        #theDict['rectype'] = ""
        theDict['status'] = recording['status'].capitalize()
        theDict['recording_oid'] = ""
        theDict['rec'] = False
        theDict['resume'] = 0
    theDict['recording_oid'] = recording['id']
    theDict['channel_oid'] = recording['channelId']
    if str(theDict['channel_oid']) in self.channels:
        theDict['channel'] = self.channels[str(theDict['channel_oid'])]
    else:
        theDict['channel'] = self.channels['0']

    theDict['movie'] = False
    return theDict

def getScheduledRecordings_v5(self):

    xbmc.log("getScheduledRecordings v5 start")
    retArr = []
    method = 'recording.recurring.list'
    ret, recurrings = doRequest5(self,method)
    if ret:
        for recurring in recurrings['recurrings']:
            theDict = recurring2dict_5(self,recurring)
            retArr.append(theDict)

    xbmc.log("getScheduledRecording v5 end")
    return retArr


######################################################################################################
# Translating a (v5 ) recurring object into a dictionary object...
######################################################################################################
def recurring2dict_5(self, recurring):
    theDict = {}
    if 'epgTitle' in recurring:
        theDict['title'] = py2_encode(recurring['epgTitle'])
    else:
        theDict['title'] = 'Unnamed'

    if 'name' in recurring:
        theDict['name'] = py2_encode(recurring['name'])
    else:
        theDict['name'] = 'Unnamed'

    if 'onlyNewEpisodes' in recurring:
        theDict['onlyNew'] = recurring['onlyNewEpisodes']
    else:
        theDict['onlyNew'] = False

    theDict['rectype'] = recurring['period']
    m = re.match(r'(\d+:\d\d) ([AP]M)*\D+(\d+:\d\d) ([AP]M)*\s*\((\w+)( - (\w+))*',recurring['period'])
    if m:
        try:
            theDict['start'] = strptimeKodi(m.group(1),'%H:%M')
            if m.group(2)=='PM':
                theDict['start'] += timedelta(hours=12)
            theDict['end'] = strptimeKodi(m.group(3),'%H:%M')
            if m.group(4)=='PM':
                theDict['end'] += timedelta(hours=12)
            theDict['rectype'] = m.group(5)
        except Exception as err:
            print(err)
    else:
        theDict['start'] = strptimeKodi("00:00",'%H:%M')
        theDict['end'] = strptimeKodi("23:59",'%H:%M')
    try:
        if reccurring['directoryID'] == '':
            theDict['directory'] = "Default"
        else:
            theDict['directory'] = recurring['directoryID'][1:-1]
    except:
        theDict['directory'] = "Default"
    theDict['subtitle'] = ''
    theDict['program_oid'] = 0
    theDict['rec'] = False

    theDict['priority'] = str(0) #recurring['Priority']
    theDict['status'] = ''
    theDict['recording_oid'] = recurring['id']
    theDict['channel_oid'] = recurring['channelID']
    if str(theDict['channel_oid']) in self.channels:
        theDict['channel'] = self.channels[str(theDict['channel_oid'])]
    else:
        theDict['channel'] = self.channels['0']
    theDict['genres'] = ''
    theDict['recquality'] = 'High'
    theDict['prepadding'] = str(recurring['prePadding'])
    theDict['postpadding'] = str(recurring['postPadding'])
    theDict['maxrecs'] = recurring['keep']
    if 'days' in recurring:
        theDict['day'] = recurring['days'].split(',')
    else:
        theDict['day'] = 'Any'
    #theDict['allChannels'] = rec['allChannels']
    theDict['movie'] = False
    theDict['desc'] = ''
    theDict['type'] = recurring['type']
    return theDict

def setLastPlayedPosition(self, recording_id, position):

    xbmc.log("setLastPlayedPosition start")
    method = 'recording.watched.set'
    method += '&recording_id=' + str(recording_id) + '&position=' + str(position)
    ret, result = doRequest5(self,method)
    if not ret:
        print (result)


def epgTag2dict_v5(self, passedData):
    theDict = {}
    #passedData [programme['oid'],
    # programme['subtitle'],
    # programme['desc'],
    # programme['title'],
    # nEpgPos,
    # i,
    # programme['start'],
    # programme['end'],
    # tagrec]
    # channel
    theDict['title'] = passedData[3]
    theDict['start'] = passedData[6]
    theDict['end'] = passedData[7]
    theDict['desc'] = passedData[2]
    theDict['status'] = ''
    theDict['season'] = 0
    theDict['episode'] = 0
    theDict['subtitle'] = passedData[1]
    theDict['significance'] = ''
    theDict['program_oid'] = passedData[0]
    theDict['filename'] = ''
    theDict['resume'] = 0
    theDict['priority'] = ""
    theDict['recording_oid'] = passedData[8]
    if theDict['recording_oid'] == None:
        theDict['rec'] = False
        theDict['rectype'] = ''
        theDict['status'] = ''
    else:
        theDict['rec'] = True
        theDict['rectype'] = 'E'
        theDict['status'] = 'In-Progress'

    theDict['channel_oid'] = passedData[9][2]
    if str(theDict['channel_oid']) in self.channels:
        theDict['channel'] = self.channels[str(theDict['channel_oid'])]
    else:
        theDict['channel'] = self.channels['0']
    theDict['movie'] = False
    theDict['genres'] = {}
    return theDict

def getGuideInfo_v5(self,start,channelId=None):

    xbmc.log("getGuideInfo v5 start")
    retArr = []
    method = 'channel.listings.current'
    if start != None:
        method += start
    if channelId != None:
        method += channelId
    ret, listings = doRequest5(self,method)
    if ret:
        for listing in listings:
            retArr.append(getGuideData(self,listing))

    xbmc.log("getGuideInfo v5 end")
    return retArr

def getGroupGuideInfo_v5(self,start,groupId):

    xbmc.log("getGroupGuideInfo v5 start")
    retArr = []

    method = 'channel.list&group_id=' + quote(groupId)
    ret, channels = doRequest5(self,method)
    if ret:
        for channel in channels['channels']:
            method = 'channel.listings.current&channel_id='  + str(channel['channelId'])

            if start != None:
                method += start

            ret, listings = doRequest5(self,method)
            if ret:
                for listing in listings:
                    retArr.append(getGuideData(self,listing))

    xbmc.log("getGroupGuideInfo v5 end")
    return retArr

def getGuideData(self,listing):
    channel = {}
    channel['name'] = py2_decode(listing['channel']['channel_name'])
    channel['oid'] = listing['channel']['channel_id']
    channel['num'] = listing['channel']['channel_formatted_number']
    progs = []
    for program in listing['channel']['listings']:
        dic = {}
        dic['title'] = py2_decode(program['name'])
        if 'description' in program:
            dic['desc'] = py2_decode(program['description'])
        else:
            dic['desc'] = ''
        if 'subtitle' in program:
            dic['subtitle'] = py2_decode(program['subtitle'])
        else:
            dic['subtitle'] = ''
        if 'season' in program:
            dic['season'] = program['season']
        else:
            dic['season'] = 0
        if 'episode' in program:
            dic['episode'] = program['episode']
        else:
            dic['episode'] = 0
        dic['start'] = datetime.fromtimestamp(program['start'])
        dic['end'] = datetime.fromtimestamp(program['end'])
        if self.miniEPG > dic['end']:
            self.miniEPG = dic['end']

        dic['oid'] = program['id']
        if 'recording_status' in program:
            dic['rec'] = True
            dic['recording_id'] = program['recording_id']
        else:
            dic['rec'] = False

        dic['genreColour'] = 0
        if 'genres' in program:
            for genre in program['genres']:
                dic['genres'] = genre
                try:
                    if self.genresColours[genre] != 0:
                        dic['genreColour'] = str(hex(self.genresColours[genre]))
                except:
                    pass
        else:
            dic['genres'] = ''
        if 'firstrun' in program:
            dic['firstrun'] = program['firstrun']
        else:
            dic['firstrun'] = False
        progs.append(dic)
        dic['significance'] = ''
    channel['progs'] = progs
    return channel

def getRecordingsSummary_v5(self):
    xbmc.log("getRecordingsSummary v5 start")
    recordings = self.getRecentRecordings(self.settings.NextPVR_USER, self.settings.NextPVR_PW)
    summary = {}
    for recording in recordings:
        if recording['title'] in summary:
            summary[recording['title']][2] += 1
        else:
            mylist = []
            mylist.append(recording['title'])
            mylist.append(recording['start'])
            mylist.append(1)
            summary[recording['title']] = mylist
    retArr = []
    for recording in summary:
        theDict = {}
        theDict['title'] = py2_decode(summary[recording][0])
        theDict['start'] =  summary[recording][1]
        theDict['count'] = summary[recording][2]
        retArr.append(theDict)
    xbmc.log("getRecordingsSummary v5 end")
    return retArr

def cancelRecording_v5(self, progDetails):
    xbmc.log(str(progDetails))
    if progDetails['rectype'].lower() == "recurring" or progDetails['status'].lower() == "recurring" or 'day' in progDetails:
        debug("Cancelling Recurring")
        method = 'recording.recurring.delete&recurring_id=' + str(progDetails['recording_oid'])
    elif progDetails['status'].lower() == "pending" or progDetails['status'].lower() == "in-progress":
        debug("Cancelling")
        method = 'recording.delete&recording_id=' + str(progDetails['recording_oid'])
    elif progDetails['status'].lower() == "completed":
        debug("Deleting")
        method = 'recording.delete&recording_id=' + str(progDetails['recording_oid'])
    elif progDetails['status'].lower() == "failed"  or progDetails['status'].lower() == "conflict" :
        debug("Deleting record")
        method = 'recording.delete&recording_id=' + str(progDetails['recording_oid'])
    else: ## "deleted":
        debug("Cancelling and Deleting")
        method = 'unknown'
    xbmc.log(method)
    ret, delete = doRequest5(self,method)
    if ret:
        self.changedRecordings = True
    else:
        print(delete)
    return ret

def scheduleRecording_v5(self, progDetails):
    rc = -1
    xbmc.log(str(progDetails))
    common = '&pre_padding={0}&post_padding={1}'.format(progDetails['prepadding'],progDetails['postpadding'])
    if progDetails['directory'] != "Default":
        common += progDetails['directory']

    if progDetails['rectype'] == 'Record Once':
        method = 'recording.save{0}&event_id={1}'.format(common,progDetails['program_oid'])
    else:
        common = 'recording.recurring.save' + common + '&keep=' + str(progDetails['maxrecs'])
        if progDetails['rectype'] == "Record Season (NEW episodes on this channel)":
            method = '{0}&event_id={1}&only_new=true'.format(common,progDetails['program_oid'])
        elif progDetails['rectype'] == "Record Season (All episodes on this channel)":
            method = '{0}&event_id={1}'.format(common,progDetails['program_oid'])
        elif progDetails['rectype'] == "Record Season (Daily, this timeslot)":
            method = '{0}&event_id={1}&timeslot=true&recurring_type=3'.format(common,progDetails['program_oid'])
        elif progDetails['rectype'] == "Record Season (Weekly, this timeslot)":
            method = '{0}&event_id={1}&timeslot=true&recurring_type=4'.format(common,progDetails['program_oid'])
        elif progDetails['rectype'] == "Record Season (Monday-Friday, this timeslot)":
            method = '{0}&event_id={1}&timeslot=true&recurring_type=5'.format(common,progDetails['program_oid'])
        elif progDetails['rectype'] == "Record Season (Weekends, this timeslot)":
            method = '{0}&event_id={1}&timeslot=true&recurring_type=6'.format(common,progDetails['program_oid'])
        elif progDetails['rectype'] == "Record All Episodes, All Channels":
            #method = '{0}&name={1}&start_time={2}&end_time={3}&keyword={4}'.format(common,quote(progDetails['title']),getTimeStamp(progDetails['start']),getTimeStamp(progDetails['end']),quote(progDetails['title'].replace("'","''")))
            method = '{0}&name={1}&start_time={2}&end_time={3}&keyword=title+like+\'{4}\''.format(common,quote(progDetails['title']),getTimeStamp(progDetails['start']),getTimeStamp(progDetails['end']),quote(progDetails['title'].replace("'","''")))
        else:
            xbmc.log("Unknown rectype")
            return 500
    ret, status = doRequest5(self,method)
    if ret:
        rc = 200
    else:
        print(status)
    return rc

def jsonDate_v5(self, dateStr):
    try:
        d = datetime.fromtimestamp(dateStr)
    except Exception as e:
        print(e)
        d = dateutil.parser.parse(dateStr)#.astimezone(dateutil.tz.tzlocal())
    return datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)

def getTimeStamp(dateValue):
    import calendar
    return str(int(calendar.timegm(dateValue.timetuple())))

def GetNextPVRInfo_v5(self):
    dic = {}
    xbmc.log("getRecording v5 start")

    dic['directory'] = None

    method = 'system.space'
    ret, system = doRequest5(self,method)
    if ret:
        space = {}
        space['free'] = system[0]['free'] // 1000000000
        space['total'] = system[0]['total'] // 1000000000
        if (space['total'] == 0):
            space['total'] = 1
        dic['space'] = space

    method = 'system.recordings'
    ret, system = doRequest5(self,method)
    if ret:
        pass
    else:
        system = _json.loads('{"pending": 1,"inprogress": 2,"available": 3,"failed": 4,"conflict": 5,"deleted": 6}')

    schedule = {}
    schedule['Available'] = str(system['available'])
    schedule['Deleted'] = str(system['deleted'])
    schedule['Failed'] = str(system['failed'])
    schedule['Pending'] = str(system['pending'])
    schedule['InProgress'] = str(system['inprogress'])
    schedule['Recurring'] = ''
    schedule['Conflict'] = str(system['conflict'])
    dic['schedule'] = schedule

    return dic
def searchProgram_v5(self, needle,option):

    xbmc.log("searchProgram v5 start")
    method = 'channel.listings.search'
    search = []
    if option == 0:
        parameters = '&title=%{0}%'.format(needle)
    elif option == 1:
        parameters = '&description=%{0}%'.format(needle)
    elif option == 2:
        parameters = '&subtitle=%{0}%'.format(needle)
    if option == 3:
        parameters = '&title=%{0}%+or+description=%{0}%+or+subtitle=%{0}%'.format(needle)
    method += parameters
    xbmc.log(method)
    ret, results = doRequest5(self,method)
    if ret:
        for listing in results['listings']:
            hit = {}
            hit['rec'] = False
            hit['title'] = listing['name']
            hit['start'] = jsonDate_v5(self,listing['start'])
            hit['end'] = jsonDate_v5(self,listing['end'])
            if str(listing['channelId']) in self.channels:
                hit['channel'] = self.channels[str(listing['channelId'])]
            else:
                hit['channel'] = self.channels['0']
            hit['channel_oid'] = listing['channelId']
            hit['desc'] = listing['description']
            if 'subtitle' in listing:
                hit['subtitle'] = listing['subtitle']
            else:
                hit['subtitle'] = ''
            hit['program_oid'] = listing['id']
            search.append(hit)

    xbmc.log("searchProgram v5 end")
    return search

def logMessage_v5(self,msg):
    method = 'system.log&msg=' + quote(msg)
    ret, result = doRequest5(self,method)
    if not ret:
        print (result)

def getRecurringRecord(self,oid):
    schedules = self.getScheduledRecordings(None,None)
    for schedule in schedules:
        if schedule['recording_oid'] == oid:
            return schedule
    return None

def updateRecording_v5(self, progDetails):
    if progDetails['rectype'] == 'Recurring':
        pass
    else:
        pass
    return None

def strptimeKodi(date_string,format):
    #https://forum.kodi.tv/showthread.php?tid=112916&pid=2416605#pid2416605
    try:
        return datetime.strptime(date_string, format)
    except TypeError:
        return datetime(*(time.strptime(date_string, format)[0:6]))
    return None
