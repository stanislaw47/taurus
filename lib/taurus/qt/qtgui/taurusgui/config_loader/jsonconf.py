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
import os

from ..utils import PanelDescription, ToolBarDescription, AppletDescription, ExternalApp
from .abstract import AbstractConfigLoader, ConfigLoaderError


__all__ = ["JsonConfigLoader"]


class JsonConfigLoader(AbstractConfigLoader):

    def __init__(self, confname):
        super(JsonConfigLoader, self).__init__(confname)
        self._data = {}

    def _get_objects(self, klass):
        """
        Helper function to get list of Python objects from dictionary
        """
        objs = []
        for o in self._data.get(klass.__name__ + "s", []):  # 's' is for plural form
            if isinstance(o, dict):
                objs.append(klass(**o))
        return objs

    def load(self):
        try:
            with open(self._confname, "r") as fp:
                self._data = json.load(fp)
        except IOError as e:
            raise ConfigLoaderError("Problem with accessing config file: " + str(e))
        except ValueError as e:
            raise ConfigLoaderError("Problem with config file decoding: " + str(e))

    @property
    def conf_dir(self):
        return os.path.abspath(os.path.dirname(self._confname))

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
    def monitor(self):
        return self._data.get("MONITOR")

    @property
    def panels(self):
        return self._get_objects(PanelDescription)

    @property
    def toolbars(self):
        return self._get_objects(ToolBarDescription)

    @property
    def applets(self):
        return self._get_objects(AppletDescription)

    @property
    def external_apps(self):
        return self._get_objects(ExternalApp)
