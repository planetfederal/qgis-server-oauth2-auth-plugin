# -*- coding: utf-8 -*-
"""
QGIS Server OAuth Twitter filter

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

import oauth2 as oauth
import urlparse
from urllib2 import quote

from .base import OAuthFilterBase, OAuthException, Cache, OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET

request_token_url = 'https://api.twitter.com/oauth/request_token'
access_token_url = 'https://api.twitter.com/oauth/access_token'
# This is the slightly different URL used to authenticate/authorize.
authenticate_url = 'https://api.twitter.com/oauth/authenticate'

class OAuthFilterTwitter(OAuthFilterBase):

    # Store request_token -> dicts of request_token information
    request_storage = Cache()
    # Store oauth_token -> dict of oauth token information
    token_storage = Cache()
    consumer = oauth.Consumer(OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET)

    def __init__(self, iface):
        super(OAuthFilterTwitter, self).__init__(iface)

    def login(self):
        try:
            request_token = self.request_storage['request_token']
        except KeyError:
            # Step 1. Get a request token from Twitter.
            callback_url = self.get_current_url()
            url = "%s?oauth_callback=%s" % (request_token_url, quote(callback_url))
            self.log('Calling login %s' % url)
            client = oauth.Client(self.consumer)
            resp, content = client.request(url, "GET")
            self.log('Got response: %s' % resp )
            self.log('Got content: %s' % content )
            if resp['status'] != '200':
                raise OAuthException("Invalid response from OAuth endpoint.")
            # Step 2. Store the request token in a session for later use.
            request_token = dict(urlparse.parse_qsl(content))
            if request_token['oauth_callback_confirmed']  != 'true':
                raise OAuthException("Invalid callback.")
            self.request_storage[request_token['oauth_token']] = request_token
        # Step 3. Redirect the user to the authentication URL.
        self.redirect_url = "%s?oauth_token=%s" % (authenticate_url, request_token['oauth_token'])

    def authenticated(self, request_token, verifier_token):
        """
        Call OAuth endpoint to verify the request tokens.
        Return the access_token
        Raise OAuthException on error.
        """
        iface = self.serverInterface()
        request = iface.requestHandler()
        # Step 1. Use the request token in the session to build a new client.
        token = oauth.Token(request_token,
                            self.request_storage[request_token]['oauth_token_secret'])
        token.set_verifier(verifier_token)
        client = oauth.Client(self.consumer, token)

        # Step 2. Request the authorized access token from Twitter.
        self.log('Calling authenticated %s' % access_token_url)
        resp, content = client.request(access_token_url, "GET")
        if resp['status'] != '200':
            print content
            raise OAuthException("Invalid response from OAuth endpoint.")
        """
        This is what you'll get back from Twitter. Note that it includes the
        user's user_id and screen_name.
        {
            'oauth_token_secret': 'IcJXPiJh8be3BjDWW50uCY31chyhsMHEhqJVsphC3M',
            'user_id': '120889797',
            'oauth_token': '120889797-H5zNnM3qE0iFoTTpNEHIz3noL9FKzXiOxwtnyVOD',
            'screen_name': 'heyismysiteup'
        }
        """
        self.log('authenticated() Got response: %s' % resp )
        self.log('authenticated() Got content: %s' % content )
        # You may now access protected resources using the access tokens
        # You should store this access token somewhere safe, like a database,
        # for future use. The request_token can be thrown away
        del self.request_storage[request_token]
        access_token = dict(urlparse.parse_qsl(content))
        self.token_storage[access_token['oauth_token']] = access_token
        self.log('authenticated() Storing access_token %s' % access_token)
        # Clear the parameterMap
        request.removeParameter('OAUTH_TOKEN')
        request.removeParameter('OAUTH_VERIFIER')
        return access_token['oauth_token']

    def get_access_token(self):
        """
        Implements the logic to obtain a valid access_token.
        Raise OAuthException on error.
        """
        request = self.serverInterface().requestHandler()
        params = request.parameterMap()
        # 1: search in the bearer
        auth_header = params.get('HTTP_AUTHORIZATION', '')
        if auth_header.find('Bearer ') == 0:
            access_token = auth_header[6:]
            self.log('Got HTTP_AUTHORIZATION bearer: %s' % access_token)
            # Search in cache
            if self.token_storage.get(access_token):
                self.log('HTTP_AUTHORIZATION bearer is verified!')
                return access_token  # is valid!
            else:
                self.log('HTTP_AUTHORIZATION bearer is NOT verified!')
                raise OAuthException('access_token in request is NOT verified!')
        # 2: search in the query string ...
        #    or search in the POST body
        access_token = params.get('ACCESS_TOKEN', None)
        if access_token is not None:
            if self.token_storage.get(access_token):
                self.log('access_token in request is verified!')
                return access_token  # is valid!
            else:
                self.log('access_token in request is NOT verified!')
                # TODO: re-validate the token against Twitter endpoint
                raise OAuthException('access_token in request is NOT verified!')
        # 4: Search for token from verify step
        #    NOTE: this is not the access_token but a request_token!
        request_token = params.get('OAUTH_TOKEN', None)
        verifier_token = params.get('OAUTH_VERIFIER', None)
        if verifier_token is not None and request_token is not None:
            try:
                access_token = self.authenticated(request_token, verifier_token)
                # Redirect
                url = self.get_current_url()
                # Remove OAUTH_TOKEN and OAUTH_VERIFIER (lower case)
                scheme, domain, path, params, query, fragment = urlparse.urlparse(url)
                query_params = dict(urlparse.parse_qsl(query))
                del query_params['oauth_token']
                del query_params['oauth_verifier']
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
        # REQUEST is OAUTH2 and no redirect set: we need to login
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
