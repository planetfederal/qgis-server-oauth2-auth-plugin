# -*- coding: utf-8 -*-
"""
QGIS Server OAuth 2 Base filter

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

import urlparse
import time
import hashlib

try:
    from oauth2lib.client import Client
except ImportError:
    raise Exception("Please install the required Python packages in REQUIREMENTS.txt")

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

class OAuth2FilterBase(QgsServerFilter):
    """
    Base class for OAuth 2, standard implementations just need to
    define class properties:

    access_token_url = 'https://www.googleapis.com/oauth2/v4/token'
    authenticate_url = 'https://accounts.google.com/o/oauth2/v2/auth'

    And optionally:

    scope = 'some_scope'

    """

    # Configuration variables
    access_token_url = OAUTH2_ACCESS_TOKEN_URL
    authenticate_url = OAUTH2_AUTHENTICATE_URL

    scope = OAUTH2_SCOPE

    # Store request_token -> dicts of request_token information
    request_storage = Cache()
    # Store oauth_token -> dict of oauth token information
    token_storage = Cache()

    def log(self, msg):
        QgsMessageLog.logMessage('[OAUTH2] %s' % msg)

    def get_current_url(self):
        iface = self.serverInterface()
        url = "http%s://%s" % ('s' if iface.getEnv('HTTPS') == 'on' else '', iface.getEnv('SERVER_NAME'))
        if iface.getEnv('SERVER_PORT') != '80':
            url = '%s:%s' % (url, iface.getEnv('SERVER_PORT'))
        url = '%s%s' % (url, iface.getEnv('REQUEST_URI'))
        return url

    def get_callback_url(self):
        """Some oauth implementations might need a particular callback: overrideable"""
        return self.get_current_url()

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

    def login(self):
        try:
            request_token = self.request_storage['request_token']
        except KeyError:
            # Step 1. Get (build) an authorization code
            request_token = hashlib.md5(str(time.time())).hexdigest()
            # Step 2. Store the request token and the current URL in a session for later use.
            self.request_storage[request_token] = self.get_current_url()
        # Step 3. Redirect the user to the authentication URL.
        client = Client(OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET,  self.get_callback_url(), self.authenticate_url, self.access_token_url)
        self.redirect_url = client.get_authorization_code_uri(state=request_token)
        if self.scope is not None:
            self.redirect_url += '&scope=%s' % self.scope

    def authenticated(self, request_token, verifier_token):
        """
        Call OAuth endpoint to verify the request tokens.
        Return the access_token and the real (original) callback_url
        Raise OAuthException on error.
        """
        # Check the verifier_token (state)
        try:
            real_callback_url = self.request_storage[request_token]
        except KeyError:
            raise OAuthException("Invalid request_token %s!" % request_token)
        iface = self.serverInterface()
        request = iface.requestHandler()
        # Step 1. Use the request token in the session to build a new client.
        callback_url = self.get_callback_url()
        client = Client(OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET, callback_url, self.authenticate_url, self.access_token_url)
        # Step 2. Request the authorized access token from Github.
        self.log('Calling authenticated')
        content = client.get_token(verifier_token)
        """
        You get back something like this:
        u'access_token=a9f2e579db08e3883a24c46f2eaa55a67995ade6&scope=&token_type=bearer'

        or a json dict:

        {u'access_token': u'ya29.Ci8ZAw0tufxVB_lWgrwmP-TGPg5mlNkCH9cWDXDwqO-hxpV8Bv8jySkQQxX2jy-JoA',
         u'token_type': u'Bearer',
         u'expires_in': 3600,
         u'id_token': u'uG6K7zS0F4VUsaQmZSE4h81Q'}
        """
        self.log('authenticated() Got content: %s' % content )
        del self.request_storage[request_token]
        try:
            access_token = dict(urlparse.parse_qsl(content))
        except AttributeError:
            access_token = content
        self.token_storage[access_token['access_token']] = access_token
        self.log('authenticated() Storing access_token %s' % access_token)
        # Clear the parameterMap
        request.removeParameter('ACCESS_TOKEN')
        request.removeParameter('SCOPE')
        request.removeParameter('TOKEN_TYPE')
        return access_token['access_token'], real_callback_url

    def verify_access_token(self, access_token):
        """
        This is not implemented by all providers (Google does)
        The RFC is: https://tools.ietf.org/html/rfc7662
        Default implementation return False
        """
        return False

    def get_access_token(self):
        """
        Implements the logic to obtain a valid access_token.
        Raise OAuthException on error.
        """
        request = self.serverInterface().requestHandler()
        params = request.parameterMap()
        # 1: search in the bearer
        auth_header = params.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            auth_header = self.serverInterface().getEnv('HTTP_AUTHORIZATION')
        if auth_header.find('Bearer ') == 0:
            access_token = auth_header[6:]
            self.log('Got HTTP_AUTHORIZATION bearer: %s' % access_token)
            # Search in cache
            if self.token_storage.get(access_token):
                self.log('HTTP_AUTHORIZATION bearer is verified!')
                return access_token  # is valid!
            else:
                self.log('HTTP_AUTHORIZATION bearer is NOT verified [1]!')
                # Check verify_url
                profile = self.verify_access_token(access_token)
                if profile:
                    self.token_storage[access_token] = profile
                    return access_token  # is valid!
                raise OAuthException('access_token in request is NOT verified!')
        # 2: search in the query string ...
        #    or search in the POST body
        access_token = params.get('ACCESS_TOKEN', None)
        if access_token is not None:
            if self.token_storage.get(access_token):
                self.log('access_token in request is verified!')
                return access_token  # is valid!
            else:
                self.log('access_token in request is NOT verified [2]!')
                # TODO: re-validate the token against Github endpoint
                raise OAuthException('access_token in request is NOT verified!')
        # 4: Search for token from verify step
        #    NOTE: this is not the access_token but a request_token!
        verifier_token = params.get('CODE', None)
        request_token = params.get('STATE', None)
        if verifier_token is not None and request_token is not None:
            try:
                access_token, real_callback_url = self.authenticated(request_token, verifier_token)
                # Redirect
                url = real_callback_url
                scheme, domain, path, params, query, fragment = urlparse.urlparse(url)
                query_params = dict(urlparse.parse_qsl(query))
                # Add access_token to the url
                query_params['access_token'] = access_token
                query = '&'.join(["%s=%s" % (k, v) for k, v in query_params.items()])
                url = urlparse.urlunparse((scheme, domain, path, params, query, fragment))
                self.redirect_url = url
                return None
            except Exception, e:
                self.log('Cannot verify access_token: %s' % e)
                raise OAuthException('Cannot verify access_token!')
        return None

    def requestReady(self):
        self.redirect_url = None
        self.access_token = None
        self.exception = None
        self.error_code = '401 Unauthorized'
        request = self.serverInterface().requestHandler()
        params = request.parameterMap()
        for k, v in params.items():
            self.log('Request parameters: %s: %s' % (k, v))
        # Check settings:
        if not OAUTH2_CLIENT_ID or not OAUTH2_CLIENT_SECRET:
            self.exception = OAuthException('Configuration error: OAUTH2_CLIENT_ID or OAUTH2_CLIENT_SECRET are not set!')
            self.error_code = '500 Internal Server Error'
            request.setParameter('REQUEST', 'OAUTH2')
        else:
            # Try to get a valid access_token
            try:
                self.access_token = self.get_access_token()
            except OAuthException, e:
                self.exception = e
            if self.access_token is None:  # We need to login: skip the core server processing
                request.setParameter('REQUEST', 'OAUTH2')

    def responseComplete(self):
        request = self.serverInterface().requestHandler()
        # REQUEST is OAUTH2: we need to login
        if request.parameterMap().get('REQUEST') == 'OAUTH2' and not self.redirect_url:
            try:
                # Check if the auth was denied
                if request.parameterMap().get('DENIED'):
                    raise OAuthException('Authorization denied by the user!')
                self.login()
            except OAuthException, e:
                # Set an error
                self.exception = e
        # Handle redirects, can be set by login() or authenticated()
        if self.redirect_url:
            self.redirect(self.redirect_url)
        # Handle errors
        if self.exception is not None:
            self.error(self.error_code)
