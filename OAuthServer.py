# -*- coding: utf-8 -*-
"""
QGIS Server OAuth Plugin

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = 'Alessandro Pasotti'
__date__ = '05/15/2016'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from oauth_settings import *
import importlib

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

class OAuthServer:
    def __init__(self, serverIface):
        # Get selected filter from settings
        try:
            module = importlib.import_module('filters.%s' % OAUTH2_AUTHORIZATION_SERVICE_PROVIDER)
            klass_name = 'OAuth2Filter%s' % OAUTH2_AUTHORIZATION_SERVICE_PROVIDER.title()
            klass = getattr(module, klass_name)
            serverIface.registerFilter(klass(serverIface), 100)
        except (ImportError, AttributeError), e:
            QgsMessageLog.logMessage('[OAUTH2] ERROR importing provider %s %s' % (OAUTH2_AUTHORIZATION_SERVICE_PROVIDER, e))

class FakeOAuthServer:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

    def initGui(self):
        # Create action that will start plugin
        self.action = QAction(QIcon(":/plugins/"), "About OAuth Server plugin", self.iface.mainWindow())
        # Add toolbar button and menu item
        self.iface.addPluginToMenu("OAuth Server plugin", self.action)
        # connect the action to the run method
        QObject.connect(self.action, SIGNAL("activated()"), self.about)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("OAuth Server plugin", self.action)

    # run
    def about(self):
        QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate(' OAuth Server plugin', " OAuth Server plugin"), QCoreApplication.translate(' OAuth Server plugin', " OAuth Server plugin is a simple OAuth implementation for QGIS Server. See the <a href=\"https://github.com/boundlessgeo/qgis-server-oauth2-auth-plugin/blob/master/README.rst\">README</a> for more information."))



if __name__ == '__main__':
    pass
