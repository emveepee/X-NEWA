# global vars across all modules

from builtins import str
import traceback
import sys

#XNEWA Specific global vars....
#TIME_SCROLL_INTERVAL = 15 #Minutes
#TIME_DISPLAY = 60 #Minutes
#EPG_RETRIEVE_INTERVAL = 2 #Hours

#NextPVR_HOST = '127.0.0.1'
#NextPVR_WEB_PORT = 4242
#NextPVR_USER = 'ton'
#NextPVR_PW = 'ton'


# Standard xbmc stuff....
# KEYPAD CODES
ACTION_UNKNOWN			= 0
ACTION_MOVE_LEFT 	    = 1 	# Dpad
ACTION_MOVE_RIGHT	    = 2		# Dpad
ACTION_MOVE_UP		    = 3		# Dpad
ACTION_MOVE_DOWN	    = 4		# Dpad
ACTION_PAGE_UP	    	= 5		# trigger up
ACTION_PAGE_DOWN		= 6		# trigger down
ACTION_SELECT_ITEM      = 7
ACTION_HIGHLIGHT_ITEM	= 8		#
ACTION_B	            = 9     # B
ACTION_BACK	            = 10	# back btn
ACTION_INFO	            = 11	# back btn
ACTION_SHOW_GUI         = 18    # was X
ACTION_ASPECT_RATIO     = 19
ACTION_SHOW_OSD         = 24
ACTION_NEXT_SUBTITLE    = 26
ACTION_SHOW_PLAYLIST    = 33
ACTION_Y 	            = 34	# Y

ACTION_PLAYER_PLAY      = 79
ACTION_REMOTE_MENU		= 247	# menu on remote
ACTION_PAUSE    		= 12	# remote
ACTION_STOP     		= 13	# remote
ACTION_NEXT_ITEM	    = 14	# remote Skip Next

ACTION_PREV_ITEM    	= 15	# remote Skip Previous
ACTION_SMALL_STEP_BACK  = 76
ACTION_PLAYER_FORWARD	= 77	# remote Forward Previous
ACTION_QUEUE_ITEM       = 34
ACTION_PLAYER_REWIND	= 78
ACTION_CONTEXT_MENU     = 117
ACTION_FIRST_PAGE   	= 159
ACTION_RECORD       	= 170

ACTION_MOUSE_BACK           = 92
ACTION_MOUSE_LEFT_CLICK     = 100
ACTION_MOUSE_RIGHT_CLICK    = 101
ACTION_MOUSE_DOUBLE_CLICK   = 103
ACTION_WHEEL_UP             = 104
ACTION_WHEEL_DOWN           = 105
ACTION_MOUSE_MOVE           = 107

ACTION_LEFT_TRIGGER		= 111	# trigger left
ACTION_RIGHT_TRIGGER	= 112	# trigger right
ACTION_WHITE	        = 117	# white button
ACTION_LEFT_STICK       = 85   # left stick clicked in
ACTION_RIGHT_STICK      = 122   # right stick clicked in
ACTION_RIGHT_STICK_UP	= 88
ACTION_RIGHT_STICK_DOWN	= 89
ACTION_BUILT_IN_FUNCTION = 122
ACTION_RIGHT_STICK_RIGHT= 124
ACTION_RIGHT_STICK_LEFT	= 125


PAD_A                        = 256
PAD_B                        = 257
PAD_X                        = 258
PAD_Y                        = 259
PAD_BLACK                    = 260
PAD_WHITE                    = 261
PAD_LEFT_TRIGGER             = 262
PAD_RIGHT_TRIGGER            = 263
PAD_LEFT_STICK              = 264
PAD_RIGHT_STICK             = 265
PAD_RIGHT_STICK_UP          = 266 # right thumb stick directions
PAD_RIGHT_STICK_DOWN        = 267 # for defining different actions per direction
PAD_RIGHT_STICK_LEFT        = 268
PAD_RIGHT_STICK_RIGHT       = 269
PAD_DPAD_UP                  = 270
PAD_DPAD_DOWN                = 271
PAD_DPAD_LEFT                = 272
PAD_DPAD_RIGHT               = 273
PAD_START                    = 274
PAD_BACK                     = 275
PAD_LEFT_STICK              = 276
PAD_RIGHT_STICK             = 277
PAD_LEFT_ANALOG_TRIGGER      = 278
PAD_RIGHT_ANALOG_TRIGGER= 279
PAD_LEFT_STICK_UP       = 280 # left thumb stick  directions
PAD_LEFT_STICK_DOWN     = 281 # for defining different actions per direction
PAD_LEFT_STICK_LEFT     = 282
PAD_LEFT_STICK_RIGHT    = 283

REMOTE_LEFT             = 169
REMOTE_RIGHT            = 168
REMOTE_UP               = 166
REMOTE_DOWN             = 167
REMOTE_1                = 206
REMOTE_4                = 203
REMOTE_INFO             = 195


ACTION_TELETEXT_RED     = 215
ACTION_TELETEXT_GREEN   = 216
ACTION_TELETEXT_YELLOW  = 217
ACTION_TELETEXT_BLUE    = 218


REMOTE_BACK		        = 92


ACTION_GESTURE_BEGIN    = 501
ACTION_GESTURE_END      = 599
ACTION_GESTURE_NOTIFY   = 500
ACTION_GESTURE_PAN      = 504
ACTION_GESTURE_ROTATE   = 503
ACTION_GESTURE_SWIPE_DOWN = 541
ACTION_GESTURE_SWIPE_DOWN_TEN = 550
ACTION_GESTURE_SWIPE_LEFT = 511
ACTION_GESTURE_SWIPE_LEFT_TEN = 520
ACTION_GESTURE_SWIPE_RIGHT = 521
ACTION_GESTURE_SWIPE_RIGHT_TEN = 530
ACTION_GESTURE_SWIPE_UP = 531
ACTION_GESTURE_SWIPE_UP_TEN = 540
ACTION_GESTURE_ZOOM     = 502
ACTION_GESTURE_STOP     = 226

KEYBOARD_LEFT          = 61477
KEYBOARD_UP            = 61478
KEYBOARD_RIGHT         = 61479
KEYBOARD_DOWN          = 61480
KEYBOARD_PLUS          = 61627
KEYBOARD_PG_UP         = 61473
KEYBOARD_PG_DOWN        = 61474
KEYBOARD_INSERT         = 61485
KEYBOARD_BACK           = 61448
KEYBOARD_X              = 61528
KEYBOARD_A              = 61505
KEYBOARD_B              = 61506
KEYBOARD_Y              = 61529
KEYBOARD_NUM_PLUS       = 61547
KEYBOARD_NUM_MINUS      = 61549
KEYBOARD_ESC            = 61467
KEYBOARD_RETURN         = 61453
KEYBOARD_HOME           = 61576
KEYBOARD_DEL_BACK       = 61448


# ACTION CODE GROUPS
EXIT_SCRIPT = ( ACTION_BACK, PAD_BACK, REMOTE_BACK, KEYBOARD_ESC, KEYBOARD_BACK )
CONTEXT_MENU = ( ACTION_WHITE, PAD_WHITE )
INFO_MENU = ( REMOTE_INFO, REMOTE_INFO )
MOVEMENT_SCROLL_UP = ( ACTION_LEFT_TRIGGER, PAD_LEFT_ANALOG_TRIGGER, ACTION_PAGE_UP, KEYBOARD_PG_UP, PAD_LEFT_TRIGGER, ACTION_GESTURE_SWIPE_DOWN )
MOVEMENT_SCROLL_DOWN = ( ACTION_RIGHT_TRIGGER, PAD_RIGHT_ANALOG_TRIGGER, ACTION_PAGE_DOWN, KEYBOARD_PG_DOWN, PAD_RIGHT_TRIGGER, ACTION_GESTURE_SWIPE_UP)
MOVEMENT_SCROLL = MOVEMENT_SCROLL_UP + MOVEMENT_SCROLL_DOWN
MOVEMENT_KEYBOARD = ( KEYBOARD_LEFT, KEYBOARD_UP, KEYBOARD_RIGHT, KEYBOARD_DOWN, KEYBOARD_PG_UP, KEYBOARD_PG_DOWN )
MOVEMENT_REMOTE = ( REMOTE_LEFT, REMOTE_RIGHT, REMOTE_UP, REMOTE_DOWN, ACTION_NEXT_ITEM, ACTION_PREV_ITEM )
MOVEMENT_UP = ( ACTION_MOVE_UP,  ACTION_WHEEL_UP, PAD_LEFT_STICK_UP, PAD_RIGHT_STICK_UP, PAD_DPAD_UP, KEYBOARD_UP, REMOTE_UP)
MOVEMENT_DOWN = ( ACTION_MOVE_DOWN, ACTION_WHEEL_DOWN, PAD_LEFT_STICK_DOWN,PAD_RIGHT_STICK_DOWN, PAD_DPAD_DOWN, KEYBOARD_DOWN, REMOTE_DOWN)
MOVEMENT_LEFT = ( ACTION_MOVE_LEFT, PAD_LEFT_STICK_LEFT, PAD_RIGHT_STICK_LEFT,PAD_DPAD_LEFT, KEYBOARD_LEFT, REMOTE_LEFT, ACTION_RIGHT_STICK_LEFT)
MOVEMENT_RIGHT = (  ACTION_MOVE_RIGHT, PAD_LEFT_STICK_RIGHT, PAD_RIGHT_STICK_RIGHT, PAD_DPAD_RIGHT, KEYBOARD_RIGHT, REMOTE_RIGHT, ACTION_RIGHT_STICK_RIGHT)
MOVEMENT = MOVEMENT_UP + MOVEMENT_DOWN + MOVEMENT_LEFT + MOVEMENT_RIGHT + MOVEMENT_SCROLL + MOVEMENT_KEYBOARD + MOVEMENT_REMOTE

#Text Alignment
XBFONT_LEFT       = 0x00000000
XBFONT_RIGHT      = 0x00000001
XBFONT_CENTER_X   = 0x00000002
XBFONT_CENTER_Y   = 0x00000004
XBFONT_TRUNCATED  = 0x00000008

KBTYPE_ALPHA = -1
KBTYPE_NUMERIC = 0
KBTYPE_DATE = 1
KBTYPE_TIME = 2
KBTYPE_IP = 3
KBTYPE_SMB = 4      # not a real kbtype, just a common value
KBTYPE_YESNO = 5    # not a real kbtype, just a common value

# xbmc skin FONT NAMES
FONT10 = 'font10'
FONT11 = 'font11'
FONT12 = 'font12'
FONT13 = 'font13'
FONT14 = 'font14'
FONT16 = 'font16'
FONT18 = 'font18'
FONT_SPECIAL_10 = 'special10'
FONT_SPECIAL_11 = 'special11'
FONT_SPECIAL_12 = 'special12'
FONT_SPECIAL_13 = 'special13'
FONT_SPECIAL_14 = 'special14'

DEBUG = False

from xbmcaddon import Addon
import xbmc, os

__addon__        = Addon()
__addonname__    = __addon__.getAddonInfo('id')
__addonversion__ = __addon__.getAddonInfo('version')
__addonpath__    = __addon__.getAddonInfo('path')

WHERE_AM_I = __addonpath__


# Script doc constants
__scriptname__ = "knewc"
__version__ = '2.7.4'
__author__ = 'emveepee'
__original_author__ = 'Ton van der Poel'
__date__ = '2019-10-08'

XBMC_DIALOG_BUSY_OPEN = "ActivateWindow(busydialognocancel)"
XBMC_DIALOG_BUSY_CLOSE = "Dialog.Close(busydialognocancel)"

xbmc.log(__scriptname__ + " Version: " + __version__ + " Date: " + __date__)

#################################################################################################################
def debug( value ):
	global debugIndentLvl
	if (DEBUG and value):
		try:
			if value[0] == ">": debugIndentLvl += 2
			pad = rjust("", debugIndentLvl)
			xbmc.log(pad + str(value))
			if value[0] == "<": debugIndentLvl -= 2
		except:
			try:
				xbmc.log(value)
			except:
				xbmc.log("Debug() Bad chars in string")


#################################################################################################################
def handleException(txt=''):
	try:
		title = "EXCEPTION: " + txt
		e=sys.exc_info()
		list = traceback.format_exception(e[0],e[1],e[2],3)
		text = ''
		for l in list:
			text += l
		xbmc.log( title + ": " + text)
		xbmcgui.Dialog().ok(title, text)
	except: pass
