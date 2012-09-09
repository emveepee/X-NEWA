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
	sys.path.append(os.path.join(os.getcwd(), 'resources', 'src'))
	sys.path.append(os.path.join(os.getcwd(), 'resources', 'lib'))
	from myGBPVRGlobals import *
	from gbpvr.home import HomeWindow
	try:
		# start script main
		DIR_HOME = os.getcwd().replace( ";", "" )
		debug("--> Home Directory is: " + DIR_HOME)
		HomeWindow('gbpvr_home.xml', os.getcwd()).doModal()
	except:
		debug("exiting script: " + __scriptname__)
		handleException()

	debug("exiting script: " + __scriptname__)

	# remove other globals
	try:
		del dialogProgress
	except: pass
