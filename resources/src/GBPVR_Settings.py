######################################################################################################
# Class for storing specific settings
#
# Usage: Instantiate a new class and use properties to retrieve global settings...
#          I.e. mysettings= gbpvr_settings()
#        Then, use properties
#          I.e. print mysettings.GBPVR_HOST
#               print mysettings.GBPVR_PORT
######################################################################################################

import os
import ConfigParser
from myGBPVRGlobals import *
import traceback
import sys
from xbmcaddon import Addon
# Core defines

class GBPVR_Settings:

  INI_PATH = 'x-newa.ini'

  # Instantiation
  def __init__(self):
	self.configpath = os.path.join(Addon('script.xbmc.x-newa').getAddonInfo('path'), self.INI_PATH)

	self.config = config = ConfigParser.ConfigParser({'host':'127.0.0.1', 'port':'8866', 'userid':'admin', 'pw':'password',  'usewol':'No', 'mac':'00:00:00:00:00:00', 'broadcast':'255.255.255.255','scroll_int':'15', 'disp_int':'60', 'retr_int':'2', 'row_h':'75', 'group':'' })
	try:
		self.config.read(self.configpath)
	except:
		handleException()
		pass
	if (not config.has_section("NextPVR")):
		config.add_section("NextPVR")
	if (not config.has_section("EPG")):
		config.add_section("EPG")

	try:
		self.GBPVR_HOST = config.get("NextPVR", "host")
		self.GBPVR_PORT = config.getint("NextPVR", "port")
		self.GBPVR_USER = config.get("NextPVR", "userid")
		self.GBPVR_PW = config.get("NextPVR", "pw")
		self.GBPVR_USEWOL = config.get("NextPVR", "usewol")
		self.GBPVR_MAC = config.get("NextPVR", "mac")
		self.GBPVR_BROADCAST = config.get("NextPVR", "broadcast")
		self.EPG_SCROLL_INT = config.getint("EPG", "scroll_int")
		self.EPG_DISP_INT = config.getint("EPG", "disp_int")
		self.EPG_RETR_INT = config.getint("EPG", "retr_int")
		self.EPG_ROW_HEIGHT = config.getint("EPG", "row_h")
		self.EPG_GROUP = config.get("EPG", "group")
	except:
		handleException()

  ######################################################################################################
  # Saving the configuration file...
  ######################################################################################################
  def save(self):
	try:
		self.config.set("NextPVR", "host", self.GBPVR_HOST)
		self.config.set("NextPVR", "port", self.GBPVR_PORT)
		self.config.set("NextPVR", "userid", self.GBPVR_USER)
		self.config.set("NextPVR", "pw", self.GBPVR_PW)
		self.config.set("NextPVR", "usewol", self.GBPVR_USEWOL)
		self.config.set("NextPVR", "mac", self.GBPVR_MAC)
		self.config.set("NextPVR", "broadcast", self.GBPVR_BROADCAST)
		
		self.config.set("EPG", "scroll_int", self.EPG_SCROLL_INT)
		self.config.set("EPG", "disp_int", self.EPG_DISP_INT)
		self.config.set("EPG", "retr_int", self.EPG_RETR_INT)
		self.config.set("EPG", "row_h", self.EPG_ROW_HEIGHT)
		self.config.set("EPG", "group", self.EPG_GROUP)
		print "Trying to write to: " + self.configpath
		configfile = open(self.configpath, 'w')
		self.config.write(configfile)
		configfile.close()
		print "Written to: " + self.configpath
	except:
		handleException()
	return 

  def usewol(self):
          return self.GBPVR_USEWOL.lower() == "yes"

  ######################################################################################################
  # Setting one setting....
  ######################################################################################################
  def set(self, key, val):
	if key =="GBPVR_HOST":
		self.GBPVR_HOST = val
	elif key == "GBPVR_PORT":
		self.GBPVR_PORT = int(val)
	elif key == "GBPVR_USER":
		self.GBPVR_USER = val
	elif key == "GBPVR_PW":
		self.GBPVR_PW = val
	elif key == "GBPVR_USEWOL":
		self.GBPVR_USEWOL = val
	elif key == "GBPVR_MAC":
		self.GBPVR_MAC = val
	elif key == "GBPVR_BROADCAST":
		self.GBPVR_BROADCAST = val
	elif key == "EPG_SCROLL_INT":
		self.EPG_SCROLL_INT = int(val)
	elif key == "EPG_DISP_INT":
		self.EPG_DISP_INT = int(val)
	elif key == "EPG_RETR_INT":
		self.EPG_RETR_INT = int(val)
	elif key == "EPG_ROW_HEIGHT":
		self.EPG_ROW_HEIGHT = int(val)
	elif key == "EPG_GROUP":
		self.EPG_GROUP = val
