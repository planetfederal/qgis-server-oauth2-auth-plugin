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

from .base import OAuth2FilterBase

class OAuth2FilterGithub(OAuth2FilterBase):
    """Github endpoints"""
    access_token_url = 'https://github.com/login/oauth/access_token'
    # This is the slightly different URL used to authenticate/authorize.
    authenticate_url = 'https://github.com/login/oauth/authorize'
