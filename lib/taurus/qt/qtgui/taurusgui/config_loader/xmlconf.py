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

import os

from lxml import etree

from taurus.qt.qtgui.taurusgui.utils import (
    PanelDescription,
    ToolBarDescription,
    AppletDescription,
    ExternalApp,
)
from taurus.qt.qtgui.taurusgui.config_loader.abstract import (
    AbstractConfigLoader,
    ConfigLoaderError,
)


__all__ = ["XmlConfigLoader"]


class XmlConfigLoader(AbstractConfigLoader):
    """
    Loads configuration for TaurusGui from XML file
    """

    def __init__(self, confname):
        super(XmlConfigLoader, self).__init__(confname)
        self._root = etree.fromstring("<root></root>")

    def _get(self, nodename, default=None):
        """
        Helper method for getting data from XML
        """
        name = self._root.find(nodename)
        if name is None or name.text is None:
            return default
        else:
            return name.text

    def _get_objects(self, klass):
        """
        Helper method to get list of objects of given Python class
        """
        objs = []
        obj = self._root.find(klass.__name__ + "s")  # 's' is for plural form
        if obj is not None:
            for child in obj:
                if child.tag == klass.__name__:
                    child_str = etree.tostring(child, encoding="unicode")
                    o = klass.fromXml(child_str)
                    if o is not None:
                        objs.append(o)
        return objs

    @staticmethod
    def supports(confname):
        if os.path.isfile(confname):
            ext = os.path.splitext(confname)[-1]
            if ext == ".xml":
                return True
        return False

    def _get_data(self):
        """
        Get the xml root node from the xml configuration file
        """
        try:
            with open(self._confname, "r") as xmlFile:
                self._root = etree.fromstring(xmlFile.read())
        except IOError as e:
            raise ConfigLoaderError(
                "Problem with accessing config file: " + str(e)
            )
        except Exception as e:
            msg = 'Error reading the XML file: "%s"' % self._confname
            raise ConfigLoaderError(msg)

    def load(self):
        self._get_data()

        tmp = {}

        for v in self.CONFIG_VALUES:
            name = self._root.find(v)
            if name is not None and name.text is not None:
                tmp[v] = name.text

        for klass in (PanelDescription, ToolBarDescription, AppletDescription, ExternalApp):
            tmp[klass.__name__ + "s"] = self._get_objects(klass)

        tmp["CONF_DIR"] = os.path.abspath(os.path.dirname(self._confname))

        return tmp

    @property
    def synoptics(self):
        synoptic = []
        node = self._root.find("SYNOPTIC")
        if (node is not None) and (node.text is not None):
            for child in node:
                s = child.get("str")
                # we do not append empty strings
                if s:
                    synoptic.append(s)
        return synoptic
