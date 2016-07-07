# -*- coding: utf-8 -*-
"""
 This script initializes the plugin, making it known to QGIS.
"""


def serverClassFactory(serverIface):
    from OAuthServer import OAuthServer
    return OAuthServer(serverIface)


def classFactory(iface):
    from OAuthServer import FakeOAuthServer
    return FakeOAuthServer(iface)
