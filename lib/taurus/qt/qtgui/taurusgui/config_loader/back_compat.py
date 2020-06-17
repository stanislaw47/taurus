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

__all__ = ["BckCompatConfigLoader"]


class BckCompatConfigLoader(AbstractConfigLoader):
    """
    Config loader which provides backward compatibility
    """

    DEPRECATED_VALUES = ["MONITOR", "CONSOLE"]

    @staticmethod
    def supports(confname):
        return PyConfigLoader.supports(confname) or XmlConfigLoader.supports(confname)

    def load(self):
        tmp = {}

        if PyConfigLoader.supports(self._confname):
            py = PyConfigLoader(self._confname)
            py.CONFIG_VALUES + self.DEPRECATED_VALUES
            tmp.update(py.load())

        if XmlConfigLoader.supports(self._confname):
            xml = XmlConfigLoader(self._confname)
            xml.CONFIG_VALUES + self.DEPRECATED_VALUES
            tmp.update(xml.load())

        return tmp
