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
GBPVR_XMLINFO_PATH = "/public/services/InfoXML.aspx"
GBPVR_WS_MANAGE_PATH = "/public/services/ManageService.asmx?WSDL"
GBPVR_WS_SEARCH_PATH = "/public/services/SearchService.asmx?WSDL"
GBPVR_WS_DETAIL_PATH = "/public/services/DetailService.asmx?WSDL"
GBPVR_WS_GUIDE_PATH = "/public/services/GuideService.asmx?WSDL"
GBPVR_WS_SCHEDULE_PATH = "/public/services/ScheduleService.asmx?WSDL"

Last_Error = ""
# For WS Search functions, sort and filters....
# Sort fields

import time
from datetime import timedelta

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
	self.ip = ip;
	self.port = port;
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

  ######################################################################################################
  # Retrieving XMLInfo information and returning in dictionary
  ######################################################################################################
  def GetGBPVRInfo(self, userid, password):
	import urllib2
	from xml.dom import minidom

	address = "http://" + self.ip + ":" + str(self.port) + GBPVR_XMLINFO_PATH
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

	return dic

  ######################################################################################################
  # Retrieves a list of channels...
  ######################################################################################################
  def getChannelList(self, userid, password):

	import suds.client
  	print "getChannelList start"

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_SEARCH_PATH

	client = suds.client.Client(url,cache=None)

	authObj = client.factory.create('webServiceAuthentication')

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)

	ret_soap = client.service.getChannelListObject(soapheaders=authObj)
	dic = {}
	for chan in ret_soap.anyType:
		temp = chan.split(',')
		dic[temp[2]] = ( temp[1].encode('latin-1'),temp[0] )
  	print "getChannelList end"
	return dic


  ######################################################################################################
  # Retrieves a list of channelGroups...
  ######################################################################################################
  def getChannelGroupList(self, userid, password):

	import suds.client
  	print "getChannelGroupList start"

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_GUIDE_PATH

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
  def getDetails(self, userid, password, oid, type):

	import suds.client


	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_DETAIL_PATH

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

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_GUIDE_PATH
	
	if group is not None:
		print group
		print self.channelGroups
		if group not in self.channelGroups:
			print group + " group not found"
			caseGroup = None
			for groups in self.channelGroups:
				if groups.lower() == group.lower():
					print groups + " group found"
					caseGroup = groups
			group = caseGroup

	print "getGuideInfo start"

	client = suds.client.Client(url,cache=None)
	client.set_options(cache=None)
	authObj = client.factory.create('webServiceAuthentication')

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)
	ret_soap = client.service.getGuideObject( timeStart, timeEnd, channelGroup=group, soapheaders=authObj)
  	print "getGuideInfo end"	
	return self._progs2array(ret_soap)
  
  ######################################################################################################
  def getUpcomingRecordings(self, userid, password, amount=0):

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_MANAGE_PATH

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

	return self._recs2array(ret_soap)

  ######################################################################################################
  def getRecentRecordings(self, userid, password, amount=0):

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_MANAGE_PATH

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
	return self._recs2array(ret_soap)

  ######################################################################################################
  def getConflicts(self, userid, password, conflictRec):

	import suds.client
        # First, we get a list of recordings sorted by date.....

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_MANAGE_PATH

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

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_SEARCH_PATH
	
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
	return self._recs2array1(ret_soap)
  
  ######################################################################################################
  def getScheduledRecordings(self, userid, password):

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_MANAGE_PATH

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
	return self._recs2array2(ret_soap)

  ######################################################################################################
  def getConflictedRecordings(self, userid, password):

	import suds.client

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_MANAGE_PATH

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

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_MANAGE_PATH

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

	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_SCHEDULE_PATH

	client = suds.client.Client(url,cache=None)

	authObj = client.factory.create('webServiceAuthentication')

	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	recObj = client.factory.create('webServiceScheduleSettings')
        qualObj = client.factory.create('Quality')

        if progDetails['recquality'].lower() == "low":
                 recObj.quality = qualObj.Low
        elif progDetails['recquality'].lower() == "medium":
                recObj.quality = qualObj.Medium
        elif progDetails['recquality'].lower() == "high":
                recObj.quality = qualObj.High
        elif progDetails['recquality'].lower() == "custom1":
                recObj.quality = qualObj.Custom1
        else:
                recObj.quality = qualObj.Custom2
        recObj.qualityHigh = qualObj.High
        recObj.qualityMedium = qualObj.Medium
        recObj.qualityLow = qualObj.Low
        recObj.qualityCustom1 = qualObj.Custom1
        recObj.qualityCustom2 = qualObj.Custom2
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
	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_SCHEDULE_PATH
	client = suds.client.Client(url,cache=None)
	authObj = client.factory.create('webServiceAuthentication')
	
	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	recObj = client.factory.create('webServiceScheduleSettings')
	qualObj = client.factory.create('RecordingQuality')
	if progDetails['recquality'].lower() == "low":
		recObj.quality = qualObj.QUALITY_GOOD
	elif progDetails['recquality'].lower() == "medium":
		recObj.quality = qualObj.QUALITY_BETTER
	elif progDetails['recquality'].lower() == "high":
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
	
	recordDayIntervalType = client.factory.create('recordDayIntervalType')
	recordTimeIntervalType = client.factory.create('recordTimeIntervalType')

	if progDetails['rectype'] == 'Once':
		recObj.recordTimeInterval = recordTimeIntervalType.recordOnce
		recObj.recordDayInterval = recordDayIntervalType.recordThisDay
	else:
		recObj.recordTimeInterval = recordTimeIntervalType.recordThisTimeslot
		recObj.recordDayInterval = recordDayIntervalType.recordAnyDay
	
	recObj.allChannels = "false"

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
	
	url = "http://" + self.ip + ":" + str(self.port) + GBPVR_WS_SCHEDULE_PATH
	
	client = suds.client.Client(url,cache=None)
	
	authObj = client.factory.create('webServiceAuthentication')
	
	# Fill authentication object
	authObj = self._AddAuthentication(authObj, userid, password)
	
	client.set_options(soapheaders=authObj)
	print progDetails['status']
	
	if progDetails['status'].lower() == "recurring":
		debug("Cancelling")
		ret_soap = client.service.cancelRecording(progDetails['recording_oid'], soapheaders=authObj)
	elif progDetails['status'].lower() == "pending":
		debug("Cancelling")
		ret_soap = client.service.cancelRecording(progDetails['recording_oid'], soapheaders=authObj)
	elif progDetails['status'].lower() == "conflict":
		debug("Cancelling")
		ret_soap = client.service.cancelRecording(progDetails['recording_oid'], soapheaders=authObj)
	elif progDetails['status'].lower() == "in progress":
		debug("Cancelling and Deleting")
		ret_soap = client.service.cancelAndDeleteRecording(progDetails['recording_oid'], soapheaders=authObj)
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
	if L[1].webServiceEPGEventObject is not None:
		prog = L[1].webServiceEPGEventObject
	if prog.HasSchedule:
		rec = L[1].webServiceScheduleObject
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
		theDict['desc'] = prog.Desc.encode('utf-8')
	else:
		theDict['desc'] = ""

	if prog.Subtitle is not None:
		theDict['subtitle'] = prog.Subtitle.encode('utf-8')
	else:
		theDict['subtitle'] = ""
	theDict['program_oid'] = prog.OID
	theDict['recording_oid'] = rec.OID
        if prog.OID > 0:
                theDict['rec'] = True
        else:
                theDict['rec'] = False
	theDict['priority'] = rec.Priority

	if prog.ChannelOid is not 0:
		theDict['channel_oid'] = prog.ChannelOid
	else:
		theDict['channel_oid'] = rec.ChannelOid

	if rec.Status is not None:
		theDict['status'] = rec.Status
	else:
		theDict['status'] = ""
	if str(theDict['channel_oid']) in self.channels:
		theDict['channel'] = self.channels[str(theDict['channel_oid'])]
	else:
		theDict['channel'] = "Unknown"
	if rec.Status == 'Recuring':
		theDict['rectype'] = prog.recordingType
	else:
		theDict['rectype'] = self.SCHEDULE_ONCE
        
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
		rec = L.webServiceScheduleObject 
	
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
		if rec.Status == 'Recuring':
			theDict['rectype'] = prog.recordingType
		else:
			theDict['rectype'] = self.SCHEDULE_ONCE
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

	return theDict

  ######################################################################################################
  # Translating a (soap) programmelist into an array of dictionaries...
  ######################################################################################################
  def _progs2array(self, soapObj):
	retArr = []
	print "Processing listings start"
	if time.daylight != 0:
		offset = timedelta(seconds=time.timezone) - timedelta(seconds=time.altzone)
	else:
		offset = 0
	
	for chnl in soapObj.webServiceGuideListing.webServiceGuideChannel:
		channel = {}
		channel['name'] = chnl.channelName
		channel['oid'] = chnl.channelOID
		evt = chnl[3].webServiceEPGEvent
		progs = []
		for p2 in evt:
			for p1 in p2:
				prog = p1[1].webServiceEPGEventObject
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
					dic['rec'] = True
				else:
					dic['rec'] = False
				#todo fix genres
				dic['genre'] = "" 
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

	if soapObj.webServiceEPGEventObjects.webServiceReturn.Error is True:
		print soapObj.webServiceEPGEventObjects.webServiceReturn.Message
		print soapObj
		dict = {}
		return dict
	
	L = soapObj.webServiceEPGEventObjects

	if L.webServiceEPGEventObject is not None:
		prog = L.webServiceEPGEventObject
	else:
		prog = L.webServiceRecurringObject

	if prog.HasSchedule is True:
		rec = L.webServiceScheduleObject

	dict = {}
	if prog.Title is not None:
		dict['title'] = prog.Title
	else:
		dict['title'] = rec.Name
	
	if  time.daylight != 0:
		offset = timedelta(seconds=time.timezone) - timedelta(seconds=time.altzone)
	else:
		offset = 0

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

	if str(dict['channel_oid']) in self.channels:
		dict['channel'] = self.channels[str(dict['channel_oid'])]
	else:
		dict['channel'] = "Unknown"
		
	dict['program_oid'] = prog.OID
	
	if prog.HasSchedule is True:
		dict['status'] = rec.Status
		if rec.Status == "Completed" or rec.Status == "In-Progress":
			dict['filename'] = rec.RecordingFileName
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
		dict['recording_oid'] = ""
		dict['rectype'] = ""
		dict['recday'] = ""
		dict['recquality'] = ""
		dict['prepadding'] = ""
		dict['postpadding'] = ""
		dict['maxrecs'] = ""
		dict['priority'] = ""
	dict['genres'] = []
	try:
		dict['genres'] = ""
	except:
		pass

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

