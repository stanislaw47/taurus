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

import json

from ..utils import PanelDescription, ToolBarDescription, AppletDescription, ExternalApp
from .abstract import AbstractConfigLoader, ConfigLoaderError


__all__ = ["JsonConfigLoader"]


class JsonConfigLoader(AbstractConfigLoader):

    def __init__(self, confname):
        super(JsonConfigLoader, self).__init__(confname)
        self._data = {}

    def load(self):
        try:
            with open(self._confname, "r") as fp:
                self._data = json.load(fp)
        except IOError as e:
            raise ConfigLoaderError("Problem with accessing config file: " + str(e))
        except ValueError as e:
            raise ConfigLoaderError("Problem with config file decoding: " + str(e))

    @property
    def app_name(self):
        return self._data.get("GUI_NAME")

    @property
    def org_name(self):
        return self._data.get("ORGANIZATION")

    @property
    def custom_logo(self):
        return self._data.get("CUSTOM_LOGO")

    @property
    def org_logo(self):
        return self._data.get("ORGANIZATION_LOGO")

    @property
    def single_instance(self):
        return self._data.get("SINGE_INSTANCE")

    @property
    def manual_uri(self):
        return self._data.get("MANUAL_URI")

    @property
    def ini_file(self):
        return self._data.get("INIFILE")

    @property
    def extra_catalog_widgets(self):
        return self._data.get("EXTRA_CATALOG_WIDGETS", [])

    @property
    def synoptics(self):
        return self._data.get("SYNOPTIC", [])

    @property
    def console(self):
        return self._data.get("CONSOLE")

    @property
    def panels(self):
        panels = []
        for p in self._data.get("PanelDescriptions", []):
            if isinstance(p, dict):
                panels.append(PanelDescription(**p))
        return panels

    @property
    def toolbars(self):
        toolbars = []
        for t in self._data.get("ToolBarDescriptions", []):
            if isinstance(t, dict):
                toolbars.append(ToolBarDescription(**t))
        return toolbars

    @property
    def applets(self):
        applets = []
        for a in self._data.get("AppletDescriptions", []):
            if isinstance(a, dict):
                applets.append(AppletDescription(**a))
        return applets

    @property
    def external_apps(self):
        external_apps = []
        for e in self._data.get("ExternalApps", []):
            if isinstance(e, dict):
                external_apps.append(PanelDescription(**e))
        return external_apps
