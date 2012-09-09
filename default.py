#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
	myGBPVR

	Controlling GB-PVR from within XBMC.

	Written By Ton van der Poel

	THANKS:
	To everyone who's ever helped in anyway, or if I've used code from your own scripts, MUCH APPRECIATED!


    Additional support may be found on xboxmediacenter or gbpvr forum.	
"""

__scriptname__ = "myGBPVR"
__author__     = "Ton van der Poel"
__credits__    = "bunch of ppl"
__svn_revision__ = 1558
__version__    = "[Beta SVN %d]" % __svn_revision__

if __name__ == '__main__':
	import os, sys, xbmc
	from xbmcaddon import Addon

	__settings__ = Addon(id='script.myGBPVR')

	sys.path.append(os.path.join(__settings__.getAddonInfo('path'), 'resources', 'src'))
	sys.path.append(os.path.join(__settings__.getAddonInfo('path'), 'resources', 'lib'))
 	from myGBPVRGlobals import *
	from gbpvr.home import HomeWindow
	try:
		# start script main
		DIR_HOME = __settings__.getAddonInfo('path').replace( ";", "" )
		debug("--> Home Directory is: " + DIR_HOME)
		HomeWindow('gbpvr_home.xml', __settings__.getAddonInfo('path')).doModal()
	except:
		debug("exiting script: " + __scriptname__)
		handleException()

	debug("exiting script: " + __scriptname__)

	# remove other globals
	try:
		del dialogProgress
	except: pass
