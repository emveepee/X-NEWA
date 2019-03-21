#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import xbmc
try:
    import json
except ImportError:
    import simplejson as json
import urllib2, base64

class XBMCJSON:

    def __init__(self):
        self.version = '2.0'

    def __call__(self, kwargs):
        method = '.'.join(map(str, self.n))
        self.n = []
        return XBMCJSON.__dict__['Request'](self, method, kwargs)
 
    def __getattr__(self,name):
        if not self.__dict__.has_key('n'):
            self.n=[]
        self.n.append(name)
        return self

    def Request(self, method, kwargs):
        data = {}
        print method
        print kwargs
        data ['method'] = method
        data ['params'] = kwargs
        data ['jsonrpc'] = self.version
        data ['id'] = 1
        data = json.JSONEncoder().encode(data)
        response = json.loads(xbmc.executeJSONRPC(data))
        return response

