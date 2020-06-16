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

    def load(self):
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

    @property
    def conf_dir(self):
        return os.path.abspath(os.path.dirname(self._confname))

    @property
    def app_name(self):
        return self._get("GUI_NAME")

    @property
    def org_name(self):
        return self._get("ORGANIZATION")

    @property
    def custom_logo(self):
        return self._get("CUSTOM_LOGO")

    @property
    def org_logo(self):
        return self._get("ORGANIZATION_LOGO")

    @property
    def single_instance(self):
        return self._get("SINGLE_INSTANCE")

    @property
    def manual_uri(self):
        return self._get("MANUAL_URI")

    @property
    def ini_file(self):
        return self._get("INIFILE")

    @property
    def extra_catalog_widgets(self):
        """
        Not implemented for now
        """
        return []

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

    @property
    def console(self):
        return self._get("CONSOLE")

    @property
    def monitor(self):
        return AppletDescription(
            "monitor",
            classname="TaurusMonitorTiny",
            model=self._get("MONITOR"),
        )

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

    @property
    def macroserver_name(self):
        return self._get("MACROSERVER_NAME")

    @property
    def macro_panels(self):
        return self._get("MACRO_PANELS")

    @property
    def door_name(self):
        return self._get("DOOR_NAME")

    @property
    def macroeditors_path(self):
        return self._get("MACROEDITORS_PATH")

    @property
    def instruments_from_pool(self):
        return self._get("INSTRUMENTS_FROM_POOL")
