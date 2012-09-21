#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
	X-NEWA

	Controlling NextPVR from within XBMC.

	Originally Written By Ton van der Poel
	Updated By emveepee

	THANKS:
	To everyone who's ever helped in anyway, or if I've used code from your own scripts, MUCH APPRECIATED!


    Additional support may be found on xboxmediacenter or NextPVR forums.	
"""

__scriptname__ = "X-NEWA"
__author__     = "emveepee"
__credits__    = "bunch of ppl"

if __name__ == '__main__':
	import os, sys, xbmc
	from xbmcaddon import Addon
	DIR_HOME = Addon('script.xbmc.x-newa').getAddonInfo('path')
	print DIR_HOME
	sys.path.append(os.path.join(DIR_HOME, 'resources', 'src'))
	sys.path.append(os.path.join(DIR_HOME, 'resources', 'lib'))
	print sys.path
	from nextpvr.home import HomeWindow
	from XNEWAGlobals import *
	try:
		# start script main
		DIR_HOME = WHERE_AM_I
		debug("--> Home Directory is: " + DIR_HOME)
		HomeWindow('nextpvr_home.xml', WHERE_AM_I).doModal()
	except:
		debug("exiting script: " + __scriptname__)
		handleException()

	debug("exiting script: " + __scriptname__)

	# remove other globals
	try:
		del dialogProgress
	except: pass
