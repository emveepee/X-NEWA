#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2009 analogue@yahoo.com
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import os
import xbmcgui

from myGBPVRGlobals import *
# =============================================================================            
class settingsDialog(xbmcgui.WindowXMLDialog):
    """
    Show details of show, recording and recurring recording
    """
        
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

	# Get settings from arguments...
        self.settings = kwargs['settings']

        self.win = None        
        self.shouldRefresh = False
        
    def onInit(self):
        self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())

	self.gbpvrip = self.getControl(201)
	self.gbpvrport = self.getControl(202)
	self.gbpvruser = self.getControl(203)
	self.gbpvrpw = self.getControl(204)
	self.gbpvrusewol  = self.getControl(205)
	self.gbpvrmac = self.getControl(206)
	self.gbpvrbroadcast = self.getControl(207)
	
	self.epgscrollint = self.getControl(210)
	self.epgdispint = self.getControl(211)
	self.epgretrint = self.getControl(212)
	self.epgrowh = self.getControl(213)
	
        self.saveButton = self.getControl(250)
        self.cancelButton = self.getControl(253)
	self._updateView()

    def onFocus(self, controlId):
        pass
        
    def onAction(self, action):
        if action.getId() in (EXIT_SCRIPT):
            self.close() 

    def onClick(self, controlId):
        source = self.getControl(controlId)
            
        if self.cancelButton == source:
            self.close()
        elif self.saveButton == source:
            self.settings.save()
            self.close()
	elif self.gbpvrip == source:
            self._getText(self.gbpvrip, "GBPVR_HOST")	
	elif self.gbpvrport == source:
            self._getText(self.gbpvrport, "GBPVR_PORT")	
	elif self.gbpvruser == source:
            self._getText(self.gbpvruser, "GBPVR_USER")	
	elif self.gbpvrpw == source:
            self._getText(self.gbpvrpw, "GBPVR_PW")	
	elif self.gbpvrpw == source:
            self._getText(self.gbpvrpw, "GBPVR_PW")	
	elif self.gbpvrusewol == source:
            self._getYN(self.gbpvrusewol, "GBPVR_USEWOL")	
	elif self.gbpvrmac == source:
            self._getText(self.gbpvrmac, "GBPVR_MAC")
	elif self.gbpvrbroadcast == source:
            self._getText(self.gbpvrbroadcast, "GBPVR_BROADCAST")
	elif self.epgscrollint == source:
            self._getText(self.epgscrollint, "EPG_SCROLL_INT")	
	elif self.epgdispint == source:
            self._getText(self.epgdispint, "EPG_DISP_INT")	
	elif self.epgretrint == source:
            self._getText(self.epgretrint, "EPG_RETR_INT")	
	elif self.epgrowh == source:
            self._getText(self.epgrowh, "EPG_ROW_HEIGHT")	

    def _getText(self, ctrl, key):
	cTitle = ctrl.getLabel()
	cText = ctrl.getLabel2()
	kbd = xbmc.Keyboard(cText, cTitle)

	kbd.doModal()

	if kbd.isConfirmed():
		txt = kbd.getText()
		self.settings.set(key, txt)
		ctrl.setLabel(cTitle, label2=txt)
	
    def _getYN(self, ctrl, key):
	cTitle = ctrl.getLabel()
	theList = ["No", "Yes"]
        selected = xbmcgui.Dialog().select(cTitle, theList)
        if selected < 0:
                return
        self.settings.set(key, theList[selected])
        ctrl.setLabel(cTitle, label2=theList[selected])
        
    def _updateView(self):
        
	self.win.setProperty('busy', 'true')
	try:
		self.gbpvrip.setLabel( "GBPVR Ip Adres:", label2=self.settings.GBPVR_HOST )
		self.gbpvrport.setLabel( "GBPVR Port Number:", label2=str(self.settings.GBPVR_PORT) )
		self.gbpvruser.setLabel( "GBPVR Userid:", label2=self.settings.GBPVR_USER )
		self.gbpvrpw.setLabel( "GBPVR Password:", label2=self.settings.GBPVR_PW )
		self.gbpvrusewol.setLabel( "Use Wake-On-Lan:", label2=self.settings.GBPVR_USEWOL )
		self.gbpvrmac.setLabel( "GBPVR Mac Address:", label2=self.settings.GBPVR_MAC )
		self.gbpvrbroadcast.setLabel( "Wake-On-Lan Broadcast Address:", label2=self.settings.GBPVR_BROADCAST )
		self.epgscrollint.setLabel( "Scroll Interval (min.):", label2=str(self.settings.EPG_SCROLL_INT) )
		self.epgdispint.setLabel( "Display Interval (min.):", label2=str(self.settings.EPG_DISP_INT) )
		self.epgretrint.setLabel( "Retrieve Interval (hrs.):", label2=str(self.settings.EPG_RETR_INT) )
		self.epgrowh.setLabel( "Row Height (px):", label2=str(self.settings.EPG_ROW_HEIGHT) )
	except:
		handleException()
	try:
		xbmcgui.WindowXML.setFocus(self, self.gbpvrip)
	except:
		handleException()

	self.win.setProperty('busy', 'false')

    def _chooseFromList(self, translations, title, property, setter):
        """
        Boiler plate code that presents the user with a dialog box to select a value from a list.
        Once selected, the setter method on the Schedule is called to reflect the selection.
        
        """
        pickList = self.translator.toList(translations)
        selected = xbmcgui.Dialog().select(title, pickList)
        if selected >= 0:
            self.setWindowProperty(property, pickList[selected])
            setter(translations.keys()[selected])
            
    def _enterNumber(self, heading, current, min=None, max=None):
        """
        Prompt user to enter a valid number with optional min/max bounds.
        
        """
        value = xbmcgui.Dialog().numeric(0, heading, str(current))
        if value == str(current):
            return current
        
        result = int(value)
        
        if min is not None and result < min:
            xbmcgui.Dialog().ok('Error', 'Value must be between %d and %d' % (min, max))
            result = current
            
        if max is not None and result > max:
            xbmcgui.Dialog().ok('Error', 'Value must be between %d and %d' % (min, max))
            result = current
            
        return result             
