from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import time
import string
from datetime import datetime
try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError
import json
import os
from decimal import Decimal
import operator
import re
import xbmc

try:
  Log
except NameError:
    class Logger(object):
        def __init__(self):
            return

        def Debug(self, s):
            xbmc.log(s)

        def Info(self, s):
            xbmc.log(s)

        def Warn(self, s):
            xbmc.log(s)

        def Error(self, s):
            xbmc.log(s)

        def Critical(self, s):
            xbmc.log(s)

        def Exception(self, s):
            xbmc.log(s)

    Log = Logger()

URL_DISCOVER = 'http://my.hdhomerun.com/discover'
URL_GUIDE_BASE = 'http://my.hdhomerun.com/api/guide.php?DeviceAuth='
URL_RECORDING_RULES = 'http://my.hdhomerun.com/api/recording_rules?DeviceAuth='

def searchString(needle,haystack):
    needles = needle.split(' ')
    for n in needles:
        if re.search(n, haystack, re.IGNORECASE):
            return True

class SortType(object):
    asc = 0
    desc = 1

class GroupType(object):
    All = 0
    SeriesID = 1
    Category = 2

class SeriesSummary(object):
    SeriesID = ""
    ImageURL = ""
    EpisodeCount = 0

    def __init__(self,SeriesID,ImageURL):
        self.SeriesID = SeriesID
        self.ImageURL = ImageURL
        self.EpisodeCount = 1

    def getSeriesID(self):
        return self.SeriesID

    def getImageURL(self):
        return self.ImageURL

    def getEpisodeCount(self):
        return self.EpisodeCount

    def addEpisodeCount(self,ct):
        self.EpisodeCount = self.EpisodeCount + ct

class ChannelInfo(object):
    GuideNumber = ""
    GuideName = ""
    ImageURL = ""
    Affiliate = ""
    ProgramInfos = []
    VideoCodec = ""
    AudioCodec = ""
    HD =  -1
    URL = ""
    Favorite = -1
    Tuner = None

    def __init__(self,Tuner):
        self.Tuner = Tuner
        return

    def parse(self,parsestr,PyHDHR):
        if 'GuideNumber' in parsestr:
            self.GuideNumber = parsestr['GuideNumber']
        if 'GuideName' in parsestr:
            self.GuideName = parsestr['GuideName']
        if 'ImageURL' in parsestr:
            self.ImageURL = parsestr['ImageURL']
        if 'Affiliate' in parsestr:
            self.Affiliate = parsestr['Affiliate']
        if 'Guide' in parsestr:
            self.ProgramInfos = []
            for guideitem in parsestr['Guide']:
                programinfo = ProgramInfo()
                programinfo.parse(guideitem,PyHDHR)
                self.ProgramInfos.append(programinfo)
        if 'VideoCodec' in parsestr:
            self.VideoCodec = parsestr['VideoCodec']
        if 'AudioCodec' in parsestr:
            self.AudioCodec = parsestr['AudioCodec']
        if 'HD' in parsestr:
            self.HD = parsestr['HD']
        if 'URL' in parsestr:
            self.URL = parsestr['URL']
        if 'Favorite' in parsestr:
            self.Favorite = parsestr['Favorite']

    def getProgramInfos(self):
        return self.ProgramInfos

    def getGuideNumber(self):
        return self.GuideNumber

    def getGuideName(self):
        return self.GuideName

    def getImageURL(self):
        return self.ImageURL

    def getAffiliate(self):
        return self.Affiliate

    def getVideoCodec(self):
        return self.VideoCodec

    def getAudioCodec(self):
        return self.AudioCodec

    def getHD(self):
        return self.HD

    def getURL(self):
        return self.URL

    def getFavorite(self):
        return self.Favorite

    def getTuner(self):
        return self.Tuner

class ProgramInfo(object):
    SeriesID = ""
    EpisodeNumber = ""
    EpisodeTitle = ""
    Title = ""
    ImageURL = ""
    OriginalAirdate = 0
    Synopsis = ""
    StartTime = 0
    ProgramFilters = []
    EndTime = 0

    def __init__(self):
        return

    def parse(self,parsestr,PyHDHR):
        if 'SeriesID' in parsestr:
            self.SeriesID = parsestr['SeriesID']
        if 'EpisodeNumber' in parsestr:
            self.EpisodeNumber = parsestr['EpisodeNumber']
        if 'EpisodeTitle' in parsestr:
            self.EpisodeTitle = parsestr['EpisodeTitle']
        if 'Title' in parsestr:
            self.Title = parsestr['Title']
        if 'ImageURL' in parsestr:
            self.ImageURL = parsestr['ImageURL']
        if 'OriginalAirdate' in parsestr:
            self.OriginalAirdate = parsestr['OriginalAirdate']
        if 'Synopsis' in parsestr:
            self.Synopsis = parsestr['Synopsis']
        if 'StartTime' in parsestr:
            self.StartTime = parsestr['StartTime']
        if 'EndTime' in parsestr:
            self.EndTime = parsestr['EndTime']
        if 'Filter' in parsestr:
            for filter in parsestr['Filter']:
                f = PyHDHR.addProgramFilter(ProgramFilter(filter))
                self.addProgramFilter(f)

    def getSeriesID(self):
        return self.SeriesID

    def getEpisodeNumber(self):
        return self.EpisodeNumber

    def getEpisodeTitle(self):
        return self.EpisodeTitle

    def getTitle(self):
        return self.Title

    def getImageURL(self):
        return self.ImageURL

    def getOriginalAirdate(self):
        return self.OriginalAirdate

    def getSynopsis(self):
        return self.Synopsis

    def getStartTime(self):
        return self.StartTime

    def addProgramFilter(self,ProgramFilter):
        self.ProgramFilters.append(ProgramFilter)

    def getProgramFilters(self):
        return self.ProgramFilters

    def getEndTime(self):
        return self.EndTime

class ProgramFilter(object):
    Name = ""

    def __init__(self,Name):
        self.Name = Name

    def getName(self):
        return self.Name

class RecordedProgram(object):
    Category =  ""
    ChannelAffiliate = ""
    ChannelImageURL =  ""
    ChannelName =  ""
    ChannelNumber =  ""
    EndTime = 0
    EpisodeNumber =  ""
    EpisodeTitle = ""
    FirstAiring = 0
    ImageURL =  ""
    OriginalAirdate = 0
    ProgramID =  ""
    RecordEndTime = 0
    RecordStartTime = 0
    RecordSuccess = -1
    SeriesID =  ""
    StartTime = 0
    Synopsis =  ""
    Title =  ""
    DisplayGroupID =  ""
    DisplayGroupTitle =  ""
    PlayURL =  ""
    CmdURL =  ""

    def __init__(self):
        return

    def parse(self,parsestr):
        if 'Category' in parsestr:
            self.Category = parsestr['Category']
        if 'ChannelAffiliate' in parsestr:
            self.ChannelAffiliate = parsestr['ChannelAffiliate']
        if 'ChannelImageURL' in parsestr:
            self.ChannelImageURL = parsestr['ChannelImageURL']
        if 'ChannelName' in parsestr:
            self.ChannelName = parsestr['ChannelName']
        if 'ChannelNumber' in parsestr:
            self.ChannelNumber = parsestr['ChannelNumber']
        if 'EndTime' in parsestr:
            self.EndTime = parsestr['EndTime']
        if 'EpisodeNumber' in parsestr:
            self.EpisodeNumber = parsestr['EpisodeNumber']
        if 'EpisodeTitle' in parsestr:
            self.EpisodeTitle = parsestr['EpisodeTitle']
        if 'FirstAiring' in parsestr:
            self.FirstAiring = parsestr['FirstAiring']
        if 'ImageURL' in parsestr:
            self.ImageURL = parsestr['ImageURL']
        if 'OriginalAirdate' in parsestr:
            self.OriginalAirdate = parsestr['OriginalAirdate']
        if 'ProgramID' in parsestr:
            self.ProgramID = parsestr['ProgramID']
        if 'RecordEndTime' in parsestr:
            self.RecordEndTime = parsestr['RecordEndTime']
        if 'RecordStartTime' in parsestr:
            self.RecordStartTime = parsestr['RecordStartTime']
        if 'RecordSuccess' in parsestr:
            self.RecordSuccess = parsestr['RecordSuccess']
        if 'SeriesID' in parsestr:
            self.SeriesID = parsestr['SeriesID']
        if 'StartTime' in parsestr:
            self.StartTime = parsestr['StartTime']
        if 'Synopsis' in parsestr:
            self.Synopsis = parsestr['Synopsis']
        if 'Title' in parsestr:
            self.Title = parsestr['Title']
        if 'DisplayGroupID' in parsestr:
            self.DisplayGroupID = parsestr['DisplayGroupID']
        if 'DisplayGroupTitle' in parsestr:
            self.DisplayGroupTitle = parsestr['DisplayGroupTitle']
        if 'PlayURL' in parsestr:
            self.PlayURL = parsestr['PlayURL']
        if 'CmdURL' in parsestr:
            self.CmdURL = parsestr['CmdURL']

    def getCategory(self):
        return self.Category

    def getChannelAffiliate(self):
        return self.ChannelAffiliate

    def getChannelImageURL(self):
        return self.ChannelImageURL

    def getChannelName(self):
        return self.ChannelName

    def getChannelNumber(self):
        return self.ChannelNumber

    def getEndTime(self):
        return self.EndTime

    def getEpisodeNumber(self):
        return self.EpisodeNumber

    def getEpisodeTitle(self):
        return self.EpisodeTitle

    def getFirstAiring(self):
        return self.FirstAiring

    def getImageURL(self):
        return self.ImageURL

    def getOriginalAirdate(self):
        return self.OriginalAirdate

    def getProgramID(self):
        return self.ProgramID

    def getRecordEndTime(self):
        return self.RecordEndTime

    def getRecordStartTime(self):
        return self.RecordStartTime

    def getRecordSuccess(self):
        return self.RecordSuccess

    def getSeriesID(self):
        return self.SeriesID

    def getStartTime(self):
        return self.StartTime

    def getSynopsis(self):
        return self.Synopsis

    def getTitle(self):
        return self.Title

    def getDisplayGroupID(self):
        return self.DisplayGroupID

    def getDisplayGroupTitle(self):
        return self.DisplayGroupTitle

    def getPlayURL(self):
        return self.PlayURL

    def getCmdURL(self):
        return self.CmdURL

class RecordingRule(object):
    SeriesID = ""
    Title = ""
    ImageURL = ""
    RecentOnly = 0
    Priority = 0
    Synopsis = ""
    EndPadding = 0
    StartPadding = 0
    RecordingRuleID = ""

    def __init__(self):
        return

    def parse(self,parsestr):
        if 'SeriesID' in parsestr:
            self.SeriesID = parsestr['SeriesID']
        if 'Title' in parsestr:
            self.Title = parsestr['Title']
        if 'ImageURL' in parsestr:
            self.ImageURL = parsestr['ImageURL']
        if 'RecentOnly' in parsestr:
            self.RecentOnly = parsestr['RecentOnly']
        if 'Priority' in parsestr:
            self.Priority = parsestr['Priority']
        if 'Synopsis' in parsestr:
            self.Synopsis = parsestr['Synopsis']
        if 'EndPadding' in parsestr:
            self.EndPadding = parsestr['EndPadding']
        if 'StartPadding' in parsestr:
            self.StartPadding = parsestr['StartPadding']
        if 'RecordingRuleID' in parsestr:
            self.RecordingRuleID = parsestr['RecordingRuleID']

    def getSeriesID(self):
        return self.SeriesID

    def getTitle(self):
        return self.Title

    def getImageURL(self):
        return self.ImageURL

    def setRecentOnly(self,RecentOnly):
        self.RecentOnly = RecentOnly

    def getRecentOnly(self):
        return self.RecentOnly

    def setPriority(self,Priority):
        self.Priority = Priority

    def getPriority(self):
        return self.Priority

    def getSynopsis(self):
        return self.Synopsis

    def setEndPadding(self,EndPadding):
        self.EndPadding = EndPadding

    def getEndPadding(self):
        return self.EndPadding

    def setStartPadding(self,StartPadding):
        self.StartPadding = StartPadding

    def getStartPadding(self):
        return self.StartPadding

    def getRecordingRuleID(self):
        return self.RecordingRuleID

class BaseDevice(object):
    LocalIP = ""
    BaseURL = ""
    DiscoverURL = ""

    def __init__(self):
        return

    def getLocalIP(self):
        return self.LocalIP

    def getBaseURL(self):
        return self.BaseURL

    def getDiscoverURL(self):
        return self.DiscoverURL

class Tuner(BaseDevice):
    PyHDHR = None
    DeviceID = ""
    LineupURL = ""
    TunerCount = ""
    DeviceAuth = ""
    ModelNumber = ""
    FriendlyName = ""
    FirmwareName = ""
    FirmwareVersion = ""
    ConditionalAccess = ""
    ChannelInfos = {}
    LastDiscover = 0
    LastTranscodeOptionDiscover = 0
    TranscodeOption = None

    def __init__(self,PyHDHR):
        self.PyHDHR = PyHDHR

    def parse(self,parsestr):
        if 'DeviceID' in parsestr:
            self.DeviceID = parsestr['DeviceID']
        if 'LocalIP' in parsestr:
            self.LocalIP = parsestr['LocalIP']
        if 'BaseURL' in parsestr:
            self.BaseURL = parsestr['BaseURL']
        if 'DiscoverURL' in parsestr:
            self.DiscoverURL = parsestr['DiscoverURL']
        if 'LineupURL' in parsestr:
            self.LineupURL = parsestr['LineupURL']

    def getDeviceID(self):
        return self.DeviceID

    def getLineupURL(self):
        return self.LineupURL

    def getBaseURL(self):
        return self.LineupURL

    def getTunerCount(self):
        return self.TunerCount

    def getDeviceAuth(self):
        return self.DeviceAuth

    def getModelNumber(self):
        return self.ModelNumber

    def getFriendlyName(self):
        return self.FriendlyName

    def getFirmwareName(self):
        return self.FirmwareName

    def getFirmwareVersion(self):
        return self.FirmwareVersion

    def getConditionalAccess(self):
        return self.ConditionalAccess

    def getChannelInfos(self):
        return self.ChannelInfos

    def getTranscodeOption(self):
        if time.time() - self.LastTranscodeOptionDiscover < 60 and self.TranscodeOption:
            return self.TranscodeOption

        self.LastTranscodeOptionDiscover = time.time()

        if self.ModelNumber == "HDTC-2US":
            try:
                regx = Regex('/([0-9]+.[0-9]+.[0-9]+.[0-9]+)').search(self.DiscoverURL)
                ip = regx.group(1)

                response = urlopen("http://"+ip+"/transcode.html",None,5)

                regx = Regex('transcodeChanged\(\)">((.|\n)+?)</select>').search(response.read())
                selecttags = regx.group(1)

                regx = Regex('.+"(.*)".+selected=').search(selecttags)
                self.TranscodeOption = regx.group(1)
            except Exception as e:
                pass
        return self.TranscodeOption

    def discover(self):
        if time.time() - self.LastDiscover < 60:
            return True

        self.LastDiscover = time.time()

        try:
            response = urlopen(self.DiscoverURL,None,5)
            data = json.loads(response.read())
            if 'TunerCount' in data:
                self.TunerCount = data['TunerCount']
            if 'DeviceAuth' in data:
                self.DeviceAuth = data['DeviceAuth']
                self.PyHDHR.setDeviceAuth(self.DeviceID,self.DeviceAuth)
            if 'ModelNumber' in data:
                self.ModelNumber = data['ModelNumber']
            if 'FriendlyName' in data:
                self.FriendlyName = data['FriendlyName']
            if 'FirmwareName' in data:
                self.FirmwareName = data['FirmwareName']
            if 'FirmwareVersion' in data:
                self.FirmwareVersion = data['FirmwareVersion']
            if 'ConditionalAccess' in data:
                self.ConditionalAccess = data['ConditionalAccess']
            return True
        except Exception as e:
            Log.Critical("Exception in Tuner.discover while attempting to load: "+str(self.DiscoverURL))
            Log.Critical(e)
            return False

    def processLineup(self,PyHDHR):
        self.discover()
        try:
            response = urlopen(self.LineupURL,None,5)
            data = json.loads(response.read())
            for item in data:
                if 'GuideNumber' in item:
                    if item['GuideNumber'] in self.ChannelInfos:
                        self.ChannelInfos[item['GuideNumber']].parse(item,self.PyHDHR)
                    else:
                        chaninfo = ChannelInfo(self)
                        chaninfo.parse(item,self.PyHDHR)
                        self.ChannelInfos[item['GuideNumber']] = chaninfo
                    PyHDHR.registerChannelInfo(self.ChannelInfos[item['GuideNumber']],self)
            return True
        except Exception as e:
            Log.Critical("Exception in Tuner.processLineup while attempting to load: "+str(self.LineupURL))
            Log.Critical(e)
            return False

    def processGuide(self,PyHDHR):
        if not self.DeviceAuth:
            return False
        try:
            response = urlopen(URL_GUIDE_BASE + self.DeviceAuth,None,5)
            data = json.loads(response.read())
            for item in data:
                if 'GuideNumber' in item:
                    if item['GuideNumber'] in self.ChannelInfos:
                        self.ChannelInfos[item['GuideNumber']].parse(item,self.PyHDHR)
                    else:
                        chaninfo = ChannelInfo(self)
                        chaninfo.parse(item,self.PyHDHR)
                        self.ChannelInfos[item['GuideNumber']] = chaninfo
                    PyHDHR.registerChannelInfo(self.ChannelInfos[item['GuideNumber']],self)
            return True
        except Exception as e:
            Log.Critical("Exception in Tuner.processGuide while attempting to load: "+str(URL_GUIDE_BASE + self.DeviceAuth))
            Log.Critical(e)
            return False

class DVR(BaseDevice):
    StorageID = ""
    StorageURL = ""
    FreeSpace = ""
    Version = ""
    FriendlyName = ""

    def __init__(self):
        return

    def parse(self,parsestr):
        if 'StorageID' in parsestr:
            self.StorageID = parsestr['StorageID']
        if 'LocalIP' in parsestr:
            self.LocalIP = parsestr['LocalIP']
        if 'BaseURL' in parsestr:
            self.BaseURL = parsestr['BaseURL']
        if 'DiscoverURL' in parsestr:
            self.DiscoverURL = parsestr['DiscoverURL']
        if 'StorageURL' in parsestr:
            self.StorageURL = parsestr['StorageURL']

    def getStorageID(self):
        return self.StorageID

    def getStorageURL(self):
        return self.StorageURL

    def getFreeSpace():
        return self.FreeSpace

    def getVersion():
        return self.Version

    def getFriendlyName():
        return self.FriendlyName

    def discover(self):
        try:
            response = urlopen(self.DiscoverURL,None,5)
            data = json.loads(response.read())
            if 'FreeSpace' in data:
                self.FreeSpace = data['FreeSpace']
            if 'Version' in data:
                self.Version = data['Version']
            if 'FriendlyName' in data:
                self.FriendlyName = data['FriendlyName']
            return True
        except Exception as e:
            Log.Critical("Exception in DVR.discover while attempting to load: "+str(self.DiscoverURL))
            Log.Critical(e)
            return False

class PyHDHR(object):
    Tuners = {}
    DVRs = {}
    ProgramFilters = {}
    DeviceAuths = {}
    RecordingRules = {}
    ChannelLineup = {}
    ChannelArray = []
    ChannelInfos = {}
    LastDiscover = 0
    LastRecordedDiscover = 0
    RecordedPrograms = {}

    def __init__(self):
        return

    def getTuners(self):
        self.discover()
        return self.Tuners

    def getDVRs(self):
        self.discover()
        return self.DVRs

    def setDeviceAuth(self,DeviceID,DeviceAuth):
        self.DeviceAuths[DeviceID] = DeviceAuth

    def getDeviceAuth(self):
        retstr = ""
        for key in self.DeviceAuths:
            retstr += self.DeviceAuths[key]
        return retstr

    def addProgramFilter(self,pf):
        if pf.getName() not in self.ProgramFilters:
            self.ProgramFilters[pf.getName()] = pf
        return self.ProgramFilters[pf.getName()]

    def getProgramFilters(self):
        self.discover()
        return self.ProgramFilters

    def registerChannelInfo(self,chaninfo,tuner):
        if chaninfo.getGuideNumber() in self.ChannelLineup:
            if tuner not in self.ChannelLineup[chaninfo.getGuideNumber()]:
                self.ChannelLineup[chaninfo.getGuideNumber()].append(tuner)
        else:
            self.ChannelArray.append(Decimal(chaninfo.getGuideNumber()))
            chans = []
            chans.append(tuner)
            self.ChannelLineup[chaninfo.getGuideNumber()] = chans
        self.ChannelInfos[chaninfo.getGuideNumber()] = chaninfo

    def getChannelInfo(self,guideno):
        if guideno in self.ChannelInfos:
            return self.ChannelInfos[guideno]
        else:
            return None

    def getChannelList(self):
        self.discover()
        self.ChannelArray.sort()
        return self.ChannelArray

    def getWhatsOn(self,guideno=None):
        self.discover()

        if not guideno:
            onprogs = {}
            for key in self.ChannelInfos:
                progs = self.ChannelInfos[key].getProgramInfos()
                if len(progs) > 0:
                    onprogs[self.ChannelInfos[key].getGuideNumber()] = progs[0]
            return onprogs
        else:
            if guideno in self.ChannelInfos:
                progs = self.ChannelInfos[guideno].getProgramInfos()
                if len(progs) > 0:
                    return progs[0]

    def getLiveTVURL(self,guideno):
        self.discover(True)
        for tunerkey in self.Tuners:
            chaninfos = self.Tuners[tunerkey].getChannelInfos()
            if guideno in chaninfos:
                return chaninfos[guideno].getURL()
        return None

    def getLiveTVURLList(self,guideno):
        self.discover(True)
        urls = []
        for tunerkey in self.Tuners:
            chaninfos = self.Tuners[tunerkey].getChannelInfos()
            if guideno in chaninfos:
                urls.append('file.ts')
                urls.append(chaninfos[guideno].getURL())
        return urls

    def getRecordedPrograms(self,force=False):
        self.discover()

        if not force and len(self.RecordedPrograms) != 0:
            if time.time() - self.LastRecordedDiscover < 60:
                return self.RecordedPrograms

        self.LastRecordedDiscover = time.time()

        self.RecordedPrograms = {}
        xbmc.log("getRecordedPrograms - DVRs:"+str(self.DVRs))
        for key in self.DVRs:
            Log.Debug("getRecordedPrograms key:"+key)
            try:
                response = urlopen(self.DVRs[key].getStorageURL(),None,5)
                data = json.loads(response.read())
                for item in data:
                    recprog = RecordedProgram()
                    recprog.parse(item)
                    self.RecordedPrograms[recprog.getProgramID()] = recprog
            except Exception as e:
                Log.Critical("Exception in PyHDHR.getRecordedPrograms while attempting to load: "+str(self.DVRs[key].getStorageURL()))
                Log.Critical(e)
        return self.RecordedPrograms

    def getFilteredRecordedPrograms(self,sortby,grouptype,groupby):
        self.discover()
        progs = self.getRecordedPrograms()

        if progs:
            filteredprogs = []
            for prog in (sorted(list(progs.values()), key=operator.attrgetter('RecordEndTime'), reverse=(True if sortby == SortType.asc else False))):
                if grouptype == GroupType.All:
                    filteredprogs.append(prog)
                elif grouptype == GroupType.SeriesID:
                    if groupby == prog.getSeriesID():
                        filteredprogs.append(prog)
                elif grouptype == GroupType.Category:
                    if groupby == prog.getCategory():
                        filteredprogs.append(prog)
                else:
                    pass
            return filteredprogs
        return None

    def getRecordedProgram(self,key):
        self.discover()
        progs = self.getRecordedPrograms()
        if progs:
            if key in progs:
                return progs[key]
        else:
            return None

    def getRecordedSeries(self):
        self.discover()
        progs = self.getRecordedPrograms()
        series = {}
        for key in progs:
            if progs[key].getDisplayGroupTitle() not in series:
                ss = SeriesSummary(progs[key].getSeriesID(),progs[key].getImageURL())
                series[progs[key].getDisplayGroupTitle()] = ss
            else:
                series[progs[key].getDisplayGroupTitle()].addEpisodeCount(1)
        return series

    def searchWhatsOn(self,query):
        self.discover()
        progs = self.getWhatsOn()

        foundprogs = {}
        for key in progs:
            if(searchString(query,progs[key].getTitle()) or
                    searchString(query,progs[key].getEpisodeTitle()) or
                    searchString(query,progs[key].getSynopsis())
            ):
                foundprogs[key] = progs[key]
            else:
                for filter in progs[key].getProgramFilters():
                    if searchString(query, filter.getName()):
                        foundprogs[key] = progs[key]
                        break
        return foundprogs

    def searchRecorded(self,query):
        self.discover()
        progs = self.getRecordedPrograms()
        foundprogs = {}
        for key in progs:
            if(searchString(query,progs[key].getTitle()) or
                    searchString(query,progs[key].getDisplayGroupTitle()) or
                    searchString(query,progs[key].getEpisodeTitle()) or
                    searchString(query,progs[key].getSynopsis()) or
                    searchString(query,progs[key].getChannelNumber()) or
                    searchString(query,progs[key].getChannelName()) or
                    searchString(query,progs[key].getChannelAffiliate()) or
                    searchString(query,progs[key].getCategory())
            ):
                foundprogs[key] = progs[key]
        return foundprogs

    def getRecordingRules(self):
        self.discover()
        self.processRecordingRules()
        return self.RecordingRules

    def processRecordingRules(self):
        if not self.getDeviceAuth():
            return False
        try:
            response = urlopen(URL_RECORDING_RULES+self.getDeviceAuth(),None,5)
            data = json.loads(response.read())
            for item in data:
                if 'RecordingRuleID' in item:
                    if item['RecordingRuleID'] in self.RecordingRules:
                        self.RecordingRules[item['RecordingRuleID']].parse(item)
                    else:
                        recordrule = RecordingRule()
                        recordrule.parse(item)
                        self.RecordingRules[item['RecordingRuleID']] = recordrule
            return True
        except Exception as e:
            Log.Critical("Exception in PyHDHR.processRecordingRules while attempting to load: "+str(URL_RECORDING_RULES+self.getDeviceAuth()))
            Log.Critical(e)
            return False

    def discover(self,force=False):
        if not force:
            if time.time() - self.LastDiscover < 60:
                return True

        self.LastDiscover = time.time()

        try:
            response = urlopen(URL_DISCOVER,None,5)
            data = json.loads(response.read())
            xbmc.log("PyHDHR.discover")
            xbmc.log("data:"+str(data))
            for item in data:
                xbmc.log("item:"+str(item))
                if 'StorageID' in item and 'StorageURL' in item:
                    #DVR
                    if item['StorageID'] in self.DVRs:
                        xbmc.log("existing dvr:"+item['StorageID'])
                        self.DVRs[item['StorageID']].parse(item)
                        self.DVRs[item['StorageID']].discover()
                    else:
                        xbmc.log("new dvr:"+item['StorageID'])
                        dvr = DVR()
                        dvr.parse(item)
                        if dvr.discover():
                            xbmc.log("discovered successfully")
                            self.DVRs[item['StorageID']] = dvr
                        else:
                            xbmc.log("discover failed")
                elif 'DeviceID' in item and 'LineupURL' in item:
                    #Tuner
                    if item['DeviceID'] in self.Tuners:
                        self.Tuners[item['DeviceID']].parse(item)
                        if self.Tuners[item['DeviceID']].discover():
                            self.Tuners[item['DeviceID']].processLineup(self)
                            self.Tuners[item['DeviceID']].processGuide(self)
                    else:
                        tuner = Tuner(self)
                        tuner.parse(item)
                        if tuner.discover():
                            tuner.processLineup(self)
                            tuner.processGuide(self)
                            self.Tuners[item['DeviceID']] = tuner
                else:
                    Log.Debug("PyHDHR.discover - could not determine device type - " + str(item))
            xbmc.log("done disovering. dvrs:"+str(self.DVRs))
            return True
        except Exception as e:
            Log.Critical("Exception in PyHDHR.discover while attempting to load: "+str(URL_DISCOVER))
            Log.Critical(e)
            return False

    def discoveryDump(self,filename):
        f = open(filename,'w')
        f.write("Full Discovery\n")
        try:
            f.write("\nDiscover: "+URL_DISCOVER+"\n")
            response = urlopen(URL_DISCOVER,None,5)
            data = json.loads(response.read())
            f.write("\nRAW:\n"+str(data)+"\n\nFormatted:\n")
            for item in data:
                for key in item:
                    try:
                        f.write(str(key)+" => "+str(item[key])+"\n")
                    except Exception as e:
                        f.write("[error decoding]"+"\n")
                if 'StorageID' in item and 'StorageURL' in item and 'DiscoverURL' in item:
                    #DVR
                    f.write("\nDiscover DVR: "+item['DiscoverURL']+"\n")
                    try:
                        response1 = urlopen(item['DiscoverURL'],None,5)
                        data1 = json.loads(response1.read())
                        f.write("\nRAW:\n"+str(data1)+"\n\nFormatted:\n")
                        for key1 in data1:
                            try:
                                f.write(str(key1)+" => "+str(data1[key1])+"\n")
                            except Exception as e:
                                f.write("[error decoding]"+"\n")
                    except Exception as e:
                        Log.Critical("Exception in PyHDHR.discoveryDump while attempting to load: "+str(item['DiscoverURL']))
                        Log.Critical(e)
                    f.write("\nDiscover DVR Storage: "+item['StorageURL']+"\n")
                    try:
                        response1 = urlopen(item['StorageURL'],None,5)
                        data1 = json.loads(response1.read())
                        f.write("\nRAW:\n"+str(data1)+"\n\nFormatted:\n")
                        for item1 in data1:
                            for key1 in item1:
                                try:
                                    f.write(str(key1)+" => "+str(item1[key1])+"\n")
                                except Exception as e:
                                    f.write("[error decoding]"+"\n")
                            f.write("\n")
                    except Exception as e:
                        Log.Critical("Exception in PyHDHR.discoveryDump while attempting to load: "+str(item['StorageURL']))
                        Log.Critical(e)
                elif 'DeviceID' in item and 'LineupURL' in item and 'DiscoverURL' in item:
                    #Tuner
                    f.write("\nDiscover Tuner: "+item['DiscoverURL']+"\n")
                    try:
                        response1 = urlopen(item['DiscoverURL'],None,5)
                        data1 = json.loads(response1.read())
                        f.write("\nRAW:\n"+str(data1)+"\n\nFormatted:\n")
                        for key1 in data1:
                            try:
                                f.write(str(key1)+" => "+str(data1[key1])+"\n")
                            except Exception as e:
                                f.write("[error decoding]"+"\n")
                    except Exception as e:
                        Log.Critical("Exception in PyHDHR.discoveryDump while attempting to load: "+str(item['DiscoverURL']))
                        Log.Critical(e)
                    f.write("\nDiscover Tuner Lineup: "+item['LineupURL']+"\n")
                    try:
                        response1 = urlopen(item['LineupURL'],None,5)
                        data1 = json.loads(response1.read())
                        f.write("\nRAW:\n"+str(data1)+"\n\nFormatted:\n")
                        for item1 in data1:
                            for key1 in item1:
                                try:
                                    f.write(str(key1)+" => "+str(item1[key1])+"\n")
                                except Exception as e:
                                    f.write("[error decoding]"+"\n")
                            f.write("\n")
                    except Exception as e:
                        Log.Critical("Exception in PyHDHR.discoveryDump while attempting to load: "+str(item['LineupURL']))
                        Log.Critical(e)
                else:
                    Log.Debug("PyHDHR.discoveryDump - could not determine device type - " + str(item))
        except Exception as e:
            Log.Critical("Exception in PyHDHR.discoveryDump while attempting to load: "+str(URL_DISCOVER))
            Log.Critical(e)

if __name__ == "__main__":
   import argparse
   parser = argparse.ArgumentParser()
   parser.add_argument('-f','--file',help='file to output to',default='output.txt')
   args = parser.parse_args()
   p = PyHDHR()
   p.discover()
   rp = p.getFilteredRecordedPrograms(SortType.asc,GroupType.All,None)
   if rp:
      for r in rp:
         xbmc.log(r.getProgramID())
   p.discoveryDump(args.file)
