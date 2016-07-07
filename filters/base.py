# -*- coding: utf-8 -*-
"""
QGIS Server OAuth Base filter

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = 'Alessandro Pasotti'
__date__ = '05/15/2016'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.server import *
from qgis.core import *

from oauth_settings import *

# Session management: very naive cache implementation
from collections import OrderedDict
from threading import Lock

class Cache:
    def __init__(self, size=100):
        if int(size) < 1:
            raise AttributeError('size < 1 or not a number')
        self.size = size
        self.dict = OrderedDict()
        self.lock = Lock()

    def __getitem__(self, key):
        with self.lock:
            return self.dict[key]

    def __setitem__(self, key, value):
        with self.lock:
            while len(self.dict) >= self.size:
                self.dict.popitem(last=False)
            self.dict[key] = value

    def __delitem__(self, key):
        with self.lock:
            del self.dict[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class OAuthException(Exception):
    pass

class OAuthFilterBase(QgsServerFilter):

    def log(self, msg):
        QgsMessageLog.logMessage('[OAUTH2] %s' % msg)

    def get_current_url(self):
        iface = self.serverInterface()
        url = "http%s://%s" % ('s' if iface.getEnv('HTTPS') == 'on' else '', iface.getEnv('SERVER_NAME'))
        if iface.getEnv('SERVER_PORT') != '80':
            url = '%s:%s' % (url, iface.getEnv('SERVER_PORT'))
        url = '%s%s' % (url, iface.getEnv('REQUEST_URI'))
        return url

    def redirect(self, url):
        self.log('Redirecting: %s' % self.redirect_url)
        request = self.serverInterface().requestHandler()
        request.clearHeaders()
        request.setHeader('Status', '302 Found')
        request.setHeader('Location', self.redirect_url)
        request.clearBody()
        request.appendBody('Redirecting...')

    def error(self, code=401):
        request = self.serverInterface().requestHandler()
        request.clearHeaders()
        if code == 401:
            resp_code = '401 Unauthorized %s' % self.exception
            request.setHeader(' WWW-Authenticate', 'Bearer realm="QGIS Server"')
        else:
            resp_code = '500 Internal Server Error %s' % self.exception
        self.log('Sending error: %s' % self.exception)
        request.setHeader('Status', resp_code)
        request.clearBody()
        request.appendBody('401 Unauthorized: %s' % self.exception)
