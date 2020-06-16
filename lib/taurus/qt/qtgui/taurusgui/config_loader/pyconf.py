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
import pkgutil
import sys
import types
import inspect

from taurus.qt.qtgui.taurusgui.utils import (
    PanelDescription,
    AppletDescription,
    ToolBarDescription,
    ExternalApp,
)
from taurus.qt.qtgui.taurusgui.config_loader.abstract import (
    AbstractConfigLoader,
    ConfigLoaderError,
)


__all__ = ["PyConfigLoader"]


class PyConfigLoader(AbstractConfigLoader):
    """
    Loads configuration for TaurusGui from Python module or package
    """

    def __init__(self, confname):
        super(PyConfigLoader, self).__init__(confname)
        self._mod = types.ModuleType(
            "__dummy_conf_module_%s__" % confname
        )  # dummy module

    def _get_objects(self, klass):
        objs = [
            obj
            for name, obj in inspect.getmembers(self._mod)
            if isinstance(obj, klass)
        ]
        return objs

    def _importConfiguration(self):
        """returns the module corresponding to `confname` or to
        `tgconf_<confname>`. Note: the `conf` subdirectory of the directory in
        which taurusgui.py file is installed is temporally prepended to sys.path
        """
        confsubdir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "conf"
        )  # the path to a conf subdirectory of the place where taurusgui.py is
        oldpath = sys.path
        try:
            # add the conf subdirectory dir to the pythonpath
            sys.path = [confsubdir] + sys.path
            mod = __import__(self._confname)
        except ImportError:
            altconfname = "tgconf_%s" % self._confname
            try:
                mod = __import__(altconfname)
            except ImportError:
                msg = "cannot import %s or %s" % (self._confname, altconfname)
                raise ConfigLoaderError(msg)
        finally:
            sys.path = oldpath  # restore the previous sys.path
        return mod

    @staticmethod
    def supports(confname):
        if os.path.exists(confname):
            if os.path.isfile(confname):  # happy path, we got file
                ext = os.path.splitext(confname)[-1]
                if ext == ".py":
                    return True
                return False

            elif os.path.isdir(confname):
                # if it's directory, assume it's importable Python package
                return True
            return False
        else:
            # not exisitng path, check if it is in top-level modules
            if confname in list(pkgutil.iter_modules()):
                return True
            return False

    def load(self):
        """Reads a configuration file

        :param confname: (str or None) the  name of module located in the
                         PYTHONPATH or in the conf subdirectory of the directory
                         in which taurusgui.py file is installed.
                         This method will try to import <confname>.
                         If that fails, it will try to import
                         `tgconf_<confname>`.
                         Alternatively, `confname` can be the path to the
                         configuration module (not necessarily in the
                         PYTHONPATH).
                         `confname` can also be None, in which case a dummy
                         empty module will be used.
        """

        # import the python config file
        if os.path.exists(self._confname):  # if confname is a dir or file name
            import imp

            path, name = os.path.split(self._confname)
            name, _ = os.path.splitext(name)
            try:
                f, filename, data = imp.find_module(name, [path])
                self._mod = imp.load_module(name, f, filename, data)
            except ImportError:
                self._mod = self._importConfiguration()
        else:  # if confname is not a dir name, we assume it is a module name in the python path
            self._mod = self._importConfiguration()

    @property
    def conf_dir(self):
        return os.path.abspath(os.path.dirname(self._mod.__file__))

    @property
    def app_name(self):
        return getattr(self._mod, "GUI_NAME", None)

    @property
    def org_name(self):
        return getattr(self._mod, "ORGANIZATION", None)

    @property
    def custom_logo(self):
        return getattr(self._mod, "CUSTOM_LOGO", None)

    @property
    def org_logo(self):
        return getattr(self._mod, "ORGANIZATION_LOGO", None)

    @property
    def single_instance(self):
        return getattr(self._mod, "SINGLE_INSTANCE", None)

    @property
    def manual_uri(self):
        return getattr(self._mod, "MANUAL_URI", None)

    @property
    def ini_file(self):
        return getattr(self._mod, "INIFILE", None)

    @property
    def extra_catalog_widgets(self):
        return getattr(self._mod, "EXTRA_CATALOG_WIDGETS", [])

    @property
    def synoptics(self):
        return getattr(self._mod, "SYNOPTIC", [])

    @property
    def console(self):
        return getattr(self._mod, "CONSOLE", [])

    @property
    def monitor(self):
        return AppletDescription(
            "monitor",
            classname="TaurusMonitorTiny",
            model=getattr(self._mod, "MONITOR"),
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
        return getattr(self._mod, "MACROSERVER_NAME", None)

    @property
    def macro_panels(self):
        return getattr(self._mod, "MACRO_PANELS", None)

    @property
    def door_name(self):
        return getattr(self._mod, "DOOR_NAME", None)

    @property
    def macroeditors_path(self):
        return getattr(self._mod, "MACROEDITORS_PATH", None)

    @property
    def instruments_from_pool(self):
        return getattr(self._mod, "INSTRUMENTS_FROM_POOL", None)
