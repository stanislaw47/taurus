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

import sys

import taurus
from taurus.external.qt import Qt
from taurus.qt.qtgui.taurusgui.config_loader.abstract import \
    AbstractConfigLoader
from taurus.qt.qtgui.taurusgui.utils import PanelDescription

__all__ = ["SardanaConfigLoader"]


class SardanaConfigLoader(AbstractConfigLoader):
    """
    Config loader which loads Sardana-related values.
    This lives as a hack for manipulating AbstractLoader.CONFIG_VALUES.
    It does not load anything by itself, just injects new values into
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
        return True

    def load(self):
        return {}

    @property
    def hooks(self):
        return (
            self._loadMacroServerName,
            self._loadMacroBroker,
            self._loadDoorName,
            self._loadMacroEditorsPath,
            self._loadInstrumentsFromPool,
        )

    @staticmethod
    def _loadMacroServerName(gui, conf):
        macro_server_name = gui.getConfigValue(conf, "MACROSERVER_NAME")
        if macro_server_name:
            gui.macroserverNameChanged.emit(macro_server_name)
        return macro_server_name

    @staticmethod
    def _loadMacroBroker(gui, conf):
        """configure macro infrastructure"""
        ms = gui.getConfigValue(conf, "MACROSERVER_NAME")
        mp = gui.getConfigValue(conf, "MACRO_PANELS", True)
        # macro infrastructure will only be created if MACROSERVER_NAME is set
        if ms is not None and mp is True:
            from sardana.taurus.qt.qtgui.macrolistener import MacroBroker

            gui.__macroBroker = MacroBroker(gui)

    @staticmethod
    def _loadDoorName(gui, conf):
        door_name = gui.getConfigValue(conf, "DOOR_NAME", True)
        if door_name:
            gui.doorNameChanged.emit(door_name)

    @staticmethod
    def _loadMacroEditorsPath(gui, conf):
        macro_editors_path = gui.getConfigValue(
            conf, "MACRO_EDITORS_PATH", True
        )
        if macro_editors_path:
            from sardana.taurus.qt.qtgui.extra_macroexecutor.macroparameterseditor.macroparameterseditor import (
                ParamEditorManager,
            )

            ParamEditorManager().parsePaths(macro_editors_path)
            ParamEditorManager().browsePaths()

    def _loadInstrumentsFromPool(self, gui, conf):
        """
        Get panel descriptions from pool if required
        """
        # todo: needs heavy refactor
        ms = gui.getConfigValue(conf, "MACROSERVER_NAME")

        instruments_from_pool = gui.getConfigValue(
            conf, "INSTRUMENTS_FROM_POOL", False
        )
        if instruments_from_pool:
            try:
                gui.splashScreen().showMessage(
                    "Gathering Instrument info from Pool"
                )
            except AttributeError:
                pass
            pool_instruments = self.createInstrumentsFromPool(
                ms
            )  # auto create instruments from pool
        else:
            pool_instruments = []

        if pool_instruments:
            gui._loadCustomPanels(conf, pool_instruments)
        return pool_instruments

    @staticmethod
    def createInstrumentsFromPool(gui, macroservername):
        """
        Creates a list of instrument panel descriptions by gathering the info
        from the Pool. Each panel is a TaurusForm grouping together all those
        elements that belong to the same instrument according to the Pool info

        :return: (list<PanelDescription>)
        """
        # todo: needs heavy refactor
        instrument_dict = {}
        try:
            ms = taurus.Device(macroservername)
            instruments = ms.getElementsOfType("Instrument")
            if instruments is None:
                raise Exception()
        except Exception as e:
            msg = 'Could not fetch Instrument list from "%s"' % macroservername
            gui.error(msg)
            result = Qt.QMessageBox.critical(
                gui,
                "Initialization error",
                "%s\n\n%s" % (msg, repr(e)),
                Qt.QMessageBox.Abort | Qt.QMessageBox.Ignore,
            )
            if result == Qt.QMessageBox.Abort:
                sys.exit()
            return []
        for i in instruments.values():
            i_name = i.full_name
            # i_name, i_unknown, i_type, i_pools = i.split()
            i_view = PanelDescription(
                i_name, classname="TaurusForm", floating=False, model=[]
            )
            instrument_dict[i_name] = i_view

        from operator import attrgetter

        pool_elements = sorted(
            ms.getElementsWithInterface("Moveable").values(),
            key=attrgetter("name"),
        )
        pool_elements += sorted(
            ms.getElementsWithInterface("ExpChannel").values(),
            key=attrgetter("name"),
        )
        pool_elements += sorted(
            ms.getElementsWithInterface("IORegister").values(),
            key=attrgetter("name"),
        )
        for elem in pool_elements:
            instrument = elem.instrument
            if instrument:
                i_name = instrument
                # -----------------------------------------------------------
                # Support sardana v<2.4 (which used tango names instead of
                # taurus full names
                e_name = elem.full_name
                if not e_name.startswith("tango://"):
                    e_name = "tango://%s" % e_name
                # -----------------------------------------------------------
                instrument_dict[i_name].model.append(e_name)
        # filter out empty panels
        ret = [
            instrument
            for instrument in instrument_dict.values()
            if len(instrument.model) > 0
        ]
        return ret
