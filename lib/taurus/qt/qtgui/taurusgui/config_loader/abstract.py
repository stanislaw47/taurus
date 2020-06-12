#############################################################################
##
# This file is part of Taurus
##
# http://taurus-scada.org
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Taurus is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Taurus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
###########################################################################

""""""

__all__ = ["AbstractConfigLoader", "ConfigLoaderError"]


class ConfigLoaderError(Exception):
    def __init__(self, message):
        message = "Exception raised while loading configuration: " + message
        super(ConfigLoaderError, self).__init__(message)


class AbstractConfigLoader(object):
    """
    Abstract class for config loaders
    """

    def __init__(self, confname):
        self.confname = confname

        self.app_name = None
        self.org_name = None
        self.custom_logo = None
        self.org_logo = None
        self.single_instance = None
        self.manual_uri = None
        self.ini_file = None
        self.extra_catalog_widgets = None
        self.synoptics = None
        self.console = None

        self.panels = []
        self.toolbars = []
        self.applets = []
        self.external_apps = []

    def load():
        pass
