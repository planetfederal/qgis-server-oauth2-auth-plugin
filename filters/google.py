# -*- coding: utf-8 -*-
"""
QGIS Server OAuth Google filter

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = 'Alessandro Pasotti'
__date__ = '05/15/2016'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'


from .base import OAuth2FilterBase
import urlparse

class OAuth2FilterGoogle(OAuth2FilterBase):
    """Github endpoints"""
    access_token_url = 'https://www.googleapis.com/oauth2/v4/token'
    # This is the slightly different URL used to authenticate/authorize.
    authenticate_url = 'https://accounts.google.com/o/oauth2/v2/auth'
    # Google needs a scope
    scope = 'profile'

    def get_callback_url(self):
        """Google does not like the query string in the redirect_url"""
        scheme, domain, path, params, query, fragment = urlparse.urlparse(self.get_current_url())
        return urlparse.urlunparse((scheme, domain, path, '', '', ''))
