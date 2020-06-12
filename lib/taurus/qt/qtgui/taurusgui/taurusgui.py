#!/usr/bin/env python

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

"""This package provides the TaurusGui class"""

from __future__ import absolute_import

from builtins import str
import os
import sys
import copy
import click
import weakref
import inspect

from future.utils import string_types
from lxml import etree

import taurus
from taurus import tauruscustomsettings
from taurus.external.qt import Qt, compat
from taurus.qt.qtcore.configuration import BaseConfigurableClass
from taurus.qt.qtcore.communication import SharedDataManager
from taurus.qt.qtgui.util import TaurusWidgetFactory
from taurus.qt.qtgui.base import TaurusBaseWidget, TaurusBaseComponent
from taurus.qt.qtgui.container import TaurusMainWindow
from taurus.qt.qtgui.taurusgui.utils import (ExternalApp, PanelDescription,
                                             ToolBarDescription,
                                             AppletDescription)
from taurus.qt.qtgui.util.ui import UILoadable
from taurus.qt.qtgui.taurusgui.utils import ExternalAppAction
from taurus.core.util.log import deprecation_decorator
from taurus.qt.qtgui.taurusgui.config_loader import getLoader


__all__ = ["DockWidgetPanel", "TaurusGui"]

__docformat__ = 'restructuredtext'


@UILoadable(with_ui='ui')
class AssociationDialog(Qt.QDialog):
    '''A dialog for viewing and editing the associations between instruments
    and panels'''

    def __init__(self, parent, flags=None):
        if flags is None:
            flags = Qt.Qt.Widget
        Qt.QDialog.__init__(self, parent, flags)
        self.loadUi()

        self.refresh()
        self.ui.instrumentCB.activated.connect(self.onInstrumentChanged)
        self.ui.buttonBox.clicked.connect(self.onDialogButtonClicked)
        self.ui.refreshBT.clicked.connect(self.refresh)

    def refresh(self):
        currentinstrument = self.ui.instrumentCB.currentText()
        mainwindow = self.parent()

        self.associations = mainwindow.getAllInstrumentAssociations()

        # fill the comboboxes
        self.ui.instrumentCB.clear()
        self.ui.panelCB.clear()
        self.ui.instrumentCB.addItems(sorted(self.associations.keys()))
        self.ui.panelCB.addItems(['__[None]__'] + mainwindow.getPanelNames())

        # restore the index
        idx = self.ui.instrumentCB.findText(currentinstrument)
        if idx == -1 and self.ui.instrumentCB.count() > 0:
            idx = 0
        self.ui.instrumentCB.setCurrentIndex(idx)
        self.onInstrumentChanged(self.ui.instrumentCB.currentText())

    def onInstrumentChanged(self, instrumentname):
        instrumentname = str(instrumentname)
        panelname = self.associations.get(instrumentname)
        if panelname is None:
            self.ui.panelCB.setCurrentIndex(0)
            return
        else:
            idx = self.ui.panelCB.findText(panelname)
            self.ui.panelCB.setCurrentIndex(idx)

    def onDialogButtonClicked(self, button):
        role = self.ui.buttonBox.buttonRole(button)
        if role in (Qt.QDialogButtonBox.AcceptRole, Qt.QDialogButtonBox.ApplyRole):
            if self.ui.panelCB.currentIndex() > 0:
                panelname = str(self.ui.panelCB.currentText())
            else:
                panelname = None
            instrumentname = str(self.ui.instrumentCB.currentText())
            self.associations[instrumentname] = panelname
            self.parent().setInstrumentAssociation(instrumentname, panelname)


class DockWidgetPanel(Qt.QDockWidget, TaurusBaseWidget):
    '''
    This is an extended QDockWidget which provides some methods for being used
    as a "panel" of a TaurusGui application. Widgets of TaurusGui are inserted
    in the application by adding them to a DockWidgetPanel.
    '''

    def __init__(self, parent, widget, name, mainwindow):
        Qt.QDockWidget.__init__(self, None)
        TaurusBaseWidget.__init__(self, name, parent=parent)

        self.setAllowedAreas(Qt.Qt.TopDockWidgetArea)

        self.setWidget(widget)
        # self._widget = self.widget()  #keep a pointer that may change if the
        # widget changes
        name = str(name)
        self.setWindowTitle(name)
        self.setObjectName(name)
        self._custom = False

        # store a weakref of the main window
        self._mainwindow = weakref.proxy(mainwindow)

    def isCustom(self):
        return self._custom

    def setCustom(self, custom):
        self._custom = custom

    def isPermanent(self):
        return self._permanent

    def setPermanent(self, permanent):
        self._permanent = permanent

    def setWidgetFromClassName(self, classname, modulename=None):
        if self.getWidgetClassName() != classname:
            try:
                klass = TaurusWidgetFactory().getWidgetClass(classname)
                w = klass()
            except:
                try:
                    if classname is not None and '.' in classname:
                        mn, classname = classname.rsplit('.', 1)
                        modulename = ("%s.%s" %
                                      (modulename or '', mn)).strip('. ')
                    module = __import__(modulename, fromlist=[''])
                    klass = getattr(module, classname)
                    w = klass()
                except Exception as e:
                    raise RuntimeError(
                        'Cannot create widget from classname "%s". Reason: %s' % (classname, repr(e)))

            # ----------------------------------------------------------------
            # Backwards-compat. Remove when removing  CW map support
            gui_cwmap = self._mainwindow._customWidgetMap
            if gui_cwmap and hasattr(w, 'setCustomWidgetMap'):
                w.setCustomWidgetMap(gui_cwmap)
            # ----------------------------------------------------------------

            self.setWidget(w)
            wname = "%s-%s" % (str(self.objectName()), str(classname))
            w.setObjectName(wname)

    def getWidgetModuleName(self):
        w = self.widget()
        if w is None:
            return ''
        return w.__module__

    def getWidgetClassName(self):
        w = self.widget()
        if w is None:
            return ''
        return w.__class__.__name__

    def applyConfig(self, configdict, depth=-1):
        # create the widget
        try:
            self.setWidgetFromClassName(configdict.get(
                'widgetClassName'), modulename=configdict.get('widgetModuleName', None))
            if isinstance(self.widget(), BaseConfigurableClass):
                self.widget().applyConfig(configdict['widget'])
        except Exception as e:
            self.info(
                'Failed to set the widget for this panel. Reason: %s' % repr(e))
            self.traceback(self.Debug)
            return
        TaurusBaseWidget.applyConfig(self, configdict, depth)

    def createConfig(self, *args, **kwargs):
        configdict = TaurusBaseWidget.createConfig(self, *args, **kwargs)
        configdict['widgetClassName'] = self.getWidgetClassName()
        configdict['widgetModuleName'] = self.getWidgetModuleName()
        if isinstance(self.widget(), BaseConfigurableClass):
            configdict['widget'] = self.widget().createConfig()
        return configdict

    def closeEvent(self, event):
        Qt.QDockWidget.closeEvent(self, event)
        TaurusBaseWidget.closeEvent(self, event)


class TaurusGui(TaurusMainWindow):
    """
    This is main class for constructing the dynamic GUIs. TaurusGui is a
    specialised TaurusMainWindow which is able to handle "panels" and load
    configuration files.
    There are several ways of using TaurusGui. In the following we will give
    3 examples on how to create a simple GUI called "MyGui" which contains one
    panel called "Foo" and consisting of a `QWidget`:

    **Example 1: use declarative configuration files.**

    You can create a purely declarative configuration file to be interpreted by
    the standard `taurusgui` script::

        from taurus.qt.qtgui.taurusgui.utils import PanelDescription

        GUI_NAME = 'MyGui'
        panel = PanelDescription('Foo',
                                 classname='taurus.external.qt.Qt.QWidget')

    Note that this just a very simple example. For a much richer one, see the
    :mod:`taurus.qt.qtgui.taurusgui.conf.tgconf_example01`

    **Example 2: do everything programmatically.**

    A stand-alone python script that launches the gui when executed. No
    configuration file is used here. Panels and other components are added
    programatically::

        if __name__ == '__main__':
            from taurus.qt.qtgui.application import TaurusApplication
            from taurus.qt.qtgui.taurusgui import TaurusGui
            from taurus.external.qt import Qt
            app = TaurusApplication(cmd_line_parser=None, app_name='MyGui')
            gui = TaurusGui()
            panel = Qt.QWidget()
            gui.createPanel(panel, 'Foo')
            gui.show()
            app.exec_()


    **Example 3: mixing declarative and programmatic ways**

    It is also possible to create a stand-alone python script which loads itself
    as a configuration file. In this way you can add things programmatically and
    at the same time use the declarative way::

        GUI_NAME = 'MyGui' # <-- declarative!
        if __name__ == '__main__':
            from taurus.qt.qtgui.application import TaurusApplication
            from taurus.qt.qtgui.taurusgui import TaurusGui
            from taurus.external.qt import Qt
            app = TaurusApplication(cmd_line_parser=None)
            gui = TaurusGui(confname=__file__)
            panel = Qt.QWidget()
            gui.createPanel(panel, 'Foo')  # <-- programmatic!
            gui.show()
            app.exec_()

    """

    SelectedInstrument = Qt.pyqtSignal('QString')
    doorNameChanged = Qt.pyqtSignal('QString')
    macroserverNameChanged = Qt.pyqtSignal('QString')
    newShortMessage = Qt.pyqtSignal('QString')

    IMPLICIT_ASSOCIATION = '__[IMPLICIT]__'

    #: Whether to show user actions related to shared data connections
    PANELS_MENU_ENABLED = True
    #: Whether to show the applets toolbar
    APPLETS_TOOLBAR_ENABLED = True
    #: wether to add the Quick access Toolbar (empty by default)
    QUICK_ACCESS_TOOLBAR_ENABLED = True

    def __init__(self, parent=None, confname=None, configRecursionDepth=None,
                 settingsname=None):
        TaurusMainWindow.__init__(self, parent, False, True)

        if configRecursionDepth is not None:
            self.defaultConfigRecursionDepth = configRecursionDepth

        self.__panels = {}
        self.__external_app = {}
        self.__external_app_actions = {}
        self._external_app_names = []
        self.__permanent_ext_apps = []
        self.__synoptics = []
        self.__instrumentToPanelMap = {}
        self.__panelToInstrumentMap = {}
        self.setDockNestingEnabled(True)

        self.registerConfigProperty(self._getPermanentExternalApps,
                                    self._setPermanentExternalApps,
                                    'permanentexternalapps')
        self.registerConfigProperty(
            self._getPermanentCustomPanels, self._setPermanentCustomPanels, 'permanentCustomPanels')
        self.registerConfigProperty(self.getAllInstrumentAssociations,
                                    self.setAllInstrumentAssociations, 'instrumentAssociation')

        # backwards-compat
        from taurus import tauruscustomsettings
        cwmap = getattr(tauruscustomsettings, 'T_FORM_CUSTOM_WIDGET_MAP', {})
        self._customWidgetMap = cwmap  # deprecated

        # Create a global SharedDataManager
        Qt.qApp.SDM = SharedDataManager(self)

        # Initialize menus & toolbars
        if self.PANELS_MENU_ENABLED:
            self.__initPanelsMenu()
            self.__initPanelsToolBar()
        if self.QUICK_ACCESS_TOOLBAR_ENABLED:
            self.__initQuickAccessToolBar()
        if self.APPLETS_TOOLBAR_ENABLED:
            self.__initJorgBar()

        self.__initSharedDataConnections()

        if self.TOOLS_MENU_ENABLED:
            self.__initToolsMenu()

        # Create lockview actions
        self._lockviewAction = Qt.QAction(Qt.QIcon.fromTheme(
            "system-lock-screen"), "Lock View", self)
        self._lockviewAction.setCheckable(True)
        self._lockviewAction.toggled.connect(self.setLockView)
        self._lockviewAction.setChecked(not self.isModifiableByUser())

        if self.VIEW_MENU_ENABLED:
            self.__initViewMenu()

        if settingsname:
            self.resetQSettings()
            _s = Qt.QSettings(settingsname, Qt.QSettings.IniFormat)
            self.setQSettings(_s)

        self.loadConfiguration(confname)

        # connect the main window itself as a reader/writer of "short messages"
        Qt.qApp.SDM.connectReader("shortMessage", self.onShortMessage)
        Qt.qApp.SDM.connectWriter("shortMessage", self, 'newShortMessage')

        # emit a short message informing that we are ready to go
        msg = '%s is ready' % Qt.qApp.applicationName()
        self.newShortMessage.emit(msg)

        if self.defaultConfigRecursionDepth >= 0:
            self.newShortMessage.emit(
                "Running in Safe Mode. Settings not loaded"
            )
            self.warning(
                "Safe mode: \n"
                + '\n\tLoading of potentially problematic settings is disabled.'
                + '\n\tSome panels may not be loaded or may ignore previous '
                + 'user configuration'
                + '\n\tThis will also apply when loading perspectives'
            )

    def closeEvent(self, event):
        try:
            self.__macroBroker.removeTemporaryPanels()
        except:
            pass
        TaurusMainWindow.closeEvent(self, event)
        for n, panel in self.__panels.items():
            panel.closeEvent(event)
            panel.widget().closeEvent(event)
            if not event.isAccepted():
                result = Qt.QMessageBox.question(
                    self, 'Closing error',
                    "Panel '%s' cannot be closed. Proceed closing?" % n,
                    Qt.QMessageBox.Yes | Qt.QMessageBox.No)
                if result == Qt.QMessageBox.Yes:
                    event.accept()
                else:
                    break

    def __updatePanelsMenu(self):
        '''dynamically fill the panels menus'''
        panelsmenu = self.sender()
        permanent = (panelsmenu == self.__permPanelsMenu)
        panelsmenu.clear()
        panelnames = sorted(
            [n for n, p in self.__panels.items() if (p.isPermanent() == permanent)])
        for name in panelnames:
            panelsmenu.addAction(self.__panels[name].toggleViewAction())

    def __initPanelsMenu(self):
        # Panels menu
        self.__panelsMenu = Qt.QMenu('Panels', self)
        try:  # insert the panels menu before the help menu
            self.menuBar().insertMenu(self.helpMenu.menuAction(),
                                      self.__panelsMenu)
        except AttributeError:  # Or just add it if help menu is not shown
            self.menuBar().addMenu(self.__panelsMenu)
        self.hideAllPanelsAction = self.__panelsMenu.addAction(
            Qt.QIcon('actions:hide.svg'), "Hide all panels", self.hideAllPanels)
        self.showAllPanelsAction = self.__panelsMenu.addAction(
            Qt.QIcon('actions:show.svg'), "Show all panels", self.showAllPanels)
        self.newPanelAction = self.__panelsMenu.addAction(
            Qt.QIcon.fromTheme("window-new"), "New Panel...",
            self.createCustomPanel)
        self.removePanelAction = self.__panelsMenu.addAction(
            Qt.QIcon.fromTheme("edit-clear"), "Remove Panel...",
            self.removePanel)
        self.__panelsMenu.addAction(Qt.QIcon.fromTheme(
            "preferences-desktop-personal"),
            "Switch temporary/permanent status...",
            self.updatePermanentCustomPanels)
        # temporary and permanent panels submenus
        self.__panelsMenu.addSeparator()
        self.__permPanelsMenu = Qt.QMenu('Permanent Panels', self)
        self.__panelsMenu.addMenu(self.__permPanelsMenu)
        self.__permPanelsMenu.aboutToShow.connect(self.__updatePanelsMenu)
        self.__tempPanelsMenu = Qt.QMenu('Temporary Panels', self)
        self.__panelsMenu.addMenu(self.__tempPanelsMenu)
        self.__tempPanelsMenu.aboutToShow.connect(self.__updatePanelsMenu)
        self.__panelsMenu.addSeparator()

    def __initViewMenu(self):
        # the superclass may already have added stuff to the viewMenu
        self.viewMenu.addSeparator()
        # view locking
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self._lockviewAction)

    def __initPanelsToolBar(self):
        # Panels toolbar
        self.panelsToolBar = self.addToolBar("Panels")
        self.panelsToolBar.setObjectName("PanelsToolbar")
        self.panelsToolBar.addAction(self.newPanelAction)
        if self.VIEW_MENU_ENABLED:
            self.viewToolBarsMenu.addAction(self.panelsToolBar.toggleViewAction())

    def __initQuickAccessToolBar(self):
        self.quickAccessToolBar = self.addToolBar("Quick Access")
        self.quickAccessToolBar.setObjectName("quickAccessToolbar")
        self.quickAccessToolBar.setToolButtonStyle(
            Qt.Qt.ToolButtonTextBesideIcon)
        if self.VIEW_MENU_ENABLED:
            self.viewToolBarsMenu.addAction(
                self.quickAccessToolBar.toggleViewAction()
            )

    def __initJorgBar(self):
        # Fancy Stuff ToolBar (aka Jorg's Bar ;) )
        self.jorgsBar = Qt.QToolBar('Fancy ToolBar')
        self.jorgsBar.setObjectName('jorgsToolBar')
        self.addToolBar(Qt.Qt.RightToolBarArea, self.jorgsBar)
        self.jorgsBar.setIconSize(Qt.QSize(60, 60))
        self.jorgsBar.setMovable(False)

    def __initSharedDataConnections(self):
        # register the TAURUSGUI itself as a writer/reader for several shared
        # data items
        splashScreen = self.splashScreen()
        if splashScreen is not None:
            self.splashScreen().showMessage("setting up shared data connections")
        Qt.qApp.SDM.connectWriter(
            "macroserverName", self, 'macroserverNameChanged')
        Qt.qApp.SDM.connectWriter("doorName", self, 'doorNameChanged')
        Qt.qApp.SDM.connectReader(
            "SelectedInstrument", self.onSelectedInstrument)
        Qt.qApp.SDM.connectWriter(
            "SelectedInstrument", self, 'SelectedInstrument')
        Qt.qApp.SDM.connectReader("executionStarted", self.setFocusToPanel)
        Qt.qApp.SDM.connectReader("selectedPerspective", self.loadPerspective)
        Qt.qApp.SDM.connectWriter(
            "perspectiveChanged", self, 'perspectiveChanged')

    def __initToolsMenu(self):
        if self.toolsMenu is None:
            self.toolsMenu = Qt.QMenu("Tools")
        tm = self.toolsMenu
        tm.addAction(Qt.QIcon("apps:preferences-system-session.svg"),
                     "manage instrument-panel associations", self.onShowAssociationDialog)
        tm.addAction(Qt.QIcon.fromTheme("document-save"),
                     "Export current Panel configuration to XML",
                     self.onExportCurrentPanelConfiguration)
        tm.addAction(Qt.QIcon("actions:data-transfer.svg"),
                     "Show Shared Data Manager connections", self.showSDMInfo)

        # tools->external apps submenu
        self.addExternalApplicationAction = self.externalAppsMenu.addAction(
            Qt.QIcon.fromTheme('list-add'),
            'Add external application launcher...',
            self.createExternalApp)
        self.removeExternalApplicationAction = self.externalAppsMenu.addAction(
            Qt.QIcon.fromTheme('list-remove'),
            'Remove external appication launcher...',
            self.removeExternalApp)
        self.externalAppsMenu.addSeparator()

    def createExternalApp(self):
        '''Add a new external application on execution time'''
        from .appsettingswizard import ExternalAppEditor
        app_editor = ExternalAppEditor(self)
        name, xml, ok = app_editor.getDialog()
        if name in self._external_app_names:
            msg = ('The "%s" external application exists in your GUI.'
                   ' If you want to create a new one, '
                   'please use other text label' % name)
            taurus.warning(msg)
            return

        if ok:
            extapp = ExternalApp.fromXml(xml)
            action = extapp.getAction()
            action_name = str(action.text())
            self.__external_app[action_name] = extapp
            self._addExternalAppLauncher(name, action)

    def _addExternalAppLauncher(self, name, action):
        action_name = str(action.text())
        self.__external_app_actions[action_name] = action
        self.addExternalAppLauncher(action)
        self._external_app_names.append(name)

    def removeExternalApp(self, name=None):
        '''Remove the given external application from the GUI.

        :param name: (str or None) the name of the external application to be
                     removed
                     If None given, the user will be prompted
        '''
        apps = list(self.__external_app.keys()) + self.__permanent_ext_apps
        if name is None:
            items = sorted(apps)
            msg1 = "Remove External application"
            msg2 = ("External application to be removed "
                    "(only custom external applications can be removed).")
            name, ok = Qt.QInputDialog.getItem(self, msg1, msg2, items, 0,
                                               False)
            if not ok:
                return
        name = str(name)
        if name not in apps:
            msg = ('Cannot remove the external application "%s"'
                   ' (not found)' % name)
            self.debug(msg)
            return
        if name in list(self.__external_app.keys()):
            self.__external_app.pop(name)
        else:
            self.__permanent_ext_apps.remove(name)
        action = self.__external_app_actions.pop(name)
        self._external_app_names.remove(name)
        self.deleteExternalAppLauncher(action)
        self.debug('External application "%s" removed' % name)

    @deprecation_decorator(alt="item factories", rel="4.6.5")
    def setCustomWidgetMap(self, map):
        '''
        Sets the widget map that is used application-wide. This widget map will
        be used by default in all TaurusForm Panels belonging to this gui.

        :param map: (dict<str,Qt.QWidget>) a dictionary whose keys are device
                    type strings (e.g. see :class:`PyTango.DeviceInfo`) and
                    whose values are widgets to be used

        .. seealso:: :meth:`TaurusForm.setCustomWidgetMap`, :meth:`getCustomWidgetMap`
        '''
        self._customWidgetMap = map

    @deprecation_decorator(alt="item factories", rel="4.6.5")
    def getCustomWidgetMap(self):
        '''
        Returns the default map used to create custom widgets by the TaurusForms
        belonging to this GUI

        :return: (dict<str,Qt.QWidget>) a dictionary whose keys are device
                 type strings (i.e. see :class:`PyTango.DeviceInfo`) and whose
                 values are widgets to be used

        .. seealso:: :meth:`setCustomWidgetMap`
        '''
        return self._customWidgetMap

    def createConfig(self, *args, **kwargs):
        '''reimplemented from TaurusMainWindow.createConfig'''
        self.updatePermanentCustomPanels(showAlways=False)
        self.updatePermanentExternalApplications(showAlways=False)
        cfg = TaurusMainWindow.createConfig(self, *args, **kwargs)
        return cfg

    def removePanel(self, name=None):
        ''' remove the given panel from the GUI.

        .. note:: The panel; is actually removed from the current perspective.
                  If the panel is saved in other perspectives, it should be removed from
                  them as well.

        :param name: (str or None) the name of the panel to be removed
                     If None given, the user will be prompted
        '''
        if name is None:
            items = sorted(
                [n for n, p in self.__panels.items() if p.isCustom()])
            name, ok = Qt.QInputDialog.getItem(self, "Remove Panel",
                                               "Panel to be removed (only custom panels can be removed).\n Important: you may want to save the perspective afterwards,\n and maybe remove the panel from other perspectives as well", items, 0, False)
            if not ok:
                return
        name = str(name)
        if name not in self.__panels:
            self.debug('Cannot remove panel "%s" (not found)' % name)
            return
        panel = self.__panels.pop(name)
        try:
            # in case the widget is a Taurus one and does some cleaning when
            # setting model to None
            panel.widget().setModel(None)
        except:
            pass

        self.unregisterConfigurableItem(name, raiseOnError=False)
        self.removeDockWidget(panel)
        panel.setParent(None)
        panel.setAttribute(Qt.Qt.WA_DeleteOnClose)
        panel.close()
        self.debug('Panel "%s" removed' % name)

    def createPanel(self, widget, name, floating=False, registerconfig=True, custom=False,
                    permanent=False, icon=None, instrumentkey=None):
        '''
        Creates a panel containing the given widget.

        :param wiget: (QWidget) the widget to be contained in the panel
        :param name: (str) the name of the panel. It will be used in tabs as well as for configuration
        :param floating: (bool) whether the panel should be docked or floating. (see note below)
        :param registerconfig: (bool) if True, the panel will be registered as a delegate for configuration
        :param custom: (bool) if True the panel is to be considered a "custom panel"
        :param permanent: (bool) set this to True for panels that need to be recreated when restoring the app
        :param icon: (QIcon) icon for the panel
        :param instrumentkey: (str) name of an instrument to which this panel is to be associated

        :return: (DockWidgetPanel) the created panel

        .. note:: On a previous version, there was a mandatory parameter called
                  `area` (which accepted a Qt.DockWidgetArea or None as values)
                  this parameter has now been substituted by the keyword
                  argument `floating`. In order to provide backwards
                  compatibility, the "floating" keyword argument stays at the
                  same position as the old `area` argument and if a Qt.DockWidgetArea
                  value is given, it will be interpreted as floating=True (while if
                  `None` is passed, it will be interpreted as floating=False.
        '''

        # backwards compatibility:
        if not isinstance(floating, bool):
            self.info(
                'Deprecation warning: please note that the "area" argument is deprecated. See TaurusGui.createPanel doc')
            floating = not(floating)

        name = str(name)
        if name in self.__panels:
            self.info('Panel with name "%s" already exists. Reusing.' % name)
            return self.__panels[name]

        # create a panel
        panel = DockWidgetPanel(None, widget, name, self)
        # we will only place panels in this area
        self.addDockWidget(Qt.Qt.TopDockWidgetArea, panel)
        if len(self.__panels) != 0:
            self.tabifyDockWidget(list(self.__panels.values())[-1], panel)

        panel.setFloating(floating)

        # associate this panel with an instrument
        if instrumentkey is not None:
            if instrumentkey == self.IMPLICIT_ASSOCIATION:
                # see if there is an item whose name is the same as that of the
                # panel
                for syn in self.__synoptics:
                    if name in syn.get_item_list():
                        self.setInstrumentAssociation(name, name)
                        break
            else:
                self.setInstrumentAssociation(instrumentkey, name)

        if icon is not None:
            panel.toggleViewAction().setIcon(icon)

        # set flags
        panel.setCustom(custom)
        panel.setPermanent(permanent)

        # register the panel for configuration
        if registerconfig:
            self.registerConfigDelegate(panel, name=name)
        self.__panels[name] = panel

        # connect the panel visibility changes
        panel.visibilityChanged.connect(self._onPanelVisibilityChanged)

        return panel

    def getPanel(self, name):
        '''get a panel object by name

        :return: (DockWidgetPanel)
        '''
        return self.__panels[str(name)]

    def getPanelNames(self):
        '''returns the names of existing panels

        :return: (list<str>)
        '''
        return copy.deepcopy(list(self.__panels.keys()))

    def _setPermanentExternalApps(self, permExternalApps):
        '''creates empty panels for restoring custom panels.

        :param permCustomPanels: (list<str>) list of names of custom panels
        '''
        # first create the panels if they don't actually exist
        for name in permExternalApps:
            if name not in self._external_app_names:
                # create empty action
                self.__permanent_ext_apps.append(name)
                action = ExternalAppAction('', name)
                self._addExternalAppLauncher(name, action)

    def _getPermanentExternalApps(self):
        return self.__permanent_ext_apps

    def _setPermanentCustomPanels(self, permCustomPanels):
        '''creates empty panels for restoring custom panels.

        :param permCustomPanels: (list<str>) list of names of custom panels
        '''
        # first create the panels if they don't actually exist
        for name in permCustomPanels:
            if name not in self.__panels:
                self.createPanel(None, name, custom=True, permanent=True)

    def _getPermanentCustomPanels(self):
        '''
        returns a list of panel names for which the custom and permanent flags
        are True (i.e., those custom panels that should be stored in
        configuration and/or perspectives)

        :return: (list<str>)
        '''
        return [n for n, p in self.__panels.items() if (p.isCustom() and p.isPermanent())]

    def updatePermanentCustomPanels(self, showAlways=True):
        '''
        Shows a dialog for selecting which custom panels should be permanently
        stored in the configuration.

        :param showAlways: (bool) forces showing the dialog even if there are no new custom Panels
        '''
        # check if there are some newly created panels that may be made
        # permanent
        perm = self._getPermanentCustomPanels()
        temp = [n for n, p in self.__panels.items() if (
            p.isCustom() and not p.isPermanent())]
        if len(temp) > 0 or showAlways:
            from taurus.qt.qtgui.panel import QDoubleListDlg
            dlg = QDoubleListDlg(winTitle='Stored panels',
                                 mainLabel='Select which of the panels should be stored',
                                 label1='Temporary (to be discarded)', label2='Permanent (to be stored)',
                                 list1=temp, list2=perm)
            result = dlg.exec_()
            if result == Qt.QDialog.Accepted:
                # update the permanent Custom Panels
                registered = self.getConfigurableItemNames()
                for name in dlg.getAll2():
                    if name not in registered:
                        self.__panels[name].setPermanent(True)
                        self.registerConfigDelegate(self.__panels[name], name)
                # unregister any panel that is temporary
                for name in dlg.getAll1():
                    self.__panels[name].setPermanent(False)
                    self.unregisterConfigurableItem(name, raiseOnError=False)

    def updatePermanentExternalApplications(self, showAlways=True):
        '''
        Shows a dialog for selecting which new externals applications
        should be permanently stored in the configuration.

        :param showAlways: (bool) forces showing the dialog
        '''
        # check if there are some newly created external applications that may
        # be made permanent
        #permanet_ext_app = list(self._external_app_names)
        if len(self.__external_app) > 0 or showAlways:
            from taurus.qt.qtgui.panel import QDoubleListDlg
            msg = 'Select which of the external applications should be stored'
            dlg = QDoubleListDlg(winTitle='Stored external applications',
                                 mainLabel=msg,
                                 label1='Temporary (to be discarded)',
                                 label2='Permanent (to be stored)',
                                 list1=list(self.__external_app.keys()),
                                 list2=self.__permanent_ext_apps)
            result = dlg.exec_()
            if result == Qt.QDialog.Accepted:
                # update the temporally external applications
                for name in dlg.getAll2():
                    self.__permanent_ext_apps.append(str(name))
                    if name in self.__external_app:
                        self.__external_app.pop(str(name))

                for name in dlg.getAll1():
                    self.unregisterConfigurableItem("_extApp[%s]" % str(name),
                                                    raiseOnError=False)

    def createCustomPanel(self, paneldesc=None):
        '''
        Creates a panel from a Panel Description and sets it as "custom panel".

        :param paneldesc: (PanelDescription) description of the panel to be created

        .. seealso:: :meth:`createPanel`
        '''

        if paneldesc is None:
            from taurus.qt.qtgui.taurusgui import PanelDescriptionWizard
            paneldesc, ok = PanelDescriptionWizard.getDialog(
                self, extraWidgets=self._extraCatalogWidgets)
            if not ok:
                return
        w = paneldesc.getWidget(sdm=Qt.qApp.SDM, setModel=False)
        # ----------------------------------------------------------------
        # Backwards-compat. Remove when removing  CW map support
        if self._customWidgetMap and hasattr(w, 'setCustomWidgetMap'):
            w.setCustomWidgetMap(self._customWidgetMap)
        # ----------------------------------------------------------------
        if paneldesc.model is not None:
            w.setModel(paneldesc.model)

        if isinstance(w, TaurusBaseComponent):
            # TODO: allow to select these options in the dialog
            w.setModifiableByUser(True)
            w.setModelInConfig(True)

        self.createPanel(w, paneldesc.name, floating=paneldesc.floating, custom=True,
                         registerconfig=False, instrumentkey=paneldesc.instrumentkey,
                         permanent=False)
        msg = 'Panel %s created. Drag items to it or use the context menu to customize it' % w.name
        self.newShortMessage.emit(msg)

    def createMainSynoptic(self, synopticname):
        '''
        Creates a synoptic panel and registers it as "SelectedInstrument"
        reader and writer (allowing  selecting instruments from synoptic
        '''
        try:
            jdwFileName = os.path.join(self._confDirectory, synopticname)
            from taurus.qt.qtgui.graphic import TaurusJDrawSynopticsView
            synoptic = TaurusJDrawSynopticsView()
            synoptic.setModel(jdwFileName)
            self.__synoptics.append(synoptic)
        except Exception as e:
            # print repr(e)
            msg = 'Error loading synoptic file "%s".\nSynoptic won\'t be available' % jdwFileName
            self.error(msg)
            self.traceback(level=taurus.Info)
            result = Qt.QMessageBox.critical(self, 'Initialization error', '%s\n\n%s' % (
                msg, repr(e)), Qt.QMessageBox.Abort | Qt.QMessageBox.Ignore)
            if result == Qt.QMessageBox.Abort:
                sys.exit()

        Qt.qApp.SDM.connectWriter(
            "SelectedInstrument", synoptic, "graphicItemSelected")
        Qt.qApp.SDM.connectReader(
            "SelectedInstrument", synoptic.selectGraphicItem)

        # find an unique (and short) name
        name = os.path.splitext(os.path.basename(synopticname))[0]
        if len(name) > 10:
            name = 'Syn'
        i = 2
        prefix = name
        while name in self.__panels:
            name = '%s_%i' % (prefix, i)
            i += 1

        synopticpanel = self.createPanel(synoptic, name, permanent=True,
                                         icon=Qt.QIcon.fromTheme(
                                             'image-x-generic'))

        if self.QUICK_ACCESS_TOOLBAR_ENABLED:
            toggleSynopticAction = synopticpanel.toggleViewAction()
            self.quickAccessToolBar.addAction(toggleSynopticAction)

    def createConsole(self, kernels):
        msg = ('createConsole() and the "CONSOLE" configuration key are ' +
               'deprecated since 4.0.4. Add a panel with a ' +
               'silx.gui.console.IPythonWidget  widdget instead')
        self.deprecated(msg)
        try:
            from silx.gui.console import IPythonWidget
        except ImportError:
            self.warning('Cannot import taurus.qt.qtgui.console. ' +
                         'The Console Panel will not be available')
            return
        console = IPythonWidget()
        self.createPanel(console, "Console", permanent=True,
                         icon=Qt.QIcon.fromTheme('utilities-terminal'))

    def createInstrumentsFromPool(self, macroservername):
        '''
        Creates a list of instrument panel descriptions by gathering the info
        from the Pool. Each panel is a TaurusForm grouping together all those
        elements that belong to the same instrument according to the Pool info

        :return: (list<PanelDescription>)
        '''
        instrument_dict = {}
        try:
            ms = taurus.Device(macroservername)
            instruments = ms.getElementsOfType('Instrument')
            if instruments is None:
                raise Exception()
        except Exception as e:
            msg = 'Could not fetch Instrument list from "%s"' % macroservername
            self.error(msg)
            result = Qt.QMessageBox.critical(self, 'Initialization error', '%s\n\n%s' % (
                msg, repr(e)), Qt.QMessageBox.Abort | Qt.QMessageBox.Ignore)
            if result == Qt.QMessageBox.Abort:
                sys.exit()
            return []
        for i in instruments.values():
            i_name = i.full_name
            #i_name, i_unknown, i_type, i_pools = i.split()
            i_view = PanelDescription(
                i_name, classname='TaurusForm', floating=False, model=[])
            instrument_dict[i_name] = i_view

        from operator import attrgetter
        pool_elements = sorted(ms.getElementsWithInterface(
            'Moveable').values(), key=attrgetter('name'))
        pool_elements += sorted(ms.getElementsWithInterface(
            'ExpChannel').values(), key=attrgetter('name'))
        pool_elements += sorted(ms.getElementsWithInterface(
            'IORegister').values(), key=attrgetter('name'))
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
        ret = [instrument for instrument in instrument_dict.values()
               if len(instrument.model) > 0]
        return ret

    def getConfigValue(self, conf, field, default=None):
        value = getattr(conf, field)
        if value is None:
            return default
        else:
            return value

    def loadConfiguration(self, confname):
        '''Reads a configuration file
        '''
        try:
            conf = getLoader(confname)
            conf.load()
            self._confDirectory = conf.conf_dir
        except Exception:
            import traceback
            msg = 'Error loading configuration: %s' % traceback.format_exc()  # repr(e)
            self.error(msg)
            Qt.QMessageBox.critical(
                self, 'Initialization error', msg, Qt.QMessageBox.Abort)
            sys.exit()

        self._loadAppName(conf, confname)
        self._loadOrgName(conf)
        self._loadCustomLogo(conf)
        Qt.QApplication.instance().basicConfig()
        self._loadOrgLogo(conf)

        self._loadSingleInstance(conf)

        self._loadExtraCatalogWidgets(conf)
        self._loadManualUri(conf)
        POOLINSTRUMENTS = self._loadSardanaOptions(conf)
        self._loadSynoptic(conf)
        # TODO: remove deprecated _loadConsole
        self._loadConsole(conf)

        self._loadCustomPanels(conf, POOLINSTRUMENTS)
        self._loadCustomToolBars(conf)
        self._loadCustomApplets(conf)
        self._loadExternalApps(conf)
        self._loadIniFile(conf)

    def _loadAppName(self, conf, confname):
        appname = self.getConfigValue(conf, "app_name")
        Qt.qApp.setApplicationName(appname)
        self.setWindowTitle(appname)

    def _loadOrgName(self, conf):
        orgname = self.getConfigValue(conf, "org_name", str(Qt.qApp.organizationName()) or 'Taurus')
        Qt.qApp.setOrganizationName(orgname)

    def _loadCustomLogo(self, conf):
        custom_logo = self.getConfigValue(conf, "custom_logo", 'logos:taurus.png')
        if Qt.QFile.exists(custom_logo):
            custom_icon = Qt.QIcon(custom_logo)
        else:
            custom_icon = Qt.QIcon(os.path.join(
                self._confDirectory, custom_logo))
        self.setWindowIcon(custom_icon)
        if self.APPLETS_TOOLBAR_ENABLED:
            self.jorgsBar.addAction(custom_icon, Qt.qApp.applicationName())

    def _loadOrgLogo(self, conf):
        logo = getattr(tauruscustomsettings,
                       "ORGANIZATION_LOGO",
                       "logos:taurus.png")
        org_logo = self.getConfigValue(conf, "org_logo", logo)
        if Qt.QFile.exists(org_logo):
            org_icon = Qt.QIcon(org_logo)
        else:
            org_icon = Qt.QIcon(os.path.join(
                self._confDirectory, org_logo))
        if self.APPLETS_TOOLBAR_ENABLED:
            self.jorgsBar.addAction(org_icon, Qt.qApp.organizationName())

    def _loadSingleInstance(self, conf):
        """
        if required, enforce that only one instance of this GUI can be run
        """
        single_inst = self.getConfigValue(conf, "single_instance", True)

        if single_inst:
            if not self.checkSingleInstance():
                msg = 'Only one instance of %s is allowed to run the same time' % (
                    Qt.qApp.applicationName())
                self.error(msg)
                Qt.QMessageBox.critical(
                    self, 'Multiple copies', msg, Qt.QMessageBox.Abort)
                sys.exit(1)

    def _loadExtraCatalogWidgets(self, conf):
        """
        get custom widget catalog entries
        """
        # @todo: support also loading from xml
        extra_catalog_widgets = self.getConfigValue(conf, "extra_catalog_widgets", [])
        self._extraCatalogWidgets = []
        for class_name, pix_map_name in extra_catalog_widgets:
            # If a relative file name is given, the conf directory will be used
            # as base path
            if pix_map_name and not Qt.QFile.exists(pix_map_name):
                pix_map_name = os.path.join(self._confDirectory, pix_map_name)
            self._extraCatalogWidgets.append((class_name, pix_map_name))

    def _loadManualUri(self, conf):
        """
        manual panel
        """
        manual_uri = self.getConfigValue(conf, "manual_uri", taurus.Release.url)
        self.setHelpManualURI(manual_uri)

        if self.HELP_MENU_ENABLED:
            self.createPanel(self.helpManualBrowser, 'Manual', permanent=True,
                             icon=Qt.QIcon.fromTheme('help-browser'))

    ### SARDANA MACRO STUFF ON
    def _loadSardanaOptions(self, conf):
        """configure macro infrastructure"""
        ms = self._loadMacroServerName(conf)
        mp = self._loadMacroPanels(conf)
        # macro infrastructure will only be created if MACROSERVER_NAME is set
        if ms is not None and mp is True:
            from sardana.taurus.qt.qtgui.macrolistener import MacroBroker
            self.__macroBroker = MacroBroker(self)
        self._loadDoorName(conf)
        self._loadMacroEditorsPath(conf)
        pool_instruments = self._loadInstrumentsFromPool(conf, ms)
        return pool_instruments

    def _loadMacroServerName(self, conf):
        macro_server_name = self.getConfigValue(conf, "macroserver_name")
        if macro_server_name:
            self.macroserverNameChanged.emit(macro_server_name)
        return macro_server_name

    def _loadMacroPanels(self, conf):
        return self.getConfigValue(conf, "macro_panels", True)

    def _loadDoorName(self, conf):
        door_name = self.getConfigValue(conf, "door_name", True)
        if door_name:
            self.doorNameChanged.emit(door_name)

    def _loadMacroEditorsPath(self, conf):
        macro_editors_path = self.getConfigValue(conf, "macroeditors_path", True)
        if macro_editors_path:
            from sardana.taurus.qt.qtgui.extra_macroexecutor.macroparameterseditor.macroparameterseditor import \
                ParamEditorManager
            ParamEditorManager().parsePaths(macro_editors_path)
            ParamEditorManager().browsePaths()

    def _loadInstrumentsFromPool(self, conf, macro_server_name):
        """
        Get panel descriptions from pool if required
        """
        instruments_from_pool = self.getConfigValue(conf, "instruments_from_pool", False)
        if instruments_from_pool:
            try:
                self.splashScreen().showMessage("Gathering Instrument info from Pool")
            except AttributeError:
                pass
            pool_instruments = self.createInstrumentsFromPool(
                macro_server_name)  # auto create instruments from pool
        else:
            pool_instruments = []
        return pool_instruments
    ### SARDANA MACRO STUFF OFF
    
    def _loadSynoptic(self, conf):
        # Synoptics
        synoptic = self.getConfigValue(conf, "synoptic", [])
        if isinstance(synoptic, string_types):  # old config file style
            self.warning(
                'Deprecated usage of synoptic keyword (now it expects a list of paths). Please update your configuration file to: "synoptic=[\'%s\']".' % synoptic)
            synoptic = [synoptic]
        for s in synoptic:
            self.createMainSynoptic(s)

    def _loadConsole(self, conf):
        """
        Deprecated CONSOLE command (if you need a IPython Console, just add a
        Panel with a `silx.gui.console.IPythonWidget`
        """
        # TODO: remove this method when making deprecation efective
        console = self.getConfigValue(conf, "console", [])
        if console:
            self.createConsole([])

    def _loadCustomPanels(self, conf, poolinstruments=None):
        """
        get custom panel descriptions from the python config file, xml config and
        create panels based on the panel descriptions
        """

        custom_panels = conf.panels

        for p in custom_panels + poolinstruments:
            try:
                try:
                    self.splashScreen().showMessage("Creating panel %s" % p.name)
                except AttributeError:
                    pass
                w = p.getWidget(sdm=Qt.qApp.SDM, setModel=False)

                for key, value in p.widget_properties.items():
                    # set additional configuration for the
                    if hasattr(w, key):
                        try:
                            setattr(w, key, value)
                        except Exception as e:
                            msg = "Cannot set %r.%s=%s" % (w, key, str(value))
                            self.error(msg)
                            self.traceback(level=taurus.Info)
                            result = Qt.QMessageBox.critical(
                                self,
                                "Initialization error",
                                "%s\n\n%r" % (msg, e),
                                Qt.QMessageBox.Abort | Qt.QMessageBox.Ignore
                            )
                            if result == Qt.QMessageBox.Abort:
                                sys.exit()
                # -------------------------------------------------------------
                # Backwards-compat. Remove when removing  CW map support
                if self._customWidgetMap and hasattr(w, 'setCustomWidgetMap'):
                    w.setCustomWidgetMap(self._customWidgetMap)
                # -------------------------------------------------------------
                if p.model is not None:
                    w.setModel(p.model)
                if p.instrumentkey is None:
                    instrumentkey = self.IMPLICIT_ASSOCIATION

                if isinstance(w, TaurusBaseComponent):
                    if p.modifiable_by_user is not None:
                        w.setModifiableByUser(p.modifiable_by_user)
                    if p.model_in_config is not None:
                        w.setModelInConfig(p.model_in_config)
                    if p.widget_formatter is not None:
                        w.setFormat(p.widget_formatter)

                icon = p.icon
                # the pool instruments may change when the pool config changes,
                # so we do not store their config
                registerconfig = p not in poolinstruments
                # create a panel

                self.createPanel(
                    w,
                    p.name,
                    floating=p.floating,
                    registerconfig=registerconfig,
                    instrumentkey=instrumentkey,
                    permanent=True,
                    icon=icon
                )
            except Exception as e:
                msg = "Cannot create panel %s" % getattr(
                    p, "name", "__Unknown__")
                self.error(msg)
                self.traceback(level=taurus.Info)
                result = Qt.QMessageBox.critical(self, "Initialization error", "%s\n\n%s" % (
                    msg, repr(e)), Qt.QMessageBox.Abort | Qt.QMessageBox.Ignore)
                if result == Qt.QMessageBox.Abort:
                    sys.exit()

    def _loadCustomToolBars(self, conf):
        """
        get custom toolbars descriptions from the python config file, xml config and
        create toolbars based on the descriptions
        """
        for d in conf.toolbars:
            try:
                try:
                    self.splashScreen().showMessage("Creating Toolbar %s" % d.name)
                except AttributeError:
                    pass
                w = d.getWidget(sdm=Qt.qApp.SDM, setModel=False)
                if d.model is not None:
                    w.setModel(d.model)
                w.setWindowTitle(d.name)
                # add the toolbar to the window
                self.addToolBar(w)
                # add the toggleview action to the view menu
                self.viewToolBarsMenu.addAction(w.toggleViewAction())
                # register the toolbar as delegate if it supports it
                if isinstance(w, BaseConfigurableClass):
                    self.registerConfigDelegate(w, d.name)

            except Exception as e:
                msg = "Cannot add toolbar %s" % getattr(
                    d, "name", "__Unknown__")
                self.error(msg)
                self.traceback(level=taurus.Info)
                result = Qt.QMessageBox.critical(self, "Initialization error", "%s\n\n%s" % (
                    msg, repr(e)), Qt.QMessageBox.Abort | Qt.QMessageBox.Ignore)
                if result == Qt.QMessageBox.Abort:
                    sys.exit()

    def _loadCustomApplets(self, conf):
        """
        get custom applet descriptions from the python config file, xml config and
        create applet based on the descriptions
        """
        custom_applets = conf.applets[:]
        # for backwards compatibility
        MONITOR = self.getConfigValue(conf, "monitor", [])
        if MONITOR:
            custom_applets.append(AppletDescription(
                "monitor", classname="TaurusMonitorTiny", model=MONITOR))

        for d in custom_applets:
            try:
                try:
                    self.splashScreen().showMessage("Creating applet %s" % d.name)
                except AttributeError:
                    pass
                w = d.getWidget(sdm=Qt.qApp.SDM, setModel=False)
                if d.model is not None:
                    w.setModel(d.model)
                # add the widget to the applets toolbar
                self.jorgsBar.addWidget(w)
                # register the toolbar as delegate if it supports it
                if isinstance(w, BaseConfigurableClass):
                    self.registerConfigDelegate(w, d.name)
            except Exception as e:
                msg = "Cannot add applet %s" % getattr(
                    d, "name", "__Unknown__")
                self.error(msg)
                self.traceback(level=taurus.Info)
                result = Qt.QMessageBox.critical(self, "Initialization error", "%s\n\n%s" % (
                    msg, repr(e)), Qt.QMessageBox.Abort | Qt.QMessageBox.Ignore)
                if result == Qt.QMessageBox.Abort:
                    sys.exit()

    def _loadExternalApps(self, conf):
        """
        add external applications from both the python and the xml config files
        """
        for a in conf.external_apps:
            self._external_app_names.append(str(a.getAction().text()))
            self.addExternalAppLauncher(a.getAction())

    def _loadIniFile(self, conf):
        """
        get the "factory settings" filename. By default, it is called
        "default.ini" and resides in the configuration dir
        """
        ini_file = self.getConfigValue(conf, "ini_file", "default.ini")

        # if a relative name is given, the conf dir is used as the root path
        ini_file_name = os.path.join(self._confDirectory, ini_file)

        # read the settings (or the factory settings if the regular file is not
        # found)
        msg = "Loading previous state"
        if self.defaultConfigRecursionDepth >= 0:
            msg += " in Fail Proof mode"
        try:
            self.splashScreen().showMessage(msg)
        except AttributeError:
            pass
        self.loadSettings(factorySettingsFileName=ini_file_name)

    def setLockView(self, locked):
        self.setModifiableByUser(not locked)

    def setModifiableByUser(self, modifiable):
        if modifiable:
            dwfeat = Qt.QDockWidget.AllDockWidgetFeatures
        else:
            dwfeat = Qt.QDockWidget.NoDockWidgetFeatures
        for panel in self.__panels.values():
            panel.toggleViewAction().setEnabled(modifiable)
            panel.setFeatures(dwfeat)

        if self.PANELS_MENU_ENABLED:
            for action in (self.newPanelAction, self.showAllPanelsAction,
                           self.hideAllPanelsAction,
                        ):
                action.setEnabled(modifiable)

        if self.TOOLS_MENU_ENABLED:
            for action in (self.addExternalApplicationAction,
                           self.removeExternalApplicationAction,
                        ):
                action.setEnabled(modifiable)

        self._lockviewAction.setChecked(not modifiable)

        TaurusMainWindow.setModifiableByUser(self, modifiable)

    def onShortMessage(self, msg):
        ''' Slot to be called when there is a new short message. Currently, the only action
        taken when there is a new message is to display it in the main window status bar.

        :param msg: (str) the short descriptive message to be handled
        '''
        self.statusBar().showMessage(msg)

    def hideAllPanels(self):
        '''hides all current panels'''
        for panel in self.__panels.values():
            panel.hide()

    def showAllPanels(self):
        '''shows all current panels'''
        for panel in self.__panels.values():
            panel.show()

    def onShowAssociationDialog(self):
        '''launches the instrument-panel association dialog (modal)'''
        dlg = AssociationDialog(self)
        Qt.qApp.SDM.connectWriter(
            "SelectedInstrument", dlg.ui.instrumentCB, "activated(QString)")
        dlg.exec_()
        Qt.qApp.SDM.disconnectWriter(
            "SelectedInstrument", dlg.ui.instrumentCB, "activated(QString)")

    def getInstrumentAssociation(self, instrumentname):
        '''
        Returns the panel name associated to an instrument name

        :param instrumentname: (str or None) The name of the instrument whose associated panel is wanted

        :return: (str or None) the associated panel name (or None).
        '''
        return self.__instrumentToPanelMap.get(instrumentname, None)

    def setInstrumentAssociation(self, instrumentname, panelname):
        '''
        Sets the panel name associated to an instrument

        :param instrumentname: (str) The name of the instrument
        :param panelname: (str or None) The name of the associated
                          panel or None to remove the association
                          for this instrument.
        '''
        instrumentname = str(instrumentname)
        # remove a previous association if it exists
        oldpanelname = self.__instrumentToPanelMap.get(instrumentname, None)
        self.__panelToInstrumentMap.pop(oldpanelname, None)

        # create the new association
        self.__instrumentToPanelMap[instrumentname] = panelname
        if panelname is not None:
            self.__panelToInstrumentMap[panelname] = instrumentname

    def getAllInstrumentAssociations(self):
        '''
        Returns the dictionary of instrument-panel associations

        :return: (dict<str,str>) a dict whose keys are the instruments known to the gui
                 and whose values are the corresponding associated panels (or None).
        '''
        return copy.deepcopy(self.__instrumentToPanelMap)

    def setAllInstrumentAssociations(self, associationsdict, clearExisting=False):
        '''
        Sets the dictionary of instrument-panel associations.
        By default, it keeps any existing association not present in the associationsdict.

        :param associationsdict: (dict<str,str>) a dict whose keys are the instruments names
                                 and whose values are the corresponding associated panels (or None)
        :param clearExisting: (bool) if True, the the existing asociations are cleared.
                              If False (default) existing associations are
                              updated with those in associationsdict
        '''
        if clearExisting:
            self.__instrumentToPanelMap = copy.deepcopy(associationsdict)
        else:
            self.__instrumentToPanelMap.update(copy.deepcopy(associationsdict))
        self.__panelToInstrumentMap = {}
        for k, v in self.__instrumentToPanelMap.items():
            self.__panelToInstrumentMap[v] = k

    def _onPanelVisibilityChanged(self, visible):
        if visible:
            panelname = str(self.sender().objectName())
            instrumentname = self.__panelToInstrumentMap.get(panelname)
            if instrumentname is not None:
                self.SelectedInstrument.emit(instrumentname)

    def onSelectedInstrument(self, instrumentname):
        ''' Slot to be called when the selected instrument has changed (e.g. by user
        clicking in the synoptic)

        :param instrumentname: (str) The name that identifies the instrument.
        '''
        instrumentname = str(instrumentname)
        panelname = self.getInstrumentAssociation(instrumentname)
        self.setFocusToPanel(panelname)

    def setFocusToPanel(self, panelname):
        ''' Method that sets a focus for panel passed via an argument

        :param panelname: (str) The name that identifies the panel.
                               This name must be unique within the panels in the GUI.
        '''
        panelname = str(panelname)
        try:
            panel = self.__panels[panelname]
            panel.show()
            panel.setFocus()
            panel.raise_()
        except KeyError:
            pass

    def tabifyArea(self, area):
        ''' tabifies all panels in a given area.

        :param area: (Qt.DockWidgetArea)

        .. warning:: This method is deprecated
        '''
        raise DeprecationWarning(
            'tabifyArea is no longer supported (now all panels reside in the same DockWidget Area)')
        panels = self.findPanelsInArea(area)
        if len(panels) < 2:
            return
        p0 = panels[0]
        for p in panels[1:]:
            self.tabifyDockWidget(p0, p)

    def findPanelsInArea(self, area):
        ''' returns all panels in the given area

        :param area: (QMdiArea, Qt.DockWidgetArea, 'FLOATING' or None). If
                     area=='FLOATING', the dockwidgets that are floating will be
                     returned.
        :param area:  (Qt.DockWidgetArea or str )

        .. warning:: This method is deprecated
        '''
        raise DeprecationWarning(
            'findPanelsInArea is no longer supported (now all panels reside in the same DockWidget Area)')
        if area == 'FLOATING':
            return [p for p in self.__panels.values() if p.isFloating()]
        else:
            return [p for p in self.__panels.values() if self.dockWidgetArea(p) == area]

    @classmethod
    def getQtDesignerPluginInfo(cls):
        '''TaurusGui is not to be in designer '''
        return None

    def onShowManual(self, anchor=None):
        '''reimplemented from :class:`TaurusMainWindow` to show the manual in a panel (not just a dockwidget)'''
        self.setFocusToPanel('Manual')

    def onExportCurrentPanelConfiguration(self, fname=None):

        if fname is None:
            fname = self._xmlConfigFileName

        if self._xmlConfigFileName is None:
            xmlroot = etree.Element("taurusgui_config")
        else:
            try:
                f = open(self._xmlConfigFileName, 'r')
                xmlroot = etree.fromstring(f.read())
                f.close()
            except Exception as e:
                self.error('Cannot parse file "%s": %s',
                           self._xmlConfigFileName, str(e))
                return

        # retrieve/create the PanelDescriptions node
        panelDescriptionsNode = xmlroot.find("PanelDescriptions")
        if panelDescriptionsNode is None:
            panelDescriptionsNode = etree.SubElement(
                xmlroot, "PanelDescriptions")

        # Get all custom panels
        from taurus.qt.qtgui.panel import QDoubleListDlg
        dlg = QDoubleListDlg(winTitle='Export Panels to XML',
                             mainLabel='Select which of the custom panels you want to export as xml configuration',
                             label1='Not Exported', label2='Exported',
                             list1=[n for n, p in self.__panels.items() if p.isCustom()], list2=[])
        result = dlg.exec_()
        if result != Qt.QDialog.Accepted:
            return
        exportlist = dlg.getAll2()

        # create xml for those to be exported
        registered = self.getConfigurableItemNames()
        for name in exportlist:
            panel = self.__panels[name]
            if name not in registered:
                panel.setPermanent(True)
                self.registerConfigDelegate(panel, name)
            panelxml = PanelDescription.fromPanel(panel).toXml()
            panelDescriptionsNode.append(etree.fromstring(panelxml))
        xml = etree.tostring(xmlroot, pretty_print=True, encoding='unicode')

        # write to file
        while True:
            if fname is None:
                fname, _ = compat.getSaveFileName(
                    self, "Open File", self._confDirectory,
                    self.tr("XML files (*.xml)")
                )
                if not fname:
                    return
            fname = str(fname)
            # backup the file
            if os.path.exists(fname):
                import shutil
                try:
                    bckname = "%s.orig" % fname
                    shutil.copy(fname, bckname)
                except:
                    self.warning(
                        "%s will be overwritten but I could not create a backup in %s", fname, bckname)
            # write the data
            try:
                f = open(fname, 'w')
                f.write(xml)
                f.close()
                break
            except Exception as e:
                msg = 'Cannot write to %s: %s' % (fname, str(e))
                self.error(msg)
                Qt.QMessageBox.warning(
                    self, "I/O problem", msg + '\nChoose a different location.', Qt.QMessageBox.Ok, Qt.QMessageBox.NoButton)
                fname = None

        hint = "XML_CONFIG = '%s'" % os.path.relpath(
            fname, self._confDirectory)
        msg = 'Configuration written in %s' % fname
        self.info(msg)
        Qt.QMessageBox.information(self, "Configuration updated",
                                   msg + '\nMake sure that the .py configuration file in %s contains\n%s' % (
                                       self._confDirectory, hint),
                                   Qt.QMessageBox.Ok, Qt.QMessageBox.NoButton)

        return

    def showSDMInfo(self):
        '''pops up a dialog showing the current information from the Shared Data Manager'''
        #w = Qt.QMessageBox( self)
        text = 'Currently managing %i shared data objects:\n%s' % (
            len(Qt.qApp.SDM.activeDataUIDs()), ', '.join(Qt.qApp.SDM.activeDataUIDs()))
        nfo = Qt.qApp.SDM.info()
        w = Qt.QMessageBox(Qt.QMessageBox.Information, 'Shared Data Manager Information', text,
                           buttons=Qt.QMessageBox.Close, parent=self)
        w.setDetailedText(nfo)
        w.show()
        self.info(nfo)


@click.command('gui')
@click.argument('confname', nargs=1, required=True)
@click.option('--safe-mode', 'safe_mode', is_flag=True, default=False,
              help=('launch in safe mode (it prevents potentially problematic '
                    + 'configs from being loaded)')
              )
@click.option('--ini', type=click.Path(exists=True),
              metavar="INIFILE",
              help=('settings file (.ini) to be loaded (defaults to '
                    + '<user_config_dir>/<appname>.ini)'),
              default=None
              )
def gui_cmd(confname, safe_mode, ini):
    """Launch a TaurusGUI using the given CONF"""
    import sys
    import taurus
    from taurus.qt.qtgui.application import TaurusApplication

    taurus.info('Starting execution of TaurusGui')

    app = TaurusApplication(cmd_line_parser=None, app_name="taurusgui")

    if safe_mode:
        configRecursionDepth = 0
    else:
        configRecursionDepth = None

    gui = TaurusGui(None, confname=confname, settingsname=ini,
                    configRecursionDepth=configRecursionDepth)

    gui.show()
    ret = app.exec_()

    taurus.info('Finished execution of TaurusGui')
    sys.exit(ret)


@click.command('newgui')
# @click.option('--stub', 'stub_name',
#               metavar="NAME",
#               default=None,
#               help='Create an empty stub of gui with the given NAME'
#               )
def newgui_cmd():
    """Create a new TaurusGui"""
    import sys
    from taurus.qt.qtgui.application import TaurusApplication

    app = TaurusApplication(cmd_line_parser=None, app_name="newgui")

    # if stub_name is not None:
    #     pass # TODO

    from taurus.qt.qtgui.taurusgui import AppSettingsWizard
    wizard = AppSettingsWizard()
    wizard.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    gui_cmd()
