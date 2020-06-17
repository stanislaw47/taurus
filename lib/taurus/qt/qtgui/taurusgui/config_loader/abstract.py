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
import abc

# Python 2/3 compatibility
if not hasattr(abc, "ABC"):
    setattr(abc, "ABC", abc.ABCMeta("ABC", (object,), {}))


__all__ = ["AbstractConfigLoader", "ConfigLoaderError"]


class ConfigLoaderError(Exception):
    """
    Base exception raised by ConfigLoader
    """

    def __init__(self, message):
        message = "Exception raised while loading configuration: " + message
        super(ConfigLoaderError, self).__init__(message)


class AbstractConfigLoader(abc.ABC):
    """
    Abstract class for config loaders.
    It defines interface which has to be implemneted by subclass in
    order for it to be ConfigLoader
    """

    CONFIG_VALUES = [
        "GUI_NAME",
        "ORGANIZATION",
        "CUSTOM_LOGO",
        "ORGANIZATION_LOGO",
        "SINGLE_INSTANCE",
        "MANUAL_URI",
        "INIFILE",
        "EXTRA_CATALOG_WIDGETS",
        "SYNOPTIC",
    ]

    def __init__(self, confname):
        self._confname = confname

    @abc.abstractmethod
    def supports(self, confname):
        """
        Return True or False for support of specific configuration passed
        """
        return None

    @abc.abstractmethod
    def load(self):
        """
        This method is meant to load actual data from file on disk.
        Return dictionary with configuration.
        """
        return {}

    @abc.abstractproperty
    def hooks(self):
        """
        List of hooks called at the end of 'TaurusGui.loadConfiguration'
        method. Each of them shall be called with 'TaurusGui' instance as
        first argument and dictionary with configuration as second.
        """
        return []
