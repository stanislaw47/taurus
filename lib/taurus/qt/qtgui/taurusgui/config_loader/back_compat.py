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
from taurus.external.qt import Qt
from taurus.qt.qtgui.taurusgui.config_loader.abstract import (
    AbstractConfigLoader,
)
from taurus.qt.qtgui.taurusgui.config_loader.pyconf import PyConfigLoader
from taurus.qt.qtgui.taurusgui.config_loader.util import HookLoaderError
from taurus.qt.qtgui.taurusgui.config_loader.xmlconf import XmlConfigLoader

__all__ = ["BckCompatConfigLoader"]


class BckCompatConfigLoader(AbstractConfigLoader):
    """
    Config loader which provides backward compatibility
    """

    DEPRECATED_VALUES = ["MONITOR", "CONSOLE"]

    @staticmethod
    def supports(confname):
        return PyConfigLoader.supports(confname) or XmlConfigLoader.supports(
            confname
        )

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

    @property
    def hooks(self):
        return self.loadConsole, self.loadMonitor

    @staticmethod
    def loadMonitor(gui):
        monitor_model = gui.getConfigValue("MONITOR", "")
        if not monitor_model:
            return

        try:
            try:
                gui.splashScreen().showMessage("Creating applet monitor")
            except AttributeError:
                pass

            from taurus.qt.qtgui.qwt5.monitor import TaurusMonitorTiny

            w = TaurusMonitorTiny()
            w.setModel(monitor_model)
            # add the widget to the applets toolbar
            gui.jorgsBar.addWidget(w)
            # register the toolbar as delegate
            gui.registerConfigDelegate(w, "monitor")
        except Exception as e:
            raise HookLoaderError(str(e))

    @staticmethod
    def loadConsole(gui):
        """
        Deprecated CONSOLE command (if you need a IPython Console, just add a
        Panel with a `silx.gui.console.IPythonWidget`
        """
        # TODO: remove this method when making deprecation efective
        if not gui.getConfigValue("CONSOLE", []):
            return

        msg = (
            "createConsole() and the 'CONSOLE' configuration key are "
            + "deprecated since 4.0.4. Add a panel with a "
            + "silx.gui.console.IPythonWidget  widdget instead"
        )
        gui.deprecated(msg)
        try:
            from silx.gui.console import IPythonWidget
        except ImportError:
            gui.warning(
                "Cannot import taurus.qt.qtgui.console. "
                + "The Console Panel will not be available"
            )
            return
        console = IPythonWidget()
        gui.createPanel(
            console,
            "Console",
            permanent=True,
            icon=Qt.QIcon.fromTheme("utilities-terminal"),
        )
