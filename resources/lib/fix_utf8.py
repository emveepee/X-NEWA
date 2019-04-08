#v.0.1.1

from builtins import str
try:
    basestring
except NameError:
    basestring = str  #For Python 3
import unicodedata

from kodi_six.utils import py2_encode, py2_decode

def smartUnicode(s):
    if not s:
        return ''
    try:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = str(s)
            else:
                s = str(str(s), 'UTF-8')
        elif not isinstance(s, str):
            s = str(s, 'UTF-8')
    except:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = str(s)
            else:
                s = str(str(s), 'ISO-8859-1')
        elif not isinstance(s, str):
            s = str(s, 'ISO-8859-1')
    return s

def smartUTF8(s):
    return  py2_decode(smartUnicode(s))
