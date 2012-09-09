#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
	X-NEWA

	Controlling NextPVR from within XBMC.

	Written By Ton van der Poel
	Updated by emveepee

	THANKS:
	To everyone who's ever helped in anyway, or if I've used code from your own scripts, MUCH APPRECIATED!

    Additional support may be found on xboxmediacenter forum.	
"""

import xbmc, xbmcgui
import sys, re, time, os
from os import path, listdir
from string import replace, split, upper, lower, capwords, join,zfill
from datetime import date, datetime, timedelta
import traceback

# Script doc constants
__scriptname__ = "myGBPVR"
__version__ = '2.0.0'
__orgiginal_author__ = 'Ton van der Poel'
__author__ = 'emveepee'
__date__ = '2012-09-03'
xbmc.log(__scriptname__ + " Version: " + __version__ + " Date: " + __date__)

# Shared resources
from myGBPVRGlobals import *
#todo what is DIR_HOME?
DIR_HOME =  WHERE_AM_I.replace( ";", "" )
DIR_RESOURCES = os.path.join( DIR_HOME , "resources" )
DIR_RESOURCES_LIB = os.path.join( DIR_RESOURCES , "lib" )
DIR_USERDATA = xbmc.translatePath("/".join( ["T:", "script_data", __scriptname__] ))
DIR_CACHE = os.path.join( DIR_USERDATA, "cache" )
DIR_PIC = os.path.join( DIR_RESOURCES, "src", "images" )
sys.path.insert(0, DIR_RESOURCES_LIB)

from fanart import fanart
#################################################################################################################
# MAIN
#################################################################################################################
class EpgWindow(xbmcgui.WindowXML):
	# control id's
	CLBL_PROG_TITLE = 1020
	CLBL_PROG_DESC = 1030
	CLBL_DATASOURCE = 1050
	CLBL_SAVEPROG = 1060
	CGRP_NAV_LISTS = 1100
	CLST_CHANNEL = 1110
	CLST_DAY = 1120
	CLST_HOUR = 1130
	CGRP_EPG = 1300
	CLBL_CH_NAME = 1310
	
	def __init__(self, *args, **kwargs):
		debug("--> myGBPVR()__init__")
#        	xbmcgui.WindowXML.__init__(self, *args, **kwargs)

		# Need to get: oid and gbpvr....
        	self.settings = kwargs['settings']
        	self.gbpvr = kwargs['gbpvr']

		self.currentTime = datetime.now()

		self.epgTimerBars = []

		# Channel stuff
		self.epgChNames = []
		self.epgChLogos = []
		self.ChLogos = []
		self.epgButtons = []
		self.epgTagData = {}
		self.channelTop = -999
		self.channelCount = 0
		self.MaxDisplayChannels = 0
		self.initDate = self.getStartTime()
		self.EPGEndTime = datetime.now()
		self.ready = False
		self.epgData = []
		self.isStartup = True
		self.fanart = fanart()

		ret = self.loadGBPVR()
		#ret = True
		if not ret:
			self.cleanup()
			self.close()
		else:
			self.ready = True

		debug("<-- myGBPVR()__init__")

	#################################################################################################################
	def onInit( self ):
		debug("> onInit() isStartup=%s" % self.isStartup)
		self.upArrow = self.getControl(1301)
		self.downArrow = self.getControl(1302)

		if self.isStartup:
			self.ready = False

			# Store resolution
			self.rez = self.getResolution()
			# debug("onInit() resolution=%s" % self.rez)

			self.epgSetup()		
			self.updateTimeBars(0)
			self.updateChannels(0)
			self.upArrow = self.getControl(1301)
			self.downArrow = self.getControl(1302)

			# debug("Trying setfocus...")
			self.setFocus(0, 0)
			# debug("Done setfocus...")

			self.isStartup = False
			self.ready = True

		debug("< onInit()")

	#################################################################################################################
	def loadGBPVR(self, theDate=None):
		# Todo: Error-Handling
		debug("--> loadGBPVR" )
		success = True

                if theDate is None:
                        theDate = self.initDate
                        
		myDlg = xbmcgui.DialogProgress()
		myDlg.create("Loading TV Guide ...", "Please wait ...")

		myDlg.update(33, "Downloading ...")

		# Todo: Get correct times....
		tdate = theDate
		if time.daylight != 0:
			tdate1 = tdate + timedelta(seconds=time.altzone)
		else:
			tdate1 = tdate + timedelta(seconds=time.timezone)
		cstart = tdate1.strftime("%Y-%m-%dT%H:%M:00")
		tdate = tdate + timedelta(hours=self.settings.EPG_RETR_INT)
		self.EPGEndTime = tdate
		if time.daylight != 0:
			tdate = tdate + timedelta(seconds=time.altzone)
		else:
			tdate = tdate + timedelta(seconds=time.timezone)
		cend = tdate.strftime("%Y-%m-%dT%H:%M:00")


		channelGroup = self.settings.EPG_GROUP
                if self.gbpvr.AreYouThere(self.settings.usewol(), self.settings.GBPVR_MAC, self.settings.GBPVR_BROADCAST):
                    try:
                        self.epgData = self.gbpvr.getGuideInfo(self.settings.GBPVR_USER, self.settings.GBPVR_PW, cstart, cend, channelGroup)
                    except:
                        xbmcgui.Dialog().ok('Sorry', 'Error retrieving EPG data!')

		myDlg.update(66, "Downloading ...")

		chCount = len(self.epgData)
		# debug ("Channelcount: %s" %(chCount) )
		if not chCount:
			success = False

		if success:
			self.channelCount = chCount
			# load genres
			self.initGenre()
			self.initChannelIcons()

		self.ChLogos = []
		for a in self.epgData:
			cfile = self.fanart.getChannelIcon(a['name'])
			if cfile is not None:
				self.ChLogos.append(cfile)
			else:
				self.ChLogos.append('noimage.png')

		myDlg.update(100, "Complete")
		myDlg.close()
		debug("<-- loadGBPVR() success=%s" % success)
		return True

	###############################################################################################################
	# load genre icons/colours
	def initGenre(self):
		debug("--> initGenre()")
		self.genreIcons={}

		try:
			# GENRES ICONS - (not all datasources use this)
			path = os.path.join( DIR_HOME , "icons" )
			path = os.path.join( path , "genre" )
			debug("Genre path: " + path)

			self.genreIcons = getFilesInpath(path)
		except:
			debug("Error in Genres!")
			handleException()

		# debug("Genres found: %s" %(len(self.genreIcons)) )

		debug("<-- initGenre()")

	###############################################################################################################
	# load channel icons
	def initChannelIcons(self):
		debug("--> initChannelIcons()")
		self.channelIcons={}

		try:
			path = os.path.join( DIR_HOME , "icons" )
			path = os.path.join( path , "channels" )
			debug("Channel-Icon path: " + path)

			self.channelIcons = getFilesInpath(path)
		except:
			handleException()

		# debug("Channal-icons found: %s" %(len(self.channelIcons)) )

		debug("<-- initChannelIcons()")

	###############################################################################################################
	def epgSetup(self):
		debug("--> epgSetup()")
		#xbmcgui.lock()

		# title
		self.getControl(self.CLBL_PROG_TITLE).setLabel("Program Title")

		# title short desc
		self.getControl(self.CLBL_PROG_DESC).setLabel("Description")
		self.getControl(self.CLBL_PROG_DESC).setVisible(True)

		# Set up row sizes....
		EPG_ROW_HEIGHT = self.settings.EPG_ROW_HEIGHT
		EPG_GAP_HEIGHT = 2
		self.epgRowH = EPG_ROW_HEIGHT
		self.epgRowFullH = EPG_ROW_HEIGHT + EPG_GAP_HEIGHT
		# debug("epgRowH: %s epgRowGapH: %s = epgRowFullH:%s"  % (self.epgRowH,EPG_GAP_HEIGHT,self.epgRowFullH))

		# Set up EPG program-sizes and heights
		epgCtrl = self.getControl(self.CGRP_EPG)
		epgW = epgCtrl.getWidth()
		self.epgH = epgCtrl.getHeight()
		self.epgX, self.epgY = epgCtrl.getPosition()
		# debug("epgX: %s epgY: %s epgW: %s epgH: %s"  % (self.epgX,self.epgY,epgW,self.epgH))

		# Other Stuff
		self.epgTimeBarH = 35
		self.epgColGap = 3
		epgChNameW = self.getControl(self.CLBL_CH_NAME).getWidth()

		# Calculate space, size and position for EPG entries
		self.epgProgsW = epgW - epgChNameW - self.epgColGap
		self.epgProgsX = self.epgX + epgChNameW + self.epgColGap
		self.epgProgsY = self.epgY + self.epgTimeBarH
		self.epgProgsH = self.epgH - self.epgTimeBarH
		# debug("epgChNameW=%s epgProgsW=%s epgProgsH=%s epgProgsX=%s epgProgsY=%s"  % \
		#			(epgChNameW,self.epgProgsW,self.epgProgsH,self.epgProgsX,self.epgProgsY))

		# calc epg space available for just epg rows to fit in (relies on epgProgsH & epgRowFullH)
		self.MaxDisplayChannels = self.getMaxDisplayChannels()

		# Set up "Now Time" indicator line....
		try:
			self.removeControl(self.nowTimeCI)
		except: pass

		ypos = self.epgY+1
		# Todo: get from Media directory
		ICON_NOW_TIME = os.path.join(DIR_PIC,'nowtime.png')
		self.nowTimeCI = xbmcgui.ControlImage(10, ypos, 0, self.epgH, ICON_NOW_TIME)	# off screen
		self.nowTimeCI.setVisible(True)
		self.addControl(self.nowTimeCI)

		# Calculate Time Intervals
		self.TimeIntervals = int(self.settings.EPG_DISP_INT / self.settings.EPG_SCROLL_INT) + 1
		sst = "Time Ints: " + str(self.TimeIntervals)
		sst = "TIME DIS: " + str(self.settings.EPG_DISP_INT)
		sst = "TIME SCR: " + str(self.settings.EPG_SCROLL_INT)
		self.epgTimeIntervalW = int(self.epgProgsW / (self.TimeIntervals))
		# Add one for date
		self.TimeIntervals = self.TimeIntervals + 1
		self.epgPixelsPerMin = float(self.epgTimeIntervalW) / float(self.settings.EPG_SCROLL_INT)
		# debug("epgTimeIntervalW=%s epgPixelsPerMin=%s" % (self.epgTimeIntervalW, self.epgPixelsPerMin))

		# remove old timebar ctrls
		try:
			for ctrl in self.epgTimeBar:
				self.removeControl(ctrl)
		except: pass

		# create new timebar ctrls
		self.epgTimerBars = []
		FONT12 = 'font12'

		crtl = xbmcgui.ControlLabel(self.epgX, self.epgY, epgChNameW, self.epgTimeBarH, \
									'', FONT12, '0xFFFFFF00')

		self.epgTimerBars.append(crtl)
		crtl.setLabel("Base")
		self.addControl(crtl)
		tempX = self.epgProgsX

		for i in range(self.TimeIntervals -1):
			ctrl = xbmcgui.ControlLabel(tempX-45, self.epgY, 90, self.epgTimeBarH, '', FONT12, '0xFFFFFF66', alignment=0x00000002)
			self.epgTimerBars.append(ctrl)
			ctrl.setLabel("Int")
			self.addControl(ctrl)
			tempX += self.epgTimeIntervalW

		# CHANNEL NAMES
		try:
			for ctrl in self.epgChNames:
				self.removeControl(ctrl)
		except: pass
		try:
			for ctrl in self.epgChLogos:
				self.removeControl(ctrl)
		except: pass

		self.epgChNames = []
		self.epgChLogos = []
		# check if were going to use ch names
		CHANNEL_FONT = 'font11'
		CHANNEL_COLOR = "0xFFFFFFFF"
		colour = CHANNEL_COLOR
		font = CHANNEL_FONT
		XBFONT_CENTER_Y   = 0x00000004
		tempY = self.epgProgsY
                USE_CHANNELS = 1
		CHANNEL_WIDTH = 75
		CHANNEL_GAP = 10
		ChLogoPos = self.epgX
		ChTextPos = ChLogoPos + CHANNEL_WIDTH + CHANNEL_GAP
		for i in range(self.MaxDisplayChannels):
			ctrl = xbmcgui.ControlLabel(ChTextPos, tempY, epgChNameW, self.epgRowH, '', \
							font, colour, alignment=XBFONT_CENTER_Y)
			self.epgChNames.append(ctrl)
			self.addControl(ctrl)
			ctrl.setLabel("een channel")
			ctrl = xbmcgui.ControlImage(ChLogoPos, tempY, CHANNEL_WIDTH, self.epgRowH, 'noimage.png', aspectRatio=2)
			self.epgChLogos.append(ctrl)
			self.addControl(ctrl)
			tempY += self.epgRowFullH

		self.channelTop = -999

		# EPG Buttons..
		try:
			for lst in self.epgButtons:
				for ctrl in lst:
					self.removeControl(ctrl)
		except: pass
		self.epgButtons=[]
		for i in range(0, self.MaxDisplayChannels):
			self.epgButtons.append([])

		xbmcgui.unlock()

		debug("<-- epgSetup()")

	###############################################################################################
	def removeControl(self, ctrl):
		try:
			del self.epgTagData[ctrl.getId()]
		except:
			handleException()
			debug("Cannot remove control!")
			pass
		xbmcgui.WindowXML.removeControl(self, ctrl)

	###############################################################################################
	def setFocus(self, ctrl):
		raise NameError("Don't do that here!")

	###############################################################################################
	def setFocus(self, nRow, nButton):
		try:
			# debug("Row: %s, Button: %s" %(nRow, nButton) )
			while len(self.epgButtons[nRow]) == 0:
				nRow = nRow + 1
			ctrl = self.epgButtons[nRow][nButton]
			xbmcgui.WindowXML.setFocus(self, ctrl)
			self.idxRow = nRow
			self.idxButt = nButton
		except:
			handleException()
			debug("Something wrong in setfocus!!")
			pass

	###############################################################################################
	def reFocus(self):
		try:
			ctrl = self.epgButtons[self.idxRow][self.idxButt]
			xbmcgui.WindowXML.setFocus(self, ctrl)
		except:
			handleException()
			if self.idxButt == 0:
				return
			self.idxButt = self.idxButt - 1
			self.reFocus()
			pass

	###############################################################################################################
	def moveFocus(self, direction):
                #Todo: Fix for partially filled channel-data
		if direction==1: # Move right
			newIDX = self.idxButt +1
			if newIDX > len(self.epgButtons[self.idxRow])-1:
				self.updateTimeBars(+1)
				oldtop = self.channelTop
				self.channelTop = -999
				self.updateChannels(oldtop)
				self.reFocus()
				return
			try:
				self.setFocus(self.idxRow, self.idxButt+1)
			except:
				pass
		elif direction==2: # Move left
			newIDX = self.idxButt -1
			if newIDX < 0:
				self.updateTimeBars(-1)
				oldtop = self.channelTop
				self.channelTop = -999
				self.updateChannels(oldtop)
				self.reFocus()
				return
			try:
				self.setFocus(self.idxRow, newIDX)
			except:
				pass
		elif direction==3: # Move down
			newRow = self.idxRow + 1
			newIDX = self.idxButt
			if newRow > self.MaxDisplayChannels -1:
				self.updateChannels(self.channelTop+1)
				newRow = self.idxRow
			else: # This is new
                                while len(self.epgButtons[newRow]) == 0:
                                        newRow = newRow + 1
                                        if newRow > self.MaxDisplayChannels -1:
                                                # Last displayed row
                                                self.updateChannels(self.channelTop+1)
                                                newRow = self.idxRow - 1
                                                break;
                        # End of new
			if newIDX > len(self.epgButtons[newRow])-1:
				newIDX = len(self.epgButtons[newRow])-1
			try:
				self.setFocus(newRow, newIDX)
			except:
				pass
		else: # Move up
			newRow = self.idxRow - 1
			newIDX = self.idxButt
			if newRow < 0:
				self.updateChannels(self.channelTop-1)
				newRow = self.idxRow
			else: # This is new
                                while len(self.epgButtons[newRow]) == 0:
                                        newRow = newRow - 1
                                        if newRow < 0:
                                                # Last displayed row
                                                if self.channelTop < 0:
                                                        return
                                                self.updateChannels(self.channelTop-1)
                                                newRow = self.idxRow + 1
                                                break;
                        # End of new
			if newIDX > len(self.epgButtons[newRow])-1:
				newIDX = len(self.epgButtons[newRow])-1
			try:
				self.setFocus(newRow, newIDX)
			except:
				pass

	###############################################################################################
	def isReady(self):
		return self.ready

	###############################################################################################
	def scrollChannels(self, nDir):
		# debug("--> scrollChannels() nDir[=%s]" %(nDir))

		for row in self.epgButtons:
			for i in range (len(row)-1, -1, -1 ):
				posl, posy = row[i].getPosition()
				posl = posl + (self.epgTimeIntervalW * nDir)
				posr = posl + row[i].getWidth()
				cstr = row[i].getLabel()
				if posr < self.epgProgsX:
					self.removeControl(row[i])
					del row[i]
					continue
				elif posl > self.epgProgsX + self.epgProgsW:
					self.removeControl(row[i])
					del row[i]
					continue
				elif posl < self.epgProgsX:
					posl = self.epgProgsX
				elif posr > self.epgProgsX + self.epgProgsW:
					posr = self.epgProgsX + self.epgProgsW
				row[i].setPosition(posl, posy)
				row[i].setWidth(posr-posl)

		# debug("<-- scrollChannels() nDir[=%s]" %(nDir))

	###############################################################################################
	def updateChannels(self, newTop):
		# debug("--> updateChannels() newTop[=%s]" %(newTop))

		# debug("newTop: %s, channelTop: %s" %(newTop, self.channelTop) )
		# debug("Channels: %s, maxchdisp: %s" %(self.channelCount, self.MaxDisplayChannels) )

		if (newTop + self.MaxDisplayChannels > self.channelCount):
			# debug("Cannot move down...")
			# debug("<-- updateChannels() newTop[=%s]" %(newTop))
			return
		if newTop <0:
			# debug("Cannot move up...")
			# debug("<-- updateChannels() newTop[=%s]" %(newTop))
			return

		if (newTop + self.MaxDisplayChannels < self.channelCount):
			self.downArrow.setVisible(True)
		else:
			self.downArrow.setVisible(False)

		if newTop > 0:
			self.upArrow.setVisible(True)
		else:
			self.upArrow.setVisible(False)

		if (newTop + self.MaxDisplayChannels > self.channelCount):
			# debug("Cannot move down...")
			# debug("<-- updateChannels() newTop[=%s]" %(newTop))
			return
		if (newTop == self.channelTop+1):
			# Move one row down...
			self.deleteChannel(0)
			for i in range(0, self.MaxDisplayChannels):
				ctrl = self.epgChLogos[i]
				ctrl.setImage(self.ChLogos[i+newTop])
				ctrl = self.epgChNames[i]
				ctrl.setLabel(self.epgData[i+newTop]['name'])
				posX, posY = ctrl.getPosition()
				for butt in self.epgButtons[i]:
					oldX, oldY = butt.getPosition()
					butt.setPosition(oldX, posY)
			self.createChannel(self.MaxDisplayChannels-1, posY, newTop + self.MaxDisplayChannels-1, self.epgData[newTop + self.MaxDisplayChannels-1]['progs'])
			self.channelTop = newTop
		elif (newTop == self.channelTop-1):
			# Move one row up...
			self.deleteChannel(self.MaxDisplayChannels -1)
			for i in range(self.MaxDisplayChannels-1,-1,-1):
				ctrl = self.epgChLogos[i]
				ctrl.setImage(self.ChLogos[i+newTop])
				ctrl = self.epgChNames[i]
				ctrl.setLabel(self.epgData[i+newTop]['name'])
				posX, posY = ctrl.getPosition()
				for butt in self.epgButtons[i]:
					oldX, oldY = butt.getPosition()
					butt.setPosition(oldX, posY)
			self.createChannel(0, posY, newTop, self.epgData[newTop]['progs'])
			self.channelTop = newTop
		elif (newTop <> self.channelTop) and (newTop >= 0) and (newTop + self.MaxDisplayChannels <= self.channelCount):
			for i in range(0, self.MaxDisplayChannels):
				ctrl = self.epgChLogos[i]
				ctrl.setImage(self.ChLogos[i+newTop])
				ctrl = self.epgChNames[i]
				ctrl.setLabel(self.epgData[i+newTop]['name'])
				posX, posY = ctrl.getPosition()
				self.createChannel(i, posY, i+newTop, self.epgData[i+newTop]['progs'])
			self.channelTop = newTop		
		else:
			debug("Unable to move....")

		# debug("<-- updateChannels() newTop[=%s]" %(newTop))

	###############################################################################################################
	def showDescription(self, ctrlId):
		if not self.ready:
			return

		try:
			lst = self.epgTagData[ctrlId]
				
			# title
			self.getControl(self.CLBL_PROG_TITLE).setLabel(lst[3])
        
			if lst[1] == "None":
				lst[1] = ""
			if lst[2] == "None":
				lst[2] = ""
			if len(lst[1]) > 0:
				txt = lst[1] + "; " + lst[2]
			else:
				txt = lst[2]
			
			self.getControl(self.CLBL_PROG_DESC).setLabel(txt)
		except:
			pass

	###############################################################################################################
	def onClick(self, controlID):
		if not self.ready:
			return

		import details

		oid = self.epgTagData[controlID][0]
        	detailDialog = details.DetailDialog("nextpvr_details.xml",  WHERE_AM_I, gbpvr=self.gbpvr, settings=self.settings, oid=oid, epg=True, type="E")
        	detailDialog.doModal()
        	if detailDialog.returnvalue is not None:
                        # First, get the epgData item....
                        ctrl = self.getControl(controlID)
                        epgChannel = self.epgTagData[controlID][4]
                        epgProgram = self.epgTagData[controlID][5]
                        if detailDialog.returnvalue == "REC":
                                self.epgData[epgChannel]['progs'][epgProgram]['rec'] = True
                        else:
                                self.epgData[epgChannel]['progs'][epgProgram]['rec'] = False
                        oldtop = self.channelTop
                        self.channelTop = -999
                        self.updateChannels(oldtop)
                        self.reFocus()

	###############################################################################################################
	def onFocus(self, controlID):
		self.showDescription(controlID)
	    
	##############################################################################################################
        def _goToDate(self):
                # Show date select....
                nowdate = datetime.now()
                nowdate = nowdate + timedelta(hours=1)
                theDate = nowdate
                theDays = []
                for i in range(5):
                        theDays.append(nowdate.strftime("%A, %B %d") )
                        nowdate = nowdate + timedelta(days=1)
                theDlg = xbmcgui.Dialog()
                pos = theDlg.select('Pick date:', theDays)
                if pos <0:
                        return
                theDate = theDate + timedelta(days=pos)
                nowdate = nowdate.replace(hour=19, minute=0)
                theHours = []                
                for i in range(12):
                        theHours.append(nowdate.strftime("%H:%M") )
                        nowdate = nowdate + timedelta(hours=2)
                pos = theDlg.select('Pick time:', theHours)
                if pos <0:
                        return
                pos = 19 + (pos * 2)
                while pos>23:
                        pos = pos - 24
                theDate = theDate.replace(hour=pos, minute=0)
                theDlg.ok("Here","Would now skip to: " + theDate.strftime("%A, %B %d %H:%M") )
                self.initDate = theDate
                self.epgStartTime = theDate
                self.loadGBPVR(theDate)
                self.updateTimeBars(0)
                self.channelTop = -999
                self.updateChannels(0)
                self.setFocus(0, 0)

	##############################################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			buttonID = action.getButtonCode()
		except: return                

		if actionID in EXIT_SCRIPT or buttonID in EXIT_SCRIPT:
			self.ready = False
			#self.cleanup()
			self.close()
			return
		elif not self.ready:
			return

		self.ready = False

		if actionID in CONTEXT_MENU or buttonID in CONTEXT_MENU:
                        self._goToDate()
		if actionID in MOVEMENT_DOWN or buttonID in MOVEMENT_DOWN:
			#self.updateChannels(self.channelTop+1)
			self.moveFocus(3)
		if actionID in MOVEMENT_UP or buttonID in MOVEMENT_UP:
			self.moveFocus(4)
			#self.updateChannels(self.channelTop-1)
		if actionID in MOVEMENT_SCROLL_DOWN or buttonID in MOVEMENT_SCROLL_DOWN:
			i = self.channelTop + self.MaxDisplayChannels -1
			if i > (self.channelCount - self.MaxDisplayChannels):
				i = self.channelCount - self.MaxDisplayChannels
			self.updateChannels(i)
		if actionID in MOVEMENT_SCROLL_UP or buttonID in MOVEMENT_SCROLL_UP:
			i = self.channelTop - self.MaxDisplayChannels + 1
			if i < 0:
				i = 0
			self.updateChannels(i)
		if actionID in MOVEMENT_LEFT or buttonID in MOVEMENT_LEFT:
			self.moveFocus(2)
			#self.updateTimeBars(-1)
			#self.updateChannels(0)			
		if actionID in MOVEMENT_RIGHT or buttonID in MOVEMENT_RIGHT:
			self.moveFocus(1)
			#self.updateTimeBars(+1)
			#self.updateChannels(0)			
			
		self.ready = True

	###################################################################################################################
	def updateTimeBars(self, command):
		# debug("--> updateTimeBars() command=[%s]" %(command))

		if command > 0:
			interval = command * self.settings.EPG_SCROLL_INT
			tNew = self.epgStartTime + timedelta(minutes=interval) + timedelta(minutes=self.settings.EPG_DISP_INT)
			if tNew > self.EPGEndTime:
				myDlg = xbmcgui.DialogProgress()
				myDlg.create("Retrieving GBPVR data ...", "Please wait ...")
				myDlg.update(33, "Downloading ...")

				cstart = tNew.strftime("%Y-%m-%dT%H:%M:00")
				tNew = tNew + timedelta(hours=self.settings.EPG_RETR_INT)
				self.EPGEndTime = tNew
				cend = tNew.strftime("%Y-%m-%dT%H:%M:00")
				if self.gbpvr.AreYouThere(self.settings.usewol(), self.settings.GBPVR_MAC, self.settings.GBPVR_BROADCAST):
                                        tempData = self.gbpvr.getGuideInfo(self.settings.GBPVR_USER, self.settings.GBPVR_PW, cstart, cend)
                                else:
                                        return
				# Combine tempdata and epgdata
				# Todo: Handle "empty" chsnnels.... !! Need to rewrite and check for channel oid !!
				for i, a in enumerate(self.epgData):
                                        # Find epgData channel-oid in tempData..
                                        thePos = -1
                                        for j, b in enumerate(tempData):
                                                if b['oid'] == a['oid']:
                                                        thePos = j
                                        if thePos > -1:
                                                if len(tempData[thePos]['progs']) > 0:
                                                    if a['progs'][len(a['progs'])-1]['oid'] == tempData[thePos]['progs'][0]['oid']:
                                                            a['progs'] = a['progs'] + tempData[thePos]['progs'][1:]
                                                    else:
                                                            a['progs'] = a['progs'] + tempData[thePos]['progs']
				myDlg.update(100, "Complete")
				myDlg.close()
			self.epgStartTime = self.epgStartTime + timedelta(minutes=interval)
				
		elif command < 0:
			interval = command * self.settings.EPG_SCROLL_INT
			self.epgStartTime = self.epgStartTime + timedelta(minutes=interval)
			if self.epgStartTime < self.initDate:
				# Todo: Make nicer....
				self.updateTimeBars(0)
		else:
			self.epgStartTime = self.initDate

		self.epgTimerBars[0].setLabel(self.epgStartTime.strftime("%A, %B %d") )
		tempdate = self.epgStartTime
		for i in range (1, self.TimeIntervals):
			self.epgTimerBars[i].setLabel(tempdate.strftime("%H:%M") )
			tempdate = tempdate + timedelta(minutes=self.settings.EPG_SCROLL_INT)

		posx = self.getPosFromTime(datetime.now())
		if (posx > self.epgProgsX):
			self.nowTimeCI.setPosition(posx, self.epgY)
		else:	
			self.nowTimeCI.setPosition(-5, self.epgY)

		# debug("<-- updateTimeBars() command=[%s]" %(command))

	###################################################################################################################
	# Get initial time of epg. Depends on current time and interval
	def getPosFromTime(self, date):
		if date < self.epgStartTime:
			return self.epgProgsX
                interval = self.settings.EPG_SCROLL_INT + self.settings.EPG_DISP_INT
                tNew = self.epgStartTime + timedelta(minutes=interval)
		if date > tNew:
                    return self.epgProgsX + self.epgProgsW + 100
		if date.strftime("%Y-%m-%dT%H:%M:00") == tNew.strftime("%Y-%m-%dT%H:%M:00"):
                    return self.epgProgsX + self.epgProgsW
		delta = date - self.epgStartTime
		retpos = self.epgProgsX + int( (delta.seconds/60) * self.epgPixelsPerMin)
		return retpos

	###################################################################################################################
	# Get initial time of epg. Depends on current time and interval
	def getStartTime(self):
		nowdate = datetime.now()
		diff = int( (nowdate.minute -1) / self.settings.EPG_SCROLL_INT)

		diffmin = diff * self.settings.EPG_SCROLL_INT

		nowdate = nowdate - timedelta(minutes=nowdate.minute, seconds=nowdate.second)
		retdate = nowdate + timedelta(minutes=diffmin)

		return retdate			

	###################################################################################################################
	# Create a row of programs (for one channel)
	def createChannel(self, nRow, nPosY, nEpgPos, programmeList):
		try:
			for ctrl in self.epgButtons[nRow]:
				self.removeControl(ctrl)
		except: pass

		self.epgButtons[nRow] = []

		# Find 1'st program to display.... (where stoptime > epgstarttime)
		nPosX = self.epgProgsX
		nMaxX = self.epgProgsX + self.epgProgsW
		nofocusFile = os.path.join (DIR_PIC, "LightBlue")
		focusFile = os.path.join (DIR_PIC, "DarkBlue")
		nofocusRecFile = os.path.join (DIR_PIC, "LightRed")
		focusRecFile = os.path.join (DIR_PIC, "DarkRed")
		font=FONT14
		textXOffset=24
		textColor="0xFFFFFFFF"

		for i, programme in enumerate(programmeList):
			if programme['end'] < self.epgStartTime:
				continue
			# Calculate end-time...
			nRightX = self.getPosFromTime(programme['end'])
			if nRightX > nMaxX:
				# Right-side reached.... stop it.....
				theWidth = int(nMaxX - nPosX)
				theText = programme['title'].encode('latin-1')
				theText = truncate(theWidth -30, theText, font, 0)
				if programme['start'] < self.epgStartTime:
                                    theFile = "_lr.png"
                                else:
                                    theFile = "_r.png"
				if programme['rec']:
                                    theFFile = focusRecFile + theFile
                                    theNFile = nofocusRecFile + theFile
				else:
                                    theFFile = focusFile + theFile
                                    theNFile = nofocusFile + theFile
                                ctrl = xbmcgui.ControlButton(int(nPosX), int(nPosY), theWidth, self.epgRowH, \
                                                        theText, theFFile, theNFile, font=font, \
                                                        textColor=textColor, \
                                                        alignment=XBFONT_CENTER_Y|XBFONT_TRUNCATED)
				self.addControl(ctrl)
				self.epgTagData[ctrl.getId()] = [programme['oid'], programme['subtitle'], programme['desc'], programme['title'], nEpgPos, i]
				self.epgButtons[nRow].append(ctrl)
				break;
			# Put it in....
			#if nRightX == nMaxX:
                        #theWidth = int(nMaxX - nPosX)
                        #else:
                        theWidth = int(nRightX - nPosX)
			theText = programme['title'].encode('latin-1')
			theText = truncate(theWidth -30, theText, font, 0)
			if programme['start'] < self.epgStartTime:
                            theFile = "_l.png"
			else:
                            theFile = ".png"
			if programme['rec']:
                            theFFile = focusRecFile + theFile
                            theNFile = nofocusRecFile + theFile
			else:
                            theFFile = focusFile + theFile
                            theNFile = nofocusFile + theFile
                        ctrl = xbmcgui.ControlButton(int(nPosX), int(nPosY), theWidth, self.epgRowH, \
                                                        theText, theFFile, theNFile, font=font, \
                                                        textColor=textColor, \
                                                        alignment=XBFONT_CENTER_Y|XBFONT_TRUNCATED)
			self.addControl(ctrl)
			self.epgTagData[ctrl.getId()] = [programme['oid'], programme['subtitle'], programme['desc'], programme['title'], nEpgPos, i]
			self.epgButtons[nRow].append(ctrl)
			nPosX = nRightX + self.epgColGap
			if nRightX == nMaxX:
                            "Samed you know"
                            break;

	###################################################################################################################
	# Delete a row of programs (for one channel)
	def deleteChannel(self, nRow):
		try:
			for ctrl in self.epgButtons[nRow]:
				self.removeControl(ctrl)
			if nRow == 0:
				nInsPos = 7
			else:
				nInsPos = 0
			del self.epgButtons[nRow]
			self.epgButtons.insert(nInsPos, [])
		except: 
			handleException()
			debug("Error in deleting channel")
			pass


	###################################################################################################################
	# divide rows + gap into space available
	def getMaxDisplayChannels(self):
		count = int(self.epgProgsH / self.epgRowFullH)
		# debug("getMaxDisplayChannels() (%s / %s) = count=%s" % (self.epgProgsH, self.epgRowFullH, count))
		return count

		
def truncate(maxWidth, text, font, indicator, rez = 6 ):
	rezAdjust = {0 : 2.65, 1 : 1.77}
	fonts = {'font10': 9, 'font11':9, 'font12':10, 'font13':11, 'font14':12, 'font16':13, 'font18': 13, \
		  'special10':9, 'special11':9, 'special12':11, 'special13':12, 'special14':12, 'special16':13, 'special18':13}

	# print "FontAttr() orig maxWidth=%s %s %s %s" % (maxWidth, font, rez, text)
	try:
		maxWidth *= rezAdjust[rez]
	except: pass
	try:
		fontW =  fonts[font.lower()]
	except:
		fontW = 11
	shortFontW = 8

	if indicator < 0:
		mytext = "< " + text
	else:
		mytext = text

	# print "The text is now really: " + mytext
	for i in range(len(mytext), 0, -1):
		if indicator > 0:
			newText = mytext[:i] + " >"
		else:
			newText = mytext[:i]
		shortChCount = newText.count('i')+ newText.count('l') + newText.count('t') + newText.count(' ') + \
					   newText.count('r')
		otherChCount = len(newText) - shortChCount
		strW = (otherChCount * fontW) + (shortChCount * shortFontW)
		if strW <= maxWidth:
			# print "FontAttr() %s %s maxWidth=%s  strW=%s  shortChCount=%s otherChCount=%s" % (fontW, newText, maxWidth, strW, shortChCount,otherChCount)
			break

	return newText

#################################################################################################################
def handleException(txt=''):
	try:
		title = "EXCEPTION: " + txt
		e=sys.exc_info()
		list = traceback.format_exception(e[0],e[1],e[2],3)
		text = ''
		for l in list:
			text += l
		messageOK(title, text)
	except: pass

#########################
def getFilesInpath(path):
	debug("--> getFilesInPath")
	try:
		files = {}
		fileList = os.listdir(path)
		for fname in fileList:
			name = os.path.splitext(fname)[0]
			files[name] = os.path.join( path , fname )
	except:
		handleException("Error getting files!")

	return files	
	debug("<-- getFilesInPath")

######################################################################################    
# BEGIN !
######################################################################################
def info(object, spacing=10, collapse=1):
    """Print methods and doc strings.
    
    Takes module, class, list, dictionary, or string."""
    methodList = [method for method in dir(object) if callable(getattr(object, method))]
    processFunc = collapse and (lambda s: " ".join(s.split())) or (lambda s: s)
    print "\n".join(["%s %s" %
                      (method.ljust(spacing),
                       processFunc(str(getattr(object, method).__doc__)))
                     for method in methodList])

try:
	# start script main
	#todo figure out what this is
	debug("--> Home Directory is: " + DIR_HOME)
	myEPG = myGBPVR("script-myGBPVR-main.xml", DIR_HOME, "Default")
	if myEPG.ready:
		myEPG.doModal()
	del myEPG
except:
	handleException()
debug("exiting script: " + __scriptname__)
moduleList = ['mytvLib', 'bbbLib', 'bbbGUILib','smbLib', 'IMDbWin', 'IMDbLib','AlarmClock','FavShows','myGBPVRGlobals.saveProgramme','myGBPVRGlobals.datasource','tv.com','myGBPVRGlobals.mytvFavShows','wol']
for m in moduleList:
	try:
		del sys.modules[m]
		xbmc.output(__scriptname__ + " del module=%s" % m)
	except: pass

# remove other globals
try:
	del dialogProgress
except: pass

