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
from operator import attrgetter

from taurus import Device
from taurus.qt.qtgui.taurusgui.config_loader.abstract import (
    AbstractConfigLoader,
)
from taurus.qt.qtgui.taurusgui.config_loader.pyconf import PyConfigLoader
from taurus.qt.qtgui.taurusgui.config_loader.util import HookLoaderError
from taurus.qt.qtgui.taurusgui.config_loader.xmlconf import XmlConfigLoader

__all__ = ["PySardanaConfigLoader", "XmlSardanaConfigLoader"]


class BaseSardanaConfigLoader(AbstractConfigLoader):
    """
    Config loader which loads Sardana-related values.
    This lives as a hack for manipulating AbstractLoader.CONFIG_VALUES.
    It does not load anything by itself, just injects new values into
    CONFIG_VALUES so other loaders will load them.
    """

    SARDANA_VALUES = [
        "MACROSERVER_NAME",
        "MACRO_PANELS",
        "DOOR_NAME",
        "MACROEDITORS_PATH",
        "INSTRUMENTS_FROM_POOL",
    ]

    def __init__(self, confname):
        super(BaseSardanaConfigLoader, self).__init__(confname)
        # explicit copy of AbstractConfigLoader.CONFIG_VALUES is made on purpose
        # this way we avoid problems about changing it for other derived classes
        self.CONFIG_VALUES = (
            AbstractConfigLoader.CONFIG_VALUES[:] + self.SARDANA_VALUES
        )

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
    def _loadMacroServerName(gui):
        macro_server_name = gui.getConfigValue("MACROSERVER_NAME", "")
        if macro_server_name:
            gui.macroserverNameChanged.emit(macro_server_name)
        return macro_server_name

    @staticmethod
    def _loadMacroBroker(gui):
        """configure macro infrastructure"""
        ms = gui.getConfigValue("MACROSERVER_NAME", "")
        mp = gui.getConfigValue("MACRO_PANELS", True)
        # macro infrastructure will only be created if MACROSERVER_NAME is set
        if ms and mp is True:
            from sardana.taurus.qt.qtgui.macrolistener import MacroBroker

            gui.__macroBroker = MacroBroker(gui)

    @staticmethod
    def _loadDoorName(gui):
        door_name = gui.getConfigValue("DOOR_NAME", True)
        if door_name:
            gui.doorNameChanged.emit(door_name)

    @staticmethod
    def _loadMacroEditorsPath(gui):
        macro_editors_path = gui.getConfigValue(
            "MACRO_EDITORS_PATH", True
        )
        if macro_editors_path:
            from sardana.taurus.qt.qtgui.extra_macroexecutor.macroparameterseditor.macroparameterseditor import (
                ParamEditorManager,
            )

            ParamEditorManager().parsePaths(macro_editors_path)
            ParamEditorManager().browsePaths()

    def _loadInstrumentsFromPool(self, gui):
        """
        Get panel descriptions from pool if required
        """
        # todo: needs heavy refactor
        ms = gui.getConfigValue("MACROSERVER_NAME", "")
        if not ms:
            return

        instruments_from_pool = gui.getConfigValue(
            "INSTRUMENTS_FROM_POOL", False
        )
        if instruments_from_pool:
            try:
                gui.splashScreen().showMessage(
                    "Gathering Instrument info from Pool"
                )
            except AttributeError:
                pass

            pool_instruments = self._getInstrumentsFromPool(ms)
            if pool_instruments:
                self._createInstrumentPanels(gui, pool_instruments)

    @staticmethod
    def _getInstrumentsFromPool(gui, macroservername):
        """
        Get Instruments information form Pool. Return models for
        each instrument.

        :param TaurusGui gui: instance of TaurusGui
        :param str macroservername: name of MacroServer

        :return: Dicionary with Pool instruments where values are lists
                 of models
        :rtype: dict(<str, list(<str>)>)
        """
        # todo: needs heavy refactor
        instrument_dict = {}
        try:
            ms = Device(macroservername)
            instruments = ms.getElementsOfType("Instrument")
            if instruments is None:
                raise Exception()
        except Exception as e:
            msg = 'Could not fetch Instrument list from "%s": %s' % (
                macroservername,
                str(e),
            )
            raise HookLoaderError(msg)

        for i in instruments.values():
            instrument_dict[i.full_name] = []

        pool_elements = []
        for kls in ("Moveable", "ExpChannel", "IORegister"):
            pool_elements += sorted(
                ms.getElementsWithInterface(kls).values(),
                key=attrgetter("name"),
            )

        for elem in pool_elements:
            instrument = elem.instrument
            if instrument:
                # -----------------------------------------------------------
                # Support sardana v<2.4 (which used tango names instead of
                # taurus full names
                e_name = elem.full_name
                if not e_name.startswith("tango://"):
                    e_name = "tango://%s" % e_name
                # -----------------------------------------------------------
                instrument_dict[instrument].append(e_name)
        # filter out empty panels
        ret = [i for i in instrument_dict if len(instrument_dict[i]) > 0]
        return ret

    @staticmethod
    def _createInstrumentPanels(gui, poolinstruments):
        """
        Create GUI panels from Sardana Pool instruments. Each panel is a
        TaurusForm grouping together all those elements that belong to
        the same instrument according to the Pool info

        :param TaurusGui gui: isntance of TaurusGui
        :param dict(<str, list(<str>)) poolinstruments: dictionary where keys
                                                        are panel names and
                                                        values are lists of
                                                        models
        :return: None
        """

        for name, model in poolinstruments.items():
            try:
                try:
                    gui.splashScreen().showMessage(
                        "Creating instrument panel %s" % name
                    )
                except AttributeError:
                    pass
                from taurus.qt.qtgui.panel.taurusform import TaurusForm

                w = TaurusForm()

                # -------------------------------------------------------------
                # Backwards-compat. Remove when removing  CW map support
                if gui._customWidgetMap:
                    w.setCustomWidgetMap(gui._customWidgetMap)
                # -------------------------------------------------------------
                w.setModel(model)

                # the pool instruments may change when the pool config changes,
                # so we do not store their config
                gui.createPanel(
                    w,
                    name,
                    floating=False,
                    registerconfig=False,
                    instrumentkey=gui.IMPLICIT_ASSOCIATION,
                    permanent=True,
                )
            except Exception as e:
                msg = "Cannot create instrument panel %s: %s" % (name, str(e))
                raise HookLoaderError(msg)


class PySardanaConfigLoader(PyConfigLoader, BaseSardanaConfigLoader):
    pass


class XmlSardanaConfigLoader(XmlConfigLoader, BaseSardanaConfigLoader):
    pass
