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

from taurus.qt.qtgui.taurusgui.config_loader.abstract import (
    AbstractConfigLoader,
)
from taurus.qt.qtgui.taurusgui.config_loader.util import ConfigLoaderError
from taurus.qt.qtgui.taurusgui.utils import (
    AppletDescription,
    ExternalApp,
    PanelDescription,
    ToolBarDescription,
)

__all__ = ["JsonConfigLoader"]


class JsonConfigLoader(AbstractConfigLoader):
    """
    Loads configuration for TaurusGui from JSON file
    """

    def __init__(self, confname):
        super(JsonConfigLoader, self).__init__(confname)
        self._data = {}

    def _get_objects(self, klass):
        """
        Helper function to get list of Python objects from dictionary
        """
        objs = []
        classname = klass.__name__ + "s"  # 's' is for plural form
        for o in self._data.get(classname, []):
            if isinstance(o, dict):
                objs.append(klass(**o))
        return objs

    @staticmethod
    def supports(confname):
        if os.path.isfile(confname):
            ext = os.path.splitext(confname)[-1]
            if ext == ".json":
                return True
        return False

    def _get_data(self):
        try:
            with open(self._confname, "r") as fp:
                self._data = json.load(fp)
        except IOError as e:
            raise ConfigLoaderError(
                "Problem with accessing config file: " + str(e)
            )
        except ValueError as e:
            raise ConfigLoaderError(
                "Problem with config file decoding: " + str(e)
            )

    def load(self):
        self._get_data()

        tmp = {}

        for v in self.CONFIG_VALUES:
            if v in self._data:
                tmp[v] = self._data[v]

        for klass in (
            PanelDescription,
            ToolBarDescription,
            AppletDescription,
            ExternalApp,
        ):
            tmp[klass.__name__ + "s"] = self._get_objects(klass)
        self._data.update(tmp)

        self._data["CONF_DIR"] = os.path.abspath(
            os.path.dirname(self._confname)
        )

        return self._data

    @property
    def hooks(self):
        return []
