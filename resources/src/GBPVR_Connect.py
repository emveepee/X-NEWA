######################################################################################################
# Class for connecting to a GBPVR instance
#
# Requires: 	PyCrypto (for Rijnsdael Authentication)
#  		Suds (for SOAP interaction)
#  		PBKDF2 (RFC PBKDF2 support)
#
# Usage: Instantiate a new class with ip and portnumber
#  I.e. myGBPVR = new GBPVR_Connect('127.0.0.1', 80)
# Then, call methods on the new class
#  I.e. myGBPVR.AreYouThere()
#       myGBPVR.GetChannelList('gbpvruser', 'gbpvrpw')
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

Last_Error = ""
# For WS Search functions, sort and filters....
# Sort fields

import time
import datetime
from datetime import timedelta
import tempfile
import os.path
import cPickle as pickle
import xbmc

class GBPVR_Connect:

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
  SCHEDULE_ONCE = 'once'

  # Instantiation
  def __init__(self, ip, port):
	self.ip = ip
	self.port = port
	self.vlc_url = None
	if not os.path.exists(xbmc.translatePath('special://temp') + 'x-newa/'):
		os.makedirs(xbmc.translatePath('special://temp') + 'x-newa/')
	
	self.mycache = xbmc.translatePath('special://temp') + 'x-newa/'
	print self.mycache



        if not _isIP(self.ip):
                try:
                        from socket import gethostbyaddr 
                        temp = gethostbyaddr(ip)
                        debug("Resolving hostname to: " + temp[2][0])
                        self.ip = temp[2][0]
                except:
                        debug("Error instantiating (cannot resolve host-name)")
                        raise Exception, "cannot resolve host-name." 

  #Core Functions

  ######################################################################################################
  # Checking to see if the GBPVR server is awake...
  ######################################################################################################
  def AreYouThere(self, usewol=False, mac=None, broadcast='192.168.2.255', _retry=0):

	import socket
	# check if computer is on
	debug( "--> AreYouThere() socket on port " + str(self.port) + " using ip=" + str(self.ip))
	debug( "                  mac:" + str(mac) + "broadcast: " + str(broadcast))
	ret = True
	debug( "This got: " + str(usewol) + " / " + mac)

	try:
		# try and connect to host on supplied port
		s = socket.socket()
		s.settimeout ( 0.50 )
		s.connect ( ( self.ip, int(self.port ) ) )
		s.close()
	except:
                if _retry < 5:
                        
                        #_WakeOnLan("00:13:d4:fa:f5:27")
                	if usewol:
                        	_WakeOnLan(mac, broadcast)
                        time.sleep(5)
                        ret = self.AreYouThere(usewol, mac, broadcast, _retry+1)
                else:
                        ret = False

	debug("--> AreYouThere() returning: " + str(ret))
	return ret

#################################################################################################################
  def getURL(self):
	address = "http://" + self.ip + ":" + str(self.port)
	return address

#################################################################################################################
  def getVlcURL(self):
	return self.vlc_url

######################################################################################################
# Starting streaming by vlc
######################################################################################################
  def startVlcObjectByScheduleOID(self, userid, password, scheduleOID):

	import suds.client
	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_VLC_PATH

	client = suds.client.Client(url,cache=None)

	authObj = client.factory.create('webServiceAuthentication')

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)

	client.set_options(soapheaders=authObj)

	ret_soap = client.service.startVlcObjectByScheduleOID(scheduleOID, soapheaders=authObj)	
	if ret_soap.webServiceVlcObjects.webServiceVlcObject.StreamLocation  is not None:
		print ret_soap.webServiceVlcObjects.webServiceVlcObject.StreamLocation
		self.vlc_url = ret_soap.webServiceVlcObjects.webServiceVlcObject.StreamLocation
		return True
	else:
		return False

######################################################################################################
# Starting streaming by vlc
######################################################################################################
  def startVlcObjectByEPGEventOID(self, userid, password, eventOID):

	import suds.client
	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_VLC_PATH

	client = suds.client.Client(url,cache=None)

	authObj = client.factory.create('webServiceAuthentication')

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)

	client.set_options(soapheaders=authObj)

	ret_soap = client.service.startVlcObjectByEPGEventOID(eventOID, soapheaders=authObj)	
	if ret_soap.webServiceVlcObjects.webServiceVlcObject.StreamLocation  is not None:
		print ret_soap.webServiceVlcObjects.webServiceVlcObject.StreamLocation
		self.vlc_url = ret_soap.webServiceVlcObjects.webServiceVlcObject.StreamLocation
		return True
	else:
		return False


  def stopVlcStreamObject(self, userid, password):

	import suds.client
	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_VLC_PATH

	client = suds.client.Client(url,cache=None)

	authObj = client.factory.create('webServiceAuthentication')

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)

	client.set_options(soapheaders=authObj)

	ret_soap = client.service.stopVlcStreamObject(soapheaders=authObj)	
	return True

  ######################################################################################################
  # Retrieving XMLInfo information and returning in dictionary
  ######################################################################################################
  def GetGBPVRInfo(self, userid, password):
	import urllib2
	from xml.dom import minidom

	address = "http://" + self.ip + ":" + str(self.port) + NEWA_XMLINFO_PATH
	website = urllib2.urlopen(address)
	website_html = website.read()

	dom = minidom.parseString(website_html)

	dic = {}
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

	# We also get, and cache, the channel data
	self.channels = self.getChannelList(userid, password)
	self.channelGroups = self.getChannelGroupList(userid, password)
	self.RecDirs = self.getRecDirList(userid, password)
	return dic

  def cleanCache(self,spec):
	import glob
	print "clean cache for " + spec 
	fileNames = glob.glob(self.mycache+spec)
	for file in fileNames:
		os.remove(file)
	return True

  def cleanOldCache(self,spec):
	import glob
	import os
	print "clean old files for " + spec 
	fileNames = glob.glob(self.mycache+spec)
	for file in fileNames:
		ft =  datetime.datetime.fromtimestamp(os.path.getmtime(file))
		if ft - timedelta(hours=1) < datetime.datetime.now():
			os.remove(file)
	return True

  ######################################################################################################
  # Retrieves a list of channels...
  ######################################################################################################
  def getChannelList(self, userid, password):

	cached = self.mycache+'channel.List'
	print "getChannelList start"
	if checkCache(cached):
		dic = pickle.load(open(cached,'rb'))
		print "getChannelList cached end"
		return dic

	import suds.client
	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SEARCH_PATH

	client = suds.client.Client(url,cache=None)

	authObj = client.factory.create('webServiceAuthentication')

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)

	ret_soap = client.service.getChannelListObject(soapheaders=authObj)
	dic = {}

	from xbmcaddon import Addon
	self.channelPath = os.path.join( Addon('script.xbmc.x-newa').getAddonInfo('path'), "fanart", "Channels") + "/"
	import imghdr
	import urllib
	import glob
	for chan in ret_soap.anyType:
		temp = chan.split('!')
		dic[temp[2]] = ( temp[1].encode('latin-1'),temp[0] )
		try:
			output = self.channelPath+temp[1]+".*"
			icon = glob.glob(output)
			if not icon:
				url = self.getURL()+'/'+temp[3]
				output = self.channelPath+"unknown" 
				urllib.urlretrieve (url,output)
				img = imghdr.what(self.channelPath+"unknown");
				if img == "png":
					os.rename(self.channelPath+"unknown", self.channelPath+temp[1]+".png")
				elif img == "jpeg":
					os.rename(self.channelPath+"unknown", self.channelPath+temp[1]+".jpg")
				elif img is None:
					print temp[1] + " is unknown"
				else:
					print temp[1] + " Type " + img
			else:
				print "Found " + icon[0]
		except:
			print url + " Error"
			pass

  	print "getChannelList end"

	pickle.dump(dic, open(cached,'wb'))

	return dic

  ######################################################################################################
  # Sets the playback position
  ######################################################################################################
  def setPlaybackPositiontObject(self, userid, password, rec, position, duration):

	import suds.client

	print "setPlaybackPositiontObject start"

	if int(duration) == 0 and int(position) == 0:
		print "Not bothering with zero"
		return True

	if int(duration) == 0 and int(position) != 0:
		duration = position + 30
			
	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_DETAIL_PATH
	
	client = suds.client.Client(url,cache=None)
	
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

	import suds.client
  	print "getChannelGroupList start"

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_GUIDE_PATH

	client = suds.client.Client(url,cache=None)

	authObj = client.factory.create('webServiceAuthentication')

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)
	ret_soap = client.service.getChannelGroupsObject(soapheaders=authObj)
	groups = []
	for group in ret_soap.anyType:
		groups.append(group.encode('latin-1'))
  	
	print "getChannelGroupList end"
	return groups

  ######################################################################################################
  # Retrieves a list of recDir...
  ######################################################################################################
  def getRecDirList(self, userid, password):

	import suds.client
	print "getRecDirList start"
	
	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SCHEDULE_PATH
	
	client = suds.client.Client(url,cache=None)
	authObj = client.factory.create('webServiceAuthentication')
	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	client.set_options(soapheaders=authObj)
	ret_soap = client.service.getRecDirObject(soapheaders=authObj)
	#print ret_soap
	groups = []
	groups.append(ret_soap.DefaultRecordingDirectory.RecDirName.encode('latin-1'))
	if len(ret_soap.ExtraRecordingDirectories) != 0:
		for dirs in ret_soap.ExtraRecordingDirectories.webServiceRecordingDirectory:
			groups.append(dirs.RecDirName.encode('latin-1'))
	return groups

  ######################################################################################################
  def getDetails(self, userid, password, oid, type):

	import suds.client


	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_DETAIL_PATH

	client = suds.client.Client(url,cache=None)

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

	return self._detail2array(ret_soap)

  ######################################################################################################
  def getGuideInfo(self, userid, password, timeStart, timeEnd, group):

	print "getGuideInfo start "
	print timeStart

	self.cleanOldCache('guideListing-*.p')

	cached = self.mycache +'guideListing-' + str(timeStart).replace(':','')  + '.p'
	print cached
	if checkCache(cached):
		retArr = pickle.load(open(cached,'rb'))
		print "getGuideInfo cached end"
		return retArr

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_GUIDE_PATH
	
	if group is not None:
		if group not in self.channelGroups:
			print group + " group not found"
			caseGroup = None
			for groups in self.channelGroups:
				if groups.lower() == group.lower():
					print groups + " group found"
					caseGroup = groups
			group = caseGroup

	client = suds.client.Client(url,cache=None)
	client.set_options(cache=None)
	authObj = client.factory.create('webServiceAuthentication')

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)
	ret_soap = client.service.getGuideObject( timeStart, timeEnd, channelGroup=group, soapheaders=authObj)
  	print "getGuideInfo end"
	retGuide = self._progs2array(ret_soap)
	pickle.dump(retGuide, open(cached,'wb'),pickle.HIGHEST_PROTOCOL)
	return retGuide
  
  ######################################################################################################
  def getUpcomingRecordings(self, userid, password, amount=0):

	cached = self.mycache +'upcomingRecordings-' + str(amount) + '.p'
	print cached
	if checkCache(cached):
	  retArr = pickle.load(open(cached,'rb'))
	  return retArr

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH

	client = suds.client.Client(url,cache=None)
	client.set_options(cache=None)
	
	#d=dict(http='localhost:8080')
	#client.set_options(proxy=d)

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
	
	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	client.set_options(soapheaders=authObj)
	if amount == 0:
            ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)
        else:
            ret_soap = client.service.getSortedFilteredManageListObjectLimitResults(sortObj, fltrObj, amount, soapheaders=authObj)
	retArr = self._recs2array(ret_soap)
	pickle.dump(retArr, open(cached,'wb'),pickle.HIGHEST_PROTOCOL)
	return retArr

  ######################################################################################################
  def getRecentRecordings(self, userid, password, amount=0):

	cached = self.mycache +'recentRecordings-' + str(amount) + '.p'
	if checkCache(cached):
		retArr = pickle.load(open(cached,'rb'))

		return retArr

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH

	client = suds.client.Client(url,cache=None)
	client.set_options(cache=None)
	
	#d=dict(http='localhost:8080')
	#client.set_options(proxy=d)

	authObj = client.factory.create('webServiceAuthentication')
	sortObj = client.factory.create('recordingsSort')
	fltrObj = client.factory.create('recordingsFilter')

	# Figure out the sorting....
	sortObj.datetimeSortSeq = 1
	sortObj.channelSortSeq = 4
	sortObj.titleSortSeq = 3
	sortObj.statusSortSeq = 2
	sortObj.datetimeDecending = 1
	sortObj.channelDecending = 0
	sortObj.titleDecending = 0
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
	
	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)
	if amount == 0:
            ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)
	else:
            ret_soap = client.service.getSortedFilteredManageListObjectLimitResults(sortObj, fltrObj, amount, soapheaders=authObj)
	retArr = self._recs2array(ret_soap)
	pickle.dump(retArr, open(cached,'wb'),pickle.HIGHEST_PROTOCOL)
	return retArr

  ######################################################################################################
  def getConflicts(self, userid, password, conflictRec):

	import suds.client
        # First, we get a list of recordings sorted by date.....

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH

	client = suds.client.Client(url,cache=None)
	client.set_options(cache=None)
	
	#d=dict(http='localhost:8080')
	#client.set_options(proxy=d)

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
		retArr.append(theDict)

	return retArr
    
  ######################################################################################################
  def searchProgram(self, userid, password, needle):
 
	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SEARCH_PATH
	
	client = suds.client.Client(url,cache=None)
	client.set_options(cache=None)
	#d=dict(http='localhost:8080')
	#client.set_options(proxy=d)

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

#	import logging
#	logging.basicConfig(level=logging.INFO)
#	logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)
	ret_soap = client.service.searchObject(searchObj, soapheaders=authObj)
	print ret_soap
	return self._recs2array1(ret_soap)
  
  ######################################################################################################
  def getScheduledRecordings(self, userid, password):

	cached = self.mycache + 'scheduledRecordings.p'
	print cached
	if checkCache(cached):
		retArr = pickle.load(open(cached,'rb'))
		return retArr

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH

	client = suds.client.Client(url,cache=None)
	client.set_options(cache=None)
	
	#d=dict(http='localhost:8080')
	#client.set_options(proxy=d)

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
	
	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)
	ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)
	retArr = self._recs2array2(ret_soap)
	pickle.dump(retArr, open(cached,'wb'),pickle.HIGHEST_PROTOCOL)
	return retArr

  ######################################################################################################
  def getConflictedRecordings(self, userid, password):

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH

	client = suds.client.Client(url,cache=None)
	client.set_options(cache=None)
	
	#d=dict(http='localhost:8080')
	#client.set_options(proxy=d)

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
	
	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)
	ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)

	return self._recs2array(ret_soap)

  ######################################################################################################
  def getFilteredSortedRecordings(self, userid, password, filter, sort, sortorder=SORT_ASCENDING):

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_MANAGE_PATH

	client = suds.client.Client(url,cache=None)
	client.set_options(cache=None)
	
	#d=dict(http='localhost:8080')
	#client.set_options(proxy=d)

	authObj = client.factory.create('webServiceAuthentication')
	sortObj = client.factory.create('recordingsSort')
	fltrObj = client.factory.create('recordingsFilter')

	# Figure out the sorting....
	sortObj.datetimeSortSeq = 2
	sortObj.channelSortSeq = 2
	sortObj.titleSortSeq = 2
	sortObj.statusSortSeq = 2
	sortObj.datetimeDecending = 0
	sortObj.channelDecending = 0
	sortObj.titleDecending = 0
	sortObj.statusDecending = 0

	if sort == self.SORT_DATE:
		sortObj.datetimeSortSeq = 1
		if sortorder == self.SORT_DESCENDING:
			sortObj.datetimeDecending = 1
	elif sort == self.SORT_CHANNEL:
		sortObj.channelSortSeq = 1
		if sortorder == self.SORT_DESCENDING:
			sortObj.channelDecending = 1
	elif sort == self.SORT_TITLE:
		sortObj.titleSortSeq = 1
		if sortorder == self.SORT_DESCENDING:
			sortObj.titleDecending = 1
	else: # SORT_STATUS
		sortObj.statusSortSeq = 1
		if sortorder == self.SORT_DESCENDING:
			sortObj,statusDecending = 1

	# Then the filtering....
	fltrObj.All = 0
	setattr(fltrObj, "None", 0)
	fltrObj.Pending = 0
	fltrObj.InProgress = 0
	fltrObj.Completed = 0
	fltrObj.Failed = 0
	fltrObj.Conflict = 0
	fltrObj.Recurring = 0
	fltrObj.Deleted = 0
	
	if filter == self.FILTER_ALL:
		fltrObj.All = 1
	elif filter == self.FILTER_NONE:
		setattr(fltrObj, "None", 1)
	elif filter == self.FILTER_PENDING:
		fltrObj.Pending = 1
	elif filter == self.FILTER_INPROGRESS:
		fltrObj.InProgress = 1
	elif filter == self.FILTER_COMPLETED:
		fltrObj.Completed = 1
	elif filter == self.FILTER_FAILED:
		fltrObj.Failed = 1
	elif filter == self.FILTER_CONFLICT:
		fltrObj.Conflict = 1
	elif filter == self.FILTER_REOCURRING:
		fltrObj.Recurring = 1
	else: # FILTER_DELETED
		fltrObj.Deleted = 1

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)
	ret_soap = client.service.getSortedFilteredManageListObject(sortObj, fltrObj, soapheaders=authObj)

	return self._recs2array(ret_soap)

  ######################################################################################################
  def updateRecording(self, userid, password, progDetails):
	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SCHEDULE_PATH

	client = suds.client.Client(url,cache=None)

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
        recObj.qualityBest = qualObj.QUALITY_BEST
        recObj.qualityBetter = qualObj.QUALITY_BETTER
        recObj.qualityGood = qualObj.QUALITY_GOOD
        recObj.dayMonday = "false"
        recObj.dayTuesday = "false"
        recObj.dayWednesday = "false"
        recObj.dayThursday = "false"
        recObj.dayFriday = "false"
        recObj.daySaturday = "false"
        recObj.daySunday = "false"
        
	recObj.pre_padding_min = progDetails['prepadding']
        recObj.post_padding_min = progDetails['postpadding']
        try:
                recObj.extend_end_time_min = progDetails['extendend']
        except:
                recObj.extend_end_time_min = 0
        recObj.days_to_keep = progDetails['maxrecs']
	
	client.set_options(soapheaders=authObj)
	ret_soap = client.service.updateRecording(progDetails['recording_oid'], recObj, soapheaders=authObj)
	if ret_soap.Message is not None:
            last_Error = ret_soap.Message

	return (not ret_soap.Error)

  ######################################################################################################
  def scheduleRecording(self, userid, password, progDetails):
	import suds.client
	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SCHEDULE_PATH
	client = suds.client.Client(url,cache=None)
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

	recObj.dayMonday = "false"
	recObj.dayTuesday = "false"
	recObj.dayWednesday = "false"
	recObj.dayThursday = "false"
	recObj.dayFriday = "false"
	recObj.daySaturday = "false"
	recObj.daySunday = "false"
	recObj.onlyNew = "false"	
	recObj.allChannels = "false"	

	recObj.epgeventOID = progDetails['program_oid']
	recObj.ChannelOid = "0"
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
		recObj.onlyNew = true;
		recObj.recordDayInterval = recordDayIntervalType.recordAnyDay;
		recObj.recordTimeInterval = recordTimeIntervalType.recordAnyTimeslot;	
	elif progDetails['rectype'] == "Record Season (All episodes on this channel)":
		recObj.recordDayInterval = recordDayIntervalType.recordAnyDay;
		recObj.recordTimeInterval = recordTimeIntervalType.recordAnyTimeslot;
	elif progDetails['rectype'] == "Record Season (Daily, this timeslot)":
		recObj.recordDayInterval =  recordDayIntervalType.recordAnyDay;
		recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot;
	elif progDetails['rectype'] == "Record Season (Weekly, this timeslot)":
		recObj.recordDayInterval =  recordDayIntervalType.recordThisDay;
		recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot;
	elif progDetails['rectype'] == "Record Season (Monday-Friday, this timeslot)":
		recObj.recordDayInterval =  recordDayIntervalType.recordSpecificDay;
		recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot;
		recObj.dayMonday = true;
		recObj.dayTuesday = true;
		recObj.dayWednesday = true;
		recObj.dayThursday = true;
		recObj.dayFriday = true;
	elif progDetails['rectype'] == "Record Season (Weekends, this timeslot)":
		recObj.recordDayInterval =  recordDayIntervalType.recordSpecificDay;
		recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot;
		recObj.daySaturday = true;
		recObj.daySunday = true;
	elif progDetails['rectype'] == "Record All Episodes, All Channels":
		recObj.allChannels = true;
		recObj.recordDayInterval = recordDayIntervalType.recordAnyDay;
		recObj.recordTimeInterval = recordTimeIntervalType.recordAnyTimeslot;
	else:
		print "Unknown rectype"
		return False

	recObj.pre_padding_min = progDetails['prepadding']
	recObj.post_padding_min = progDetails['postpadding']
	recObj.extend_end_time_min = "0"
	recObj.days_to_keep = progDetails['maxrecs']
	recObj.days_to_keep = progDetails['maxrecs']


	client.set_options(soapheaders=authObj)

#	import logging
#	logging.basicConfig(level=logging.INFO)
#	logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)
	ret_soap = client.service.scheduleRecording(recObj, soapheaders=authObj)
	if ret_soap.webServiceEPGEventObjects.webServiceReturn.Message is not None:
		print ret_soap.webServiceEPGEventObjects.webServiceReturn.Message
		last_Error = ret_soap.webServiceEPGEventObjects.webServiceReturn.Message

	return (not ret_soap.webServiceEPGEventObjects.webServiceReturn.Error)

  ######################################################################################################
  def cancelRecording(self, userid, password, progDetails):
	import suds.client
	url = "http://" + self.ip + ":" + str(self.port) + NEWA_WS_SCHEDULE_PATH
	
	client = suds.client.Client(url,cache=None)
	
	authObj = client.factory.create('webServiceAuthentication')
	
	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)

	print progDetails

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

	return (not ret_soap.webServiceEPGEventObjects.webServiceReturn.Error)

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
		for prog in prog1:
			theDict = self._rec2dict(prog)
			retArr.append(theDict)

	return retArr

  # Helper functions
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
		print epgo

	if time.daylight != 0:
		offset = timedelta(seconds=time.timezone) - timedelta(seconds=time.altzone)
	else:
		offset = 0

	if prog is not None:
		theDict['title'] = prog.Title
		theDict['start'] = prog.StartTime + offset
		theDict['end'] = prog.EndTime + offset
		if prog.Desc is not None:
			theDict['desc'] = prog.Desc.encode('utf-8')
		else:
			theDict['desc'] = ""
		if prog.Subtitle is not None:
			theDict['subtitle'] = prog.Subtitle.encode('utf-8')
		else:
			theDict['subtitle'] = ""
		theDict['program_oid'] = prog.OID
		if prog.ChannelOid is not 0:
			theDict['channel_oid'] = prog.ChannelOid
		if prog.HasSchedule:
			theDict['recording_oid'] = rec.OID
			if prog.ChannelOid == 0:
				theDict['channel_oid'] = rec.ChannelOid
			if rec.RecordingFileName is not None:
				theDict['directory'] = rec.RecordingFileName[1:-1]
			else:
				theDict['directory'] = "Default"
		theDict['priority'] = 0
		if prog.OID > 0 and rec.Status != "Completed" and rec.Status != "Failure": 
			theDict['rec'] = True
		else:
			theDict['rec'] = False
		theDict['directory'] = ""
	else:
		theDict['title'] = rec.Name
		theDict['start'] = rec.StartTime + offset
		theDict['end'] = rec.EndTime + offset
		theDict['desc'] = ""
		theDict['subtitle'] = ""
		theDict['program_oid'] = None
		theDict['recording_oid'] = rec.OID
		theDict['priority'] = rec.Priority
		theDict['channel_oid'] = rec.ChannelOid
		theDict['rec'] = False
		theDict['directory'] = ""

	if rec.Status is not None:
		theDict['status'] = rec.Status
	else:
		theDict['status'] = ""

	if str(theDict['channel_oid']) in self.channels:
		theDict['channel'] = self.channels[str(theDict['channel_oid'])]
	else:
		theDict['channel'] = "Unknown"
	if rec.Status == 'Recuyring':
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
	prog = epgo[0].webServiceEPGEventObject

#	if L.webServiceEPGEventObject is not None:
#		prog = L.webServiceEPGEventObject


	if prog.HasSchedule is True:
		rec = epgo[0].webServiceScheduleObject 
	
	if prog.Title is not None:
		theDict['title'] = prog.Title
	else:
		theDict['title'] = rec.Name
	
	if time.daylight != 0:
		offset = timedelta(seconds=time.timezone) - timedelta(seconds=time.altzone)
	else:
		offset = 0

	if prog.StartTime.year > 1:
                theDict['start'] = prog.StartTime + offset
                theDict['end'] = prog.EndTime + offset
        else:
                theDict['start'] = rec.StartTime + offset
                theDict['end'] = rec.EndTime + offset

	if prog.Desc is not None:
		theDict['desc'] = prog.Desc
	else:
		theDict['desc'] = ""
	
	if prog.Subtitle is not None:
		theDict['subtitle'] = prog.Subtitle
	else:
		theDict['subtitle'] = ""
	
	theDict['program_oid'] = prog.OID

	if prog.OID > 0:
		theDict['rec'] = True
	else:
		theDict['rec'] = False
	if prog.HasSchedule is True:
		theDict['priority'] = rec.Priority
		if rec.Status == 'Recurring':
			theDict['rectype'] = prog.recordingType
		else:
			theDict['rectype'] = self.SCHEDULE_ONCE
		if rec.RecordingFileName is not None:
			theDict['directory'] = rec.RecordingFileName[1:-1]
		else:
			theDict['directory'] = "Default"
		theDict['status'] = rec.Status
		theDict['recording_oid'] = rec.OID
	else:
		theDict['priority'] = ""
		theDict['rectype'] = ""
		theDict['status'] = ""
		theDict['recording_oid'] = ""
	if prog.ChannelOid is not 0:
		theDict['channel_oid'] = prog.ChannelOid
	else:
		theDict['channel_oid'] = rec.ChannelOid

	if str(theDict['channel_oid']) in self.channels:
		theDict['channel'] = self.channels[str(theDict['channel_oid'])][0]
	else:
		theDict['channel'] = "Unknown" 
	return theDict


  ######################################################################################################
  # Translating a (soap)1 recordingobject into a dictionary object...
  ######################################################################################################
  def _rec2dict2(self, epgo):
	theDict = {}
	q = epgo.webServiceReturn
	rec = epgo.webServiceRecurringObject
	theDict['title'] = rec.Name
	if time.daylight != 0:
		offset = timedelta(seconds=time.timezone) - timedelta(seconds=time.altzone)
	else:
		offset = 0
	
	theDict['start'] = rec.StartTime + offset
	theDict['end'] = rec.EndTime + offset
	#todo fix Rules display
	rules = rec.RulesXmlDoc.Rules
	theDict['desc'] = str(rules)
	try:
		theDict['directory'] = rules.RecordingDirectoryID[1:-1]
	except:
		theDict['directory'] = "Default"

	theDict['subtitle'] = ""
	
	theDict['program_oid'] = rec.OID

	theDict['rec'] = False

	theDict['priority'] = rec.Priority
	theDict['rectype'] = rec.Type
	theDict['status'] = ""
	theDict['recording_oid'] = rec.OID

	theDict['channel_oid'] = rec.ChannelOid

	if str(theDict['channel_oid']) in self.channels:
		theDict['channel'] = self.channels[str(theDict['channel_oid'])][0]
	else:
		theDict['channel'] = "Unknown"

	theDict['genres'] = ""
	theDict['recquality'] = rec.Quality
	theDict['prepadding'] = rec.PrePadding
	theDict['postpadding'] = rec.PostPadding
	theDict['maxrecs'] = rec.MaxRecordings
	return theDict

  ######################################################################################################
  # Translating a (soap) programmelist into an array of dictionaries...
  ######################################################################################################
  def _progs2array(self, soapObj):

	print "Processing listings start"

	retArr = []

	if time.daylight != 0:
		offset = timedelta(seconds=time.timezone) - timedelta(seconds=time.altzone)
	else:
		offset = 0
	
	for chnl in soapObj.webServiceGuideListing.webServiceGuideChannel:
		channel = {}
		channel['name'] = chnl.channelName
		channel['oid'] = chnl.channelOID
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

			dic['start'] = prog.StartTime + offset
			dic['end'] = prog.EndTime + offset

			dic['oid'] = prog.OID
			if prog.HasSchedule is True:
				rec = event.webServiceEPGEventObjects.webServiceScheduleObject
				if rec.Status == 'Pending' or rec.Status == 'In-Progress':
					dic['rec'] = True
				else:
					dic['rec'] = False
			else:
				dic['rec'] = False
			#todo are genres used
			if prog.Genres:
				dic['genres'] = prog.Genres.Genre
			else:
				dic['genres'] = ''		
			progs.append(dic)
		channel['progs'] = progs
		retArr.append(channel)
	print "Process listing end"
	return retArr


  ######################################################################################################
  # Translating a (soap) detailrecord into a dictionary...
  ######################################################################################################
  def _detail2array(self, soapObj):
	print "Detail error returns: " + str(soapObj.webServiceEPGEventObjects.webServiceReturn.Error)

	dict = {}

	if soapObj.webServiceEPGEventObjects.webServiceReturn.Error is True:
		print soapObj.webServiceEPGEventObjects.webServiceReturn.Message
		print soapObj
		return dict
	
	if  time.daylight != 0:
		offset = timedelta(seconds=time.timezone) - timedelta(seconds=time.altzone)
	else:
		offset = 0

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
		dict['title'] = rec.Name
		dict['start'] = rec.StartTime + offset
		dict['end'] = rec.EndTime + offset
		dict['desc'] = ""
		dict['subtitle'] = ""
		dict['channel_oid'] = rec.OID
		dict['program_oid'] = None
		dict['genres'] = ''		

	if prog is not None:
		if prog.Title is not None:
			dict['title'] = prog.Title
		else:
			dict['title'] = rec.Name
		
	
		if prog.StartTime.year > 1:
				dict['start'] = prog.StartTime + offset
				dict['end'] = prog.EndTime + offset
		else:
				dict['start'] = rec.StartTime + offset
				dict['end'] = rec.EndTime + offset
	
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
		else:
			dict['genres'] = ''		

	if str(dict['channel_oid']) in self.channels:
		dict['channel'] = self.channels[str(dict['channel_oid'])]
	else:
		dict['channel'] = "Unknown"
		
	
	if rec is not None:
		dict['status'] = rec.Status
		if rec.Status == "Completed" or rec.Status == "In-Progress":
			f = rec.RecordingFileName.replace("\\","/")
			dict['filename'] = f
			dict['resume'] = rec.PlaybackPosition
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
	#	dict['genres'] = ""
	#except:
	#	pass

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
				retDic[str(n.nodeName)] = str(n.firstChild.nodeValue)
		
		retArr.append(retDic)

	return retArr

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
#	print timeString
	encodingSalt = self._hashMe(timeString)
        
	pwdHash = self._hashMe(password)
	pwd = self._Encrypt(password, pwdHash, encodingSalt)
	id = self._Encrypt(userid, pwdHash, encodingSalt);

	myguid = self._Guid();
	#We're encrypting the date/time we used to create the salt with the guid so the decrypt of the re-passed credentials knows
	#what is used as the salt
	RL = self._Encrypt(str ( len ( id ) ), pwdHash, myguid);
	myObj.RL = RL

	rt = self._Encrypt(timeString, pwdHash, myguid);

	RTL = self._Encrypt(str ( len (rt ) ), pwdHash, myguid);
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
            s.sendto(msg, (broadcast_address, 7))
            s.close()
    except:
        import traceback
        traceback.print_exc()
        return

#################################################################################################################
def _isIP(ip):
   # Check if my IP address has 4 numbers separated by dots
   num=ip.split('.')
   if not len(num)==4:
       return False
   # Check each of the 4 numbers is between 0 and 255
   for n in num:
       try:
           if int(n) < 0 or int(n) > 255:
               return False
       except:
           return False
   return True

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

def checkCache(cached):
	if os.path.isfile(cached) == True:
		ft =  datetime.datetime.fromtimestamp(os.path.getmtime(cached))
		if ft + timedelta(hours=2) > datetime.datetime.now():
			return True

	return False


