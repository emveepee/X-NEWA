#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from builtins import map
from builtins import object
import xbmc
try:
    import json
except ImportError:
    import simplejson as json

class XBMCJSON(object):

    def __init__(self):
        self.version = '2.0'

    def __call__(self, kwargs):
        method = '.'.join(map(str, self.n))
        self.n = []
        return XBMCJSON.__dict__['Request'](self, method, kwargs)

    def __getattr__(self,name):
        if 'n' not in self.__dict__:
            self.n=[]
        self.n.append(name)
        return self

    def Request(self, method, kwargs):
        data = {}
        data ['method'] = method
        data ['params'] = kwargs
        data ['jsonrpc'] = self.version
        data ['id'] = 1
        data = json.JSONEncoder().encode(data)
        response = json.loads(xbmc.executeJSONRPC(data))
        return response
