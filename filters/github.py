# -*- coding: utf-8 -*-
"""
QGIS Server OAuth GitHub filter

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

class OAuth2FilterGithub(OAuth2FilterBase):
    """Github endpoints"""
    access_token_url = 'https://github.com/login/oauth/access_token'
    # This is the slightly different URL used to authenticate/authorize.
    authenticate_url = 'https://github.com/login/oauth/authorize'
    verify_url = 'https://api.github.com/user?access_token='

    def verify_access_token(self, access_token):
        """
        This is not implemented by all providers (Google does)
        Returns the user profile as returned by the verify endpoint
        """
        response = requests.get(self.verify_url + access_token)
        # Invalid token returns 401
        if response.status_code != 200:
            return False
        try:
            profile = json.loads(response.text)
            return profile
        except:
            return False
