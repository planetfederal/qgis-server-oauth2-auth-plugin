# -*- coding: utf-8 -*-
"""
QGIS Server OAuth Auth0 filter

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = 'Alessandro Pasotti'
__date__ = '05/15/2016'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'


import requests
import json

from .base import OAuth2FilterBase
from oauth_settings import *

class OAuth2FilterAuth0(OAuth2FilterBase):

    verify_url = OAUTH2_VERIFY_URL

    def verify_access_token(self, access_token):
        """
        This is not implemented by all providers (Google and auth0 do)
        Returns the user profile as returned by the verify endpoint
        """
        if not self.verify_url:
            return False
        response = requests.get(self.verify_url, headers={'Authorization', 'Bearer %s' % access_token})
        # Invalid token returns 400
        if response.status_code != 200:
            return False
        try:
            profile = json.loads(response.text)
            if profile.get('clientID', '') == OAUTH2_CLIENT_ID:
                return profile
        except:
            return False
