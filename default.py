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
    __language__ = Addon('script.xbmc.x-newa').getLocalizedString
    print DIR_HOME
    #sys.path.append(os.path.join(DIR_HOME, 'resources', 'src'))
    #sys.path.append(os.path.join(DIR_HOME, 'resources', 'lib'))
    sys.path.insert(0, os.path.join(DIR_HOME, 'resources', 'lib'))
    sys.path.insert(0, os.path.join(DIR_HOME, 'resources', 'src'))
    print sys.path
    from nextpvr.home import HomeWindow
    from nextpvr.emulate import EmulateWindow
    from XNEWAGlobals import *
    from XNEWA_Connect import XNEWA_Connect
    from XNEWA_Settings import XNEWA_Settings
    from fix_utf8 import smartUTF8

    try:
        # start script main
        my_settings = XNEWA_Settings()
        my_xnewa = XNEWA_Connect(settings=my_settings)
        if my_xnewa.offline == False:
            DIR_HOME = WHERE_AM_I
            debug("--> Home Directory is: " + DIR_HOME)
            if my_settings.XNEWA_WEBCLIENT == False:
                if len(sys.argv) > 1:
                    xbmc.log("script parameters: %s" % sys.argv)
                    my_xnewa.GetNextPVRInfo(my_settings.NextPVR_USER, my_settings.NextPVR_PW)
                    if sys.argv[1] == "upcoming":
                        from nextpvr.upcoming import UpcomingRecordingsWindow
                        ur = UpcomingRecordingsWindow('nextpvr_upcoming.xml', WHERE_AM_I,my_settings.XNEWA_SKIN, settings=my_settings, xnewa=my_xnewa)
                        ur.doModal()
                    elif sys.argv[1] == "webclient":
                        ew = EmulateWindow("nextpvr_emulate.xml", WHERE_AM_I,my_settings.XNEWA_SKIN, settings=my_settings, xnewa=my_xnewa)
                        ew.doModal()
                    elif sys.argv[1] == "schedules":
                        from nextpvr.schedules import SchedulesWindow
                        sw = SchedulesWindow('nextpvr_schedules.xml', WHERE_AM_I,my_settings.XNEWA_SKIN, settings=my_settings, xnewa=my_xnewa)
                        sw.doModal()                        
                    elif sys.argv[1] == "epg":
                        from nextpvr.epg import EpgWindow
                        ew = EpgWindow('nextpvr_epg.xml', WHERE_AM_I,my_settings.XNEWA_SKIN, settings=my_settings, xnewa=my_xnewa)
                        ew.doModal()                        
                    elif sys.argv[1] == "recordings":
                        from nextpvr.recent import RecentRecordingsWindow
                        rw = RecentRecordingsWindow('nextpvr_recent.xml', WHERE_AM_I,my_settings.XNEWA_SKIN, settings=my_settings, xnewa=my_xnewa)
                        rw.doModal()                        
                    else:
                        HomeWindow('nextpvr_home.xml', WHERE_AM_I, settings=my_settings, xnewa=my_xnewa).doModal()
                else:
                    HomeWindow('nextpvr_home.xml', WHERE_AM_I,my_settings.XNEWA_SKIN, settings=my_settings, xnewa=my_xnewa).doModal()
            else:
                ew = EmulateWindow("nextpvr_emulate.xml", WHERE_AM_I,my_settings.XNEWA_SKIN, settings=my_settings, xnewa=my_xnewa)
                ew.doModal()
        else:
            import xbmcgui
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('%s' % smartUTF8(__language__(30100)), '%s \n%s' % (smartUTF8(__language__(30101)), my_xnewa.ip))
    except:
        debug("exiting script: " + __scriptname__)
        handleException()

    debug("exiting script: " + __scriptname__)
    
    # remove other globals
    try:
        del dialogProgress
    except: pass
