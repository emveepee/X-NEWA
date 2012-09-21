# global vars across all modules

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
ACTION_SCROLL_UP		= 5		# trigger up
ACTION_SCROLL_DOWN		= 6		# trigger down
ACTION_A	            = 7     # A
ACTION_HIGHLIGHT_ITEM	= 8		#
ACTION_B	            = 9     # B
ACTION_BACK	            = 10	# back btn
ACTION_REMOTE_INFO		= 11	# info on remote
ACTION_REMOTE_PAUSE		= 12	# remote
ACTION_REMOTE_STOP		= 13	# remote
ACTION_REMOTE_NEXT_ITEM	= 14	# remote Skip Next
ACTION_REMOTE_PREV_ITEM	= 15	# remote Skip Previous
ACTION_X 	            = 18    # X
ACTION_Y 	            = 34	# Y

ACTION_MOUSE_RIGHT_CLICK     = 101

ACTION_LEFT_TRIGGER		= 111	# trigger left
ACTION_RIGHT_TRIGGER	= 112	# trigger right
ACTION_WHITE	        = 117	# white button
ACTION_LEFT_STICK       = 85   # left stick clicked in
ACTION_RIGHT_STICK      = 122   # right stick clicked in
ACTION_RIGHT_STICK_UP	= 88
ACTION_RIGHT_STICK_DOWN	= 89
ACTION_RIGHT_STICK_RIGHT= 124
ACTION_RIGHT_STICK_LEFT	= 125
ACTION_REMOTE_RECORD	= 2010  # record button on remote - assigned in keymap.xml

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
REMOTE_BACK		= 216

KEYBOARD_LEFT          = 61477 
KEYBOARD_UP            = 61478 
KEYBOARD_RIGHT         = 61479 
KEYBOARD_DOWN          = 61480
KEYBOARD_PLUS          = 61627 
KEYBOARD_PG_UP         = 61473 
KEYBOARD_PG_DOWN        = 61474
KEYBOARD_INSERT         = 61485
KEYBOARD_X              = 61528
KEYBOARD_A              = 61505
KEYBOARD_B              = 61506
KEYBOARD_Y              = 61529
KEYBOARD_NUM_PLUS       = 61547
KEYBOARD_NUM_MINUS      = 61549
KEYBOARD_ESC            = 61467
KEYBOARD_RETURN         = 61453
KEYBOARD_HOME           = 61476
KEYBOARD_DEL_BACK       = 61448


# ACTION CODE GROUPS
CLICK_A = ( ACTION_A, PAD_A, KEYBOARD_A, KEYBOARD_RETURN, )
CLICK_B = ( ACTION_B, PAD_B, KEYBOARD_B, )
CLICK_X = ( ACTION_X, PAD_X, KEYBOARD_X, ACTION_REMOTE_STOP, )
CLICK_Y = ( ACTION_Y, PAD_Y, KEYBOARD_Y, )
SELECT_ITEM = CLICK_A
EXIT_SCRIPT = ( ACTION_BACK, PAD_BACK, REMOTE_BACK, KEYBOARD_ESC, )
CANCEL_DIALOG = CLICK_B
CONTEXT_MENU = ( ACTION_WHITE, PAD_WHITE, ACTION_REMOTE_INFO, REMOTE_INFO, KEYBOARD_HOME, ACTION_MOUSE_RIGHT_CLICK, )
LEFT_STICK_CLICK = (ACTION_LEFT_STICK, PAD_LEFT_STICK, )
RIGHT_STICK_CLICK = (ACTION_RIGHT_STICK, PAD_RIGHT_STICK, )
MOVEMENT_DPAD = ( ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP, ACTION_MOVE_DOWN, )
MOVEMENT_RIGHT_STICK = (PAD_RIGHT_STICK_UP, PAD_RIGHT_STICK_DOWN, PAD_RIGHT_STICK_LEFT, PAD_RIGHT_STICK_RIGHT, ACTION_RIGHT_STICK_UP,ACTION_RIGHT_STICK_DOWN,ACTION_RIGHT_STICK_LEFT,ACTION_RIGHT_STICK_RIGHT, )
MOVEMENT_LEFT_STICK = (PAD_LEFT_STICK_UP, PAD_LEFT_STICK_DOWN, PAD_LEFT_STICK_LEFT, PAD_LEFT_STICK_RIGHT, )
MOVEMENT_STICKS = MOVEMENT_RIGHT_STICK + MOVEMENT_LEFT_STICK
MOVEMENT_SCROLL_UP = ( ACTION_LEFT_TRIGGER, PAD_LEFT_ANALOG_TRIGGER, ACTION_SCROLL_UP, KEYBOARD_PG_UP, PAD_LEFT_TRIGGER, ACTION_REMOTE_PREV_ITEM, )
MOVEMENT_SCROLL_DOWN = ( ACTION_RIGHT_TRIGGER, PAD_RIGHT_ANALOG_TRIGGER, ACTION_SCROLL_DOWN, KEYBOARD_PG_DOWN, PAD_RIGHT_TRIGGER, ACTION_REMOTE_NEXT_ITEM, )
MOVEMENT_SCROLL = MOVEMENT_SCROLL_UP + MOVEMENT_SCROLL_DOWN
MOVEMENT_KEYBOARD = ( KEYBOARD_LEFT, KEYBOARD_UP, KEYBOARD_RIGHT, KEYBOARD_DOWN, KEYBOARD_PG_UP, KEYBOARD_PG_DOWN, )
MOVEMENT_REMOTE = ( REMOTE_LEFT, REMOTE_RIGHT, REMOTE_UP, REMOTE_DOWN, ACTION_REMOTE_NEXT_ITEM, ACTION_REMOTE_PREV_ITEM, )
MOVEMENT_UP = ( ACTION_MOVE_UP, PAD_LEFT_STICK_UP, PAD_RIGHT_STICK_UP, PAD_DPAD_UP, KEYBOARD_UP, REMOTE_UP, ACTION_RIGHT_STICK_UP,)
MOVEMENT_DOWN = ( ACTION_MOVE_DOWN, PAD_LEFT_STICK_DOWN,PAD_RIGHT_STICK_DOWN, PAD_DPAD_DOWN, KEYBOARD_DOWN, REMOTE_DOWN, ACTION_RIGHT_STICK_DOWN,)
MOVEMENT_LEFT = ( ACTION_MOVE_LEFT, PAD_LEFT_STICK_LEFT, PAD_RIGHT_STICK_LEFT,PAD_DPAD_LEFT, KEYBOARD_LEFT, REMOTE_LEFT, ACTION_RIGHT_STICK_LEFT,)
MOVEMENT_RIGHT = (  ACTION_MOVE_RIGHT, PAD_LEFT_STICK_RIGHT, PAD_RIGHT_STICK_RIGHT, PAD_DPAD_RIGHT, KEYBOARD_RIGHT, REMOTE_RIGHT, ACTION_RIGHT_STICK_RIGHT, )
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

WHERE_AM_I = Addon('script.xbmc.x-newa').getAddonInfo('path')

# Script doc constants
__scriptname__ = "XNEWAGlobals"
__version__ = '2.0.0'
__author__ = 'emveepee'
__original_author__ = 'Ton van der Poel'
__date__ = '2012-09-02'

import xbmc
xbmc.log(__scriptname__ + " Version: " + __version__ + " Date: " + __date__)

#################################################################################################################
def debug( value ):
	global debugIndentLvl
	if (DEBUG and value):
		try:
			if value[0] == ">": debugIndentLvl += 2
			pad = rjust("", debugIndentLvl)
			print pad + str(value)
			if value[0] == "<": debugIndentLvl -= 2
		except:
			try:
				print value
			except:
				print "Debug() Bad chars in string"


#################################################################################################################
def handleException(txt=''):
	try:
		title = "EXCEPTION: " + txt
		e=sys.exc_info()
		list = traceback.format_exception(e[0],e[1],e[2],3)
		text = ''
		for l in list:
			text += l
		print title + ": " + text
		messageOK(title, text)
	except: pass
