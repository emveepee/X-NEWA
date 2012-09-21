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

from XNEWAGlobals import *
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

	self.nextpvr_ip = self.getControl(201)
	self.nextpvr_port = self.getControl(202)
	self.nextpvr_user = self.getControl(203)
	self.nextpvr_pw = self.getControl(204)
	self.nextpvr_usewol  = self.getControl(205)
	self.nextpvr_mac = self.getControl(206)
	self.nextpvr_broadcast = self.getControl(207)
	self.nextpvr_stream = self.getControl(215)

	self.epgscrollint = self.getControl(210)
	self.epgdispint = self.getControl(211)
	self.epgretrint = self.getControl(212)
	self.epgrowh = self.getControl(213)
	self.epgGroup = self.getControl(214)
	
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
	elif self.nextpvr_ip == source:
            self._getText(self.nextpvr_ip, "NextPVR_HOST")	
	elif self.nextpvr_port == source:
            self._getText(self.nextpvr_port, "NextPVR_PORT")	
	elif self.nextpvr_user == source:
            self._getText(self.nextpvr_user, "NextPVR_USER")	
	elif self.nextpvr_pw == source:
            self._getText(self.nextpvr_pw, "NextPVR_PW")	
	elif self.nextpvr_pw == source:
            self._getText(self.nextpvr_pw, "NextPVR_PW")	
	elif self.nextpvr_usewol == source:
            self._getYN(self.nextpvr_usewol, "NextPVR_USEWOL")	
	elif self.nextpvr_mac == source:
            self._getText(self.nextpvr_mac, "NextPVR_MAC")
	elif self.nextpvr_broadcast == source:
            self._getText(self.nextpvr_broadcast, "NextPVR_BROADCAST")
	elif self.nextpvr_stream == source:
		choices = ['Native', 'VLC', 'Direct']
		setting =  xbmcgui.Dialog().select("Streaming Option", choices)
		self.settings.set("NextPVR_STREAM", choices[setting])
		self.nextpvr_stream.setLabel(self.nextpvr_stream.getLabel(), label2=choices[setting])
			#self.nextpvr_broadcast, "NextPVR_STREAM")
	elif self.epgscrollint == source:
            self._getText(self.epgscrollint, "EPG_SCROLL_INT")	
	elif self.epgdispint == source:
            self._getText(self.epgdispint, "EPG_DISP_INT")	
	elif self.epgretrint == source:
            self._getText(self.epgretrint, "EPG_RETR_INT")	
	elif self.epgrowh == source:
            self._getText(self.epgrowh, "EPG_ROW_HEIGHT")	
	elif self.epgGroup == source:
            self._getText(self.epgGroup, "EPG_GROUP")	

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
		self.nextpvr_ip.setLabel( "NextPVR IP Address:", label2=self.settings.NextPVR_HOST )
		self.nextpvr_port.setLabel( "NextPVR Port Number:", label2=str(self.settings.NextPVR_PORT) )
		self.nextpvr_user.setLabel( "NextPVR Userid:", label2=self.settings.NextPVR_USER )
		self.nextpvr_pw.setLabel( "NextPVR Password:", label2=self.settings.NextPVR_PW )
		self.nextpvr_usewol.setLabel( "Use Wake-On-Lan:", label2=self.settings.NextPVR_USEWOL )
		self.nextpvr_mac.setLabel( "NextPVR MAC Address:", label2=self.settings.NextPVR_MAC )
		self.nextpvr_broadcast.setLabel( "Wake-On-Lan Broadcast Address:", label2=self.settings.NextPVR_BROADCAST )
		self.nextpvr_stream.setLabel( "Streaming Format:", label2=self.settings.NextPVR_STREAM )
		self.epgscrollint.setLabel( "Scroll Interval (min.):", label2=str(self.settings.EPG_SCROLL_INT) )
		self.epgdispint.setLabel( "Display Interval (min.):", label2=str(self.settings.EPG_DISP_INT) )
		self.epgretrint.setLabel( "Retrieve Interval (hrs.):", label2=str(self.settings.EPG_RETR_INT) )
		self.epgrowh.setLabel( "Row Height (px):", label2=str(self.settings.EPG_ROW_HEIGHT) )
		self.epgGroup.setLabel( "Channel Group", label2=str(self.settings.EPG_GROUP) )
	except:
		handleException()
	try:
		xbmcgui.WindowXML.setFocus(self, self.nextpvr_ip)
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
