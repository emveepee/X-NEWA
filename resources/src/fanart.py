######################################################################################################
# Class for loading fandata
#
# Usage: Instantiate a new class and use the helper functions to retrieve icons
#          I.e. myfanart= fanart()
#        Then, call methods on the new class
#          I.e. myfanart.getChannelIcon('Discovery Channel')
#               myfanart.getShowIcon('Mythbusters')
######################################################################################################

import os
# Core defines

class fanart:

  FANART_PATH = 'fanart'
  CHANNEL_PATH = 'Channels'
  SHOW_PATH = 'Shows'
  GENRE_PATH = 'Genres'

  # Instantiation
  def __init__(self):
	from XNEWAGlobals import *

	self.channelPath = os.path.join( WHERE_AM_I, self.FANART_PATH, self.CHANNEL_PATH)
	self.showPath = os.path.join( WHERE_AM_I, self.FANART_PATH, self.SHOW_PATH)
	self.genrePath = os.path.join( WHERE_AM_I, self.FANART_PATH, self.GENRE_PATH)
	self.channelIcons = self._getFiles(self.channelPath)
	self.showIcons = self._getFiles(self.showPath) 
	self.genreIcons = self._getFiles(self.genrePath)

  #Core Functions

  ######################################################################################################
  # Try to load a channel icon
  ######################################################################################################
  def getChannelIcon(self, name):
	return self._getIcon(name, self.channelPath, self.channelIcons)		

  ######################################################################################################
  # Try to load a show icon
  ######################################################################################################
  def getShowIcon(self, name):
	return self._getIcon(name, self.showPath, self.showIcons)

  ######################################################################################################
  # Try to load a genre icon
  ######################################################################################################
  def getGenreIcon(self, name):
	return self._getIcon(name, self.genrePath, self.genreIcons)

  #Helper Functions

  ######################################################################################################
  # Finding a file in a directory, caching the contents....
  ######################################################################################################
  def _getIcon(self, name, path, var):
	for icon in var:
		if os.path.splitext(icon)[0].lower() == name.lower():
			return os.path.join(path, icon);
		if os.path.splitext(icon)[0].lower().find(name.lower()) >= 0:
			return os.path.join(path, icon);
		if name.lower().find(os.path.splitext(icon)[0].lower()) >= 0:
			return os.path.join(path, icon);
	return None

  ######################################################################################################
  # Loading an array with contents
  ######################################################################################################
  def _getFiles(self, path):
	var = []
	for filename in os.listdir(path):
		var.append(filename)
	return var