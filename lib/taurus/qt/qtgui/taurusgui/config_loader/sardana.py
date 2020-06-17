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

from taurus.qt.qtgui.taurusgui.config_loader.abstract import (
    AbstractConfigLoader,
)
from taurus.qt.qtgui.taurusgui.config_loader.pyconf import (
    PyConfigLoader
)
from taurus.qt.qtgui.taurusgui.config_loader.xmlconf import (
    XmlConfigLoader
)

__all__ = ["SardanaConfigLoader"]


class SardanaConfigLoader(AbstractConfigLoader):
    """
    Config loader which loads Sardana-related values.
    This lives as a hack for manupulating AbstracLoader.CONFIG_VALUES.
    It does not laod anything by itself, just injects new values into
    CONFIG_VALUES so other laoders will load them.
    """

    SARDANA_VALUES = [
        "MACROSERVER_NAME",
        "MACRO_PANELS",
        "DOOR_NAME",
        "MACROEDITORS_PATH",
        "INSTRUMENTS_FROM_POOL",
    ]

    def __init__(self, confname):
        super(SardanaConfigLoader, self).__init__(confname)
        AbstractConfigLoader.CONFIG_VALUES + self.SARDANA_VALUES

    @staticmethod
    def supports(confname):
        return False

    def load(self):
        return {}

    @property
    def hooks(self):
        return []
