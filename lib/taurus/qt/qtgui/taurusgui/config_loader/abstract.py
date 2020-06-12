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
    setattr(abc, "ABC", abc.ABCMeta('ABC', (object,), {}))


__all__ = ["AbstractConfigLoader", "ConfigLoaderError"]


class ConfigLoaderError(Exception):
    def __init__(self, message):
        message = "Exception raised while loading configuration: " + message
        super(ConfigLoaderError, self).__init__(message)


class AbstractConfigLoader(abc.ABC):
    """
    Abstract class for config loaders
    """

    def __init__(self, confname):
        self._confname = confname

    @abc.abstractmethod
    def load(self):
        """
        This method is meant to load actual data from file on disk
        """

    @abc.abstractproperty
    def app_name(self):
        """Name of the application"""
        return None

    @abc.abstractproperty
    def org_name(self):
        """Name of organization"""
        return None

    @abc.abstractproperty
    def custom_logo(self):
        """Path to application's custom logo file"""
        return None

    @abc.abstractproperty
    def org_logo(self):
        """Path to organization's custom logo file"""
        return None

    @abc.abstractproperty
    def single_instance(self):
        """Whether more than one instance of application can be launched simultaously or not"""
        return None

    @abc.abstractproperty
    def manual_uri(self):
        """URI pointing to application's manual"""
        return None

    @abc.abstractproperty
    def ini_file(self):
        """Path to application's default INI file with settings"""
        return None

    @abc.abstractproperty
    def extra_catalog_widgets(self):
        """Path to application's custom logo file"""
        return []

    @abc.abstractproperty
    def synoptics(self):
        """Sequence of paths to synoptic files"""
        return []

    @abc.abstractproperty
    def console(self):
        """Whether to add console widget or not"""
        return None

    @abc.abstractproperty
    def panels(self):
        """List of custom panels with widgets"""
        return []

    @abc.abstractproperty
    def toolbars(self):
        """List of custom toolbars"""
        return []

    @abc.abstractproperty
    def applets(self):
        """List of custom applets"""
        return []

    @abc.abstractproperty
    def external_apps(self):
        """List of external applications"""
        return []